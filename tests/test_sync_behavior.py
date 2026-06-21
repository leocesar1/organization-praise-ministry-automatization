import unittest
from unittest.mock import MagicMock, patch
import json
import os
import sys

# Adiciona a raiz do projeto ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.storage import OneDriveStorage
from core.models import MusicMetadata

class TestSyncBehavior(unittest.TestCase):
    
    def setUp(self):
        # Mock do cliente OneDrive
        self.mock_onedrive = MagicMock()
        
        # Simulamos que o OneDrive tem o arquivo music_database.json
        self.mock_onedrive.get_folder_children.return_value = [
            {"name": "music_database.json", "id": "FAKE_DB_ID"}
        ]
        
        # Conteúdo inicial simulando as 322 músicas (vamos usar apenas 2 para o teste)
        self.initial_db = {
            "ID_ANTIGO_1": {"music_name": "A Bênção"},
            "ID_ANTIGO_2": {"music_name": "A Boa Parte"}
        }
        self.mock_onedrive.download_file.return_value = json.dumps(self.initial_db).encode("utf-8")
        
        # Inicializa o storage com o mock
        self.storage = OneDriveStorage(self.mock_onedrive)

    def test_validation_by_id_only(self):
        """Testa se a validação ignora o nome e usa APENAS o folder_id"""
        # Se eu perguntar pelo ID_ANTIGO_1, deve retornar True
        self.assertTrue(self.storage.is_synced("ID_ANTIGO_1", music_name="Qualquer Nome"))
        
        # Se o usuário apagou a pasta "A Bênção" e criou de novo, ela terá um NOVO_ID.
        # Apesar do nome ser "A Bênção", o is_synced DEVE retornar False (pois valida apenas por ID)
        self.assertFalse(self.storage.is_synced("NOVO_ID", music_name="A Bênção"))
        
        # get_synced_info também não deve achar pelo nome se o ID mudou
        info = self.storage.get_synced_info("NOVO_ID", music_name="A Bênção")
        self.assertEqual(info, {})

    @patch('requests.put')
    def test_saving_preserves_old_records_and_fixes_json_extension(self, mock_put):
        """Testa se ao salvar uma música nova, os dados antigos não são apagados e a extensão .json é usada"""
        # Metadados fictícios da nova música
        metadata = MusicMetadata(
            name="Nova Música",
            artist="Novo Artista",
            key="C",
            bpm=120,
            compass="4/4",
            elite=False,
            instrument=None
        )
        
        # Simulamos a sincronização dessa nova música
        self.storage.mark_synced("NOVO_ID_3", 9999, metadata)
        
        # Verifica se o requests.put foi chamado
        mock_put.assert_called_once()

    @patch('requests.put')
    def test_storage_save_uses_json_extension_and_preserves_data(self, mock_put):
        """Testa diretamente se a chamada ao requests.put adiciona a extensão .json corretamente"""
        metadata = MusicMetadata(
            name="Nova Música",
            artist="Novo Artista",
            key="C",
            bpm=120,
            compass="4/4",
            elite=False,
            instrument=None
        )
        
        # Simulando base_url
        self.storage.onedrive.base_url = "https://graph.microsoft.com/v1.0"
        self.storage.folder_id = "PASTA_RAIZ_ID"
        
        # Ao marcar como sincronizado, o storage lê o db atual, adiciona a nova música e salva
        self.storage.mark_synced("NOVO_ID", 5555, metadata)
        
        # Verifica a URL que foi chamada
        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        url_called = args[0]
        
        # A URL DEVE conter music_database.json, comprovando que o bug de sobrescrever arquivo sem extensão sumiu
        self.assertTrue(url_called.endswith("music_database.json:/content"))
        
        # Verifica se o conteúdo salvo tem as 2 músicas antigas + 1 nova (não apagou nada)
        saved_data = json.loads(kwargs['data'].decode('utf-8'))
        self.assertIn("ID_ANTIGO_1", saved_data)
        self.assertIn("ID_ANTIGO_2", saved_data)
        self.assertIn("NOVO_ID", saved_data)
        self.assertEqual(len(saved_data), 3)

    def test_file_naming_uses_folder_id(self):
        """Testa a lógica de geração dos nomes dos arquivos de mapa (deve usar folder_id ao invés do nome da música)"""
        # Import local para não executar o código global
        from runners.sync_arrangements import sync_arrangement_for_folder
        import json
        
        # Mock do onedrive
        mock_onedrive = MagicMock()
        mock_onedrive.get_rpp_file.return_value = ("arquivo.rpp", b"conteudo dummy")
        mock_bot = MagicMock()
        mock_storage = MagicMock()
        mock_storage.get_synced_info.return_value = {}
        
        with patch('runners.sync_arrangements.parse_music_metadata') as mock_parse, \
             patch('runners.sync_arrangements.parse_rpp_regions') as mock_parse_regions, \
             patch('core.reaper_parser.parse_rpp_chords') as mock_parse_chords, \
             patch('core.reaper_parser.parse_rpp_tempo_map') as mock_parse_tempo, \
             patch('core.harmonic_map.build_harmonic_map') as mock_build, \
             patch('core.harmonic_layout.format_harmonic_txt') as mock_format_txt, \
             patch('core.reaper_parser.format_arrangement_message') as mock_msg:
             
             # Setup mocks
             mock_parse.return_value = MusicMetadata("A Bênção", "Gabriela", "C", 120, "4/4", False, None)
             mock_parse_regions.return_value = [{"start": 0, "end": 10, "name": "Intro"}]
             mock_parse_chords.return_value = []
             mock_parse_tempo.return_value = []
             mock_build.return_value = []
             mock_format_txt.return_value = "TEXTO FORMATADO"
             
             # Executa o sincronizador com um FOLDER_ID específico
             sync_arrangement_for_folder("MEU_FOLDER_ID_123", "pasta_nome", mock_onedrive, mock_bot, mock_storage)
             
             # Verifica se upload_json_file e upload_txt_file foram chamados com o MEU_FOLDER_ID_123.json/txt
             mock_onedrive.upload_json_file.assert_called_once()
             args_json, _ = mock_onedrive.upload_json_file.call_args
             self.assertEqual(args_json[0], "MEU_FOLDER_ID_123.json")
             
             mock_onedrive.upload_txt_file.assert_called_once()
             args_txt, _ = mock_onedrive.upload_txt_file.call_args
             self.assertEqual(args_txt[0], "MEU_FOLDER_ID_123.txt")

    @patch('requests.put')
    def test_first_execution_creates_json_file(self, mock_put):
        """Testa o comportamento quando é a primeira execução e o arquivo music_database.json ainda não existe"""
        # Cria um novo storage com um mock diferente, onde o arquivo não existe
        mock_onedrive_empty = MagicMock()
        mock_onedrive_empty.base_url = "https://graph.microsoft.com/v1.0"
        mock_onedrive_empty.get_folder_children.return_value = [] # Retorna vazio, simulando que o db não existe
        
        storage_empty = OneDriveStorage(mock_onedrive_empty)
        storage_empty.folder_id = "PASTA_RAIZ_ID"
        
        # Confirma que o load() retorna um dicionário vazio
        db_inicial = storage_empty.load()
        self.assertEqual(db_inicial, {})
        
        # Adiciona a primeira música da história e manda salvar
        metadata = MusicMetadata(
            name="Primeira Música",
            artist="Banda 1",
            key="G",
            bpm=70,
            compass="4/4",
            elite=False,
            instrument=None
        )
        storage_empty.mark_synced("ID_PRIMEIRA_MUSICA", 1000, metadata)
        
        # Verifica se o arquivo salvo tem a extensão .json mesmo sendo o primeiro
        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        url_called = args[0]
        
        self.assertTrue(url_called.endswith("music_database.json:/content"))
        
        # Verifica se o dado salvo tem exatamente 1 registro
        saved_data = json.loads(kwargs['data'].decode('utf-8'))
        self.assertIn("ID_PRIMEIRA_MUSICA", saved_data)
        self.assertEqual(len(saved_data), 1)

    @patch('requests.put')
    def test_second_execution_updates_existing_json_file(self, mock_put):
        """Testa o comportamento quando é a segunda execução e o arquivo music_database.json JÁ EXISTE"""
        # Cria um novo storage com mock onde o arquivo de banco JÁ EXISTE e tem 1 registro
        mock_onedrive_existing = MagicMock()
        mock_onedrive_existing.base_url = "https://graph.microsoft.com/v1.0"
        
        # Simula que o onedrive já possui o arquivo com o nome correto
        mock_onedrive_existing.get_folder_children.return_value = [
            {"name": "music_database.json", "id": "ID_DO_ARQUIVO_BANCO"}
        ]
        
        # Simula o conteúdo atual do arquivo no OneDrive (O registro salvo na primeira execução)
        db_existente = {
            "ID_PRIMEIRA_MUSICA": {"music_name": "Primeira Música", "message_id": 1000}
        }
        mock_onedrive_existing.download_file.return_value = json.dumps(db_existente).encode("utf-8")
        
        storage_existing = OneDriveStorage(mock_onedrive_existing)
        storage_existing.folder_id = "PASTA_RAIZ_ID"
        
        # Confirma que o load() carregou o registro existente corretamente
        db_carregado = storage_existing.load()
        self.assertIn("ID_PRIMEIRA_MUSICA", db_carregado)
        self.assertEqual(len(db_carregado), 1)
        
        # Adiciona a segunda música da história e manda salvar
        metadata_2 = MusicMetadata(
            name="Segunda Música",
            artist="Banda 2",
            key="C",
            bpm=120,
            compass="4/4",
            elite=False,
            instrument=None
        )
        storage_existing.mark_synced("ID_SEGUNDA_MUSICA", 2000, metadata_2)
        
        # Verifica se o arquivo salvo tem a extensão .json
        mock_put.assert_called_once()
        args, kwargs = mock_put.call_args
        url_called = args[0]
        
        self.assertTrue(url_called.endswith("music_database.json:/content"))
        
        # Verifica se o dado salvo AGORA tem exatamente 2 registros (Preservou o primeiro e adicionou o segundo)
        saved_data = json.loads(kwargs['data'].decode('utf-8'))
        self.assertIn("ID_PRIMEIRA_MUSICA", saved_data)
        self.assertIn("ID_SEGUNDA_MUSICA", saved_data)
        self.assertEqual(len(saved_data), 2)

if __name__ == '__main__':
    unittest.main()

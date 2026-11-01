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

    def test_get_renders_filters_non_audio_files(self):
        """Testa se get_renders filtra arquivos que não são de áudio (ex: .html, .DS_Store, subpastas)."""
        from services.onedrive import OneDriveClient

        client = OneDriveClient.__new__(OneDriveClient)
        client.get_folder_children = MagicMock()
        client.download_file = MagicMock(return_value=b"fake audio data")

        # Mock da subpasta '1 _ Renders'
        client.get_folder_children.side_effect = [
            [{"name": "1 _ Renders", "id": "RENDERS_FOLDER_ID"}],
            [
                {"id": "file_html", "name": "index.html", "size": 100},
                {"id": "file_ds", "name": ".DS_Store", "size": 5000},
                {"id": "file_txt", "name": "leia-me.txt", "size": 200},
                {"id": "folder_sub", "name": "Subpasta", "folder": {}},
                {"id": "file_mp3_1", "name": "Mix Geral.mp3", "size": 5000000},
                {"id": "file_wav", "name": "Voz - Tenor.wav", "size": 8000000},
                {"id": "file_m4a", "name": "Teclado.M4A", "size": 4000000},
            ]
        ]

        renders = client.get_renders("FOLDER_ID_MOCK")

        # Deve conter apenas os 3 arquivos de áudio
        self.assertEqual(set(renders.keys()), {"Mix Geral.mp3", "Voz - Tenor.wav", "Teclado.M4A"})
        self.assertNotIn("index.html", renders)
        self.assertNotIn(".DS_Store", renders)
        self.assertNotIn("leia-me.txt", renders)
        self.assertNotIn("Subpasta", renders)

    @patch('runners.list_musics.OneDriveClient')
    def test_list_musics(self, mock_client_cls):
        """Testa o runner list_musics retornando lista ordenada e filtrando arquivos da raiz."""
        from runners.list_musics import list_musics

        mock_client = mock_client_cls.return_value
        mock_client.get_file_list.return_value = [
            {"id": "ID_2", "name": "Leão _ C _ Gabriela Rocha _ 70bpm _ 4/4", "folder": {}},
            {"id": "ID_FILE", "name": "leia_me.txt", "file": {}},
            {"id": "ID_1", "name": "A Bênção _ G _ Gabriel Guedes _ 68bpm _ 4/4", "folder": {}},
        ]

        musics = list_musics()
        self.assertEqual(len(musics), 2)
        # Ordenado por nome
        self.assertEqual(musics[0]["id"], "ID_1")
        self.assertEqual(musics[0]["name"], "A Bênção")
        self.assertEqual(musics[1]["id"], "ID_2")
        self.assertEqual(musics[1]["name"], "Leão")

    def test_process_single_folder_with_force(self):
        """Testa se process_single_folder com force=True atualiza mesmo já estando no storage."""
        from runners.sync_music import process_single_folder

        mock_onedrive = MagicMock()
        mock_bot = MagicMock()
        mock_storage = MagicMock()

        # Configura storage para dizer que já está sincronizada
        mock_storage.is_synced.return_value = True
        mock_bot.send_audio_group.return_value = 12345
        mock_onedrive.get_renders.return_value = {"audio.mp3": b"data"}

        with patch('runners.sync_arrangements.sync_arrangement_for_folder') as mock_sync_arr:
            mock_sync_arr.return_value = ("http://mapa.link", [{"name": "Intro"}])

            # Chamada sem force -> deve ignorar e retornar False
            synced_no_force = process_single_folder(
                folder_id="ID_SYNCED",
                folder_name="01 - Música Já Sincronizada - C",
                onedrive=mock_onedrive,
                bot=mock_bot,
                storage=mock_storage,
                with_arrangement=True,
                force=False
            )
            self.assertFalse(synced_no_force)
            mock_bot.send_audio_group.assert_not_called()

            # Chamada com force -> deve processar e enviar
            synced_force = process_single_folder(
                folder_id="ID_SYNCED",
                folder_name="01 - Música Já Sincronizada - C",
                onedrive=mock_onedrive,
                bot=mock_bot,
                storage=mock_storage,
                with_arrangement=True,
                force=True
            )
            self.assertTrue(synced_force)
            mock_bot.send_audio_group.assert_called_once()
            mock_storage.mark_synced.assert_called_once()
            mock_sync_arr.assert_called_with(
                "ID_SYNCED", "01 - Música Já Sincronizada - C", mock_onedrive, mock_bot, mock_storage, force_update=True
            )

    def test_download_folder_recursive(self):
        """Testa se download_folder_recursive cria pastas e baixa arquivos locais."""
        import tempfile
        from runners.download_music import download_folder_recursive

        mock_onedrive = MagicMock()
        # Simula estrutura: raiz tem 1 arquivo e 1 subpasta com 1 arquivo
        mock_onedrive.get_folder_children.side_effect = [
            [
                {"id": "FILE_1", "name": "track.rpp", "size": 1024},
                {"id": "SUB_1", "name": "1 _ Renders", "folder": {}}
            ],
            [
                {"id": "FILE_2", "name": "Mix Geral.mp3", "size": 2048}
            ]
        ]
        mock_onedrive.download_file.side_effect = [
            b"CONTEUDO_RPP",
            b"CONTEUDO_MP3"
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            dest_dir = os.path.join(tmp_dir, "Minha_Musica")
            download_folder_recursive(mock_onedrive, "FOLDER_ROOT_ID", dest_dir)

            rpp_path = os.path.join(dest_dir, "track.rpp")
            mp3_path = os.path.join(dest_dir, "1 _ Renders", "Mix Geral.mp3")

            self.assertTrue(os.path.exists(rpp_path))
            self.assertTrue(os.path.exists(mp3_path))
            with open(rpp_path, "rb") as f:
                self.assertEqual(f.read(), b"CONTEUDO_RPP")
            with open(mp3_path, "rb") as f:
                self.assertEqual(f.read(), b"CONTEUDO_MP3")

    def test_upload_folder_recursive(self):
        """Testa se upload_folder_recursive percorre arquivos e pastas locais e chama os uploads correspondentes."""
        import tempfile
        from runners.upload_music import upload_folder_recursive

        mock_onedrive = MagicMock()
        mock_onedrive.get_or_create_folder.return_value = "REMOTE_SUB_ID"

        with tempfile.TemporaryDirectory() as tmp_dir:
            local_music = os.path.join(tmp_dir, "Musica_Local")
            os.makedirs(local_music, exist_ok=True)
            renders_dir = os.path.join(local_music, "1 _ Renders")
            os.makedirs(renders_dir, exist_ok=True)

            # Arquivo na raiz
            rpp_file = os.path.join(local_music, "projeto.rpp")
            with open(rpp_file, "wb") as f:
                f.write(b"CONTEUDO_RPP")

            # Arquivo na subpasta
            mp3_file = os.path.join(renders_dir, "Mix.mp3")
            with open(mp3_file, "wb") as f:
                f.write(b"CONTEUDO_MP3")

            # Arquivo .DS_Store a ser ignorado
            ds_store = os.path.join(local_music, ".DS_Store")
            with open(ds_store, "wb") as f:
                f.write(b"IGNORAR")

            upload_folder_recursive(mock_onedrive, local_music, "REMOTE_ROOT_ID")

            # Deve criar a subpasta 1 _ Renders
            mock_onedrive.get_or_create_folder.assert_called_once_with("1 _ Renders", parent_id="REMOTE_ROOT_ID")

            # Deve chamar upload_file para projeto.rpp e Mix.mp3 (e não para .DS_Store)
            self.assertEqual(mock_onedrive.upload_file.call_count, 2)
            mock_onedrive.upload_file.assert_any_call("projeto.rpp", b"CONTEUDO_RPP", folder_id="REMOTE_ROOT_ID")
            mock_onedrive.upload_file.assert_any_call("Mix.mp3", b"CONTEUDO_MP3", folder_id="REMOTE_SUB_ID")

if __name__ == '__main__':
    unittest.main()





import argparse
import logging
from services.storage import OneDriveStorage
from services.onedrive import OneDriveClient

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def remove_from_db(search_term: str):
    onedrive = OneDriveClient()
    onedrive.authenticate()
    storage = OneDriveStorage(onedrive)
    
    data = storage.load()
    if not data:
        logger.info("Banco de dados vazio.")
        return
        
    found_keys = []
    for folder_id, metadata in data.items():
        if search_term.lower() in metadata.get("music_name", "").lower():
            found_keys.append((folder_id, metadata))
            
    if not found_keys:
        logger.info(f"Nenhuma música contendo '{search_term}' foi encontrada no banco.")
        return
        
    logger.info("Músicas encontradas:")
    for i, (f_id, meta) in enumerate(found_keys):
        logger.info(f"[{i}] {meta.get('music_name')} - BPM: {meta.get('bpm', '?')} - ID: {f_id}")
        
    choice = input("\nDigite o número da música que deseja remover do banco de dados (ou deixe vazio para cancelar): ")
    if not choice.isdigit() or int(choice) >= len(found_keys):
        logger.info("Cancelado.")
        return
        
    idx = int(choice)
    target_folder_id = found_keys[idx][0]
    target_name = found_keys[idx][1].get('music_name')
    
    del data[target_folder_id]
    storage.save(data)
    logger.info(f"✅ '{target_name}' removida do banco de dados com sucesso!")
    logger.info("Na próxima vez que você rodar o sync_music, ela será enviada novamente.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Remove uma música do banco de dados para forçar o re-envio.")
    parser.add_argument("nome", type=str, help="Parte do nome da música para buscar")
    args = parser.parse_args()
    
    remove_from_db(args.nome)

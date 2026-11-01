import json
import sys
import logging
from services.onedrive import OneDriveClient
from core.name_parser import parse_music_metadata

# Configura logs para stderr para que stdout receba exclusivamente o JSON
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", stream=sys.stderr)
logger = logging.getLogger(__name__)

def list_musics():
    """Recupera as pastas do OneDrive e retorna uma lista de dicionários com id, name e folder_name."""
    onedrive = OneDriveClient()
    onedrive.authenticate()

    logger.info("Recuperando pastas de músicas do OneDrive...")
    items = onedrive.get_file_list()
    
    musics = []
    for item in items:
        # Se for arquivo na raiz, ignora
        if "file" in item:
            continue
            
        folder_id = item.get("id")
        folder_name = item.get("name")
        if not folder_id or not folder_name:
            continue
            
        try:
            metadata = parse_music_metadata(folder_name)
            display_name = metadata.name
        except Exception:
            display_name = folder_name
            
        musics.append({
            "id": folder_id,
            "name": display_name,
            "folder_name": folder_name
        })

    # Ordena alfabeticamente pelo nome da música
    musics.sort(key=lambda m: m["name"].lower())
    return musics

def main():
    try:
        musics = list_musics()
        json.dump(musics, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        sys.stdout.flush()
    except Exception as e:
        logger.error(f"Erro ao listar músicas: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

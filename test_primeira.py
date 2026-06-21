from services.onedrive import OneDriveClient
from services.storage import OneDriveStorage
from services.telegram import TelegramBot
from runners.sync_music import main as sync_music_main
from runners.sync_arrangements import sync_arrangement_for_folder
import logging

logging.basicConfig(level=logging.INFO)

def test_primeira_essencia():
    onedrive = OneDriveClient()
    onedrive.authenticate()
    
    bot = TelegramBot()
    storage = OneDriveStorage(onedrive)
    
    music_list = onedrive.get_file_list()
    
    for item in music_list:
        # if "primeira essencia" in item.get("name", "").lower():
        if "a benção" in item.get("name", "").lower():
            folder_id = item["id"]
            folder_name = item["name"]
            print(f"Testando: {folder_name}")
            
            # Chama a sincronização de arranjo
            sync_arrangement_for_folder(
                folder_id, folder_name, onedrive, bot, storage, force_update=True
            )
            break

if __name__ == '__main__':
    test_primeira_essencia()

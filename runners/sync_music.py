import argparse
import logging
from tqdm import tqdm
from services.onedrive import OneDriveClient
from services.telegram import TelegramBot
from services.storage import OneDriveStorage
from core.name_parser import parse_music_metadata

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main(test_mode: bool = False, limit: int = None, no_arrangement: bool = False, folder: str = None):
    with_arrangement = not no_arrangement
    onedrive = OneDriveClient()
    onedrive.authenticate()
    
    bot = TelegramBot()
    storage = OneDriveStorage(onedrive)
    
    logger.info("Recuperando lista de arquivos do OneDrive...")
    music_list = onedrive.get_file_list()
    processed = 0
    
    for item in tqdm(music_list, desc="Processando músicas"):
        if "file" in item:
            continue
            
        folder_id = item["id"]
        folder_name = item["name"]
        
        if folder and folder.lower() not in folder_name.lower():
            continue
            
        try:
            metadata = parse_music_metadata(folder_name)
        except Exception as e:
            logger.error(f"Erro ao analisar nome da pasta {folder_name}: {e}")
            continue

        if storage.is_synced(folder_id, music_name=metadata.name):
            logger.debug(f"Pula {folder_name} - já sincronizada")
            # Se for solicitado o arranjo, podemos tentar sincronizar/atualizar mesmo se a música já estiver sincronizada
            if with_arrangement:
                try:
                    from runners.sync_arrangements import sync_arrangement_for_folder
                    sync_arrangement_for_folder(folder_id, folder_name, onedrive, bot, storage, force_update=False)
                except Exception as e:
                    logger.error(f"Erro ao sincronizar arranjo complementar para {folder_name}: {e}")
            continue
            
        try:
            logger.info(f"Processando nova música: {folder_name}")
            metadata = parse_music_metadata(folder_name)
            
            # 1. Sincroniza o arranjo primeiro para obter o link do mapa (se houver e não for pulado)
            map_url = None
            regions = []
            if with_arrangement:
                try:
                    from runners.sync_arrangements import sync_arrangement_for_folder
                    # Passa force_update=False por padrão para evitar re-downloads desnecessários
                    map_url, regions = sync_arrangement_for_folder(folder_id, folder_name, onedrive, bot, storage, force_update=False)
                except Exception as e:
                    logger.error(f"Erro ao sincronizar arranjo para {metadata.name}: {e}")

            # 2. Obtém os renders e envia o grupo de áudio contendo o link e a estrutura na legenda
            render_files = onedrive.get_renders(folder_id)
            message_id = bot.send_audio_group(metadata, render_files, map_url=map_url, regions=regions)
            
            if message_id:
                storage.mark_synced(folder_id, message_id, metadata=metadata)
                processed += 1
                logger.info(f"✅ [{processed}] {metadata.name} enviada com sucesso (msg_id={message_id})")
            else:
                logger.error(f"❌ Falha ao enviar para o Telegram: {folder_name}")
                
        except Exception as e:
            logger.error(f"Erro ao processar música {folder_name}: {e}")
            try:
                storage.mark_error(folder_id, str(e), metadata=metadata if 'metadata' in locals() else None)
            except Exception as inner_e:
                logger.error(f"Não foi possível salvar o erro no database: {inner_e}")
            
        if test_mode and processed >= 1:
            logger.info("Modo teste: 1 música processada. Encerrando.")
            break
        if limit and processed >= limit:
            logger.info(f"Limite de {limit} músicas atingido.")
            break
            
    logger.info(f"Concluído! {processed} novas músicas sincronizadas.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sincroniza músicas do OneDrive para o Telegram.")
    parser.add_argument("--test", action="store_true", help="Processa apenas 1 música (modo teste)")
    parser.add_argument("--limit", type=int, default=None, help="Processa no máximo N músicas")
    parser.add_argument("--no-arrangement", action="store_true", help="Não sincroniza o mapa de arranjo (.rpp)")
    parser.add_argument("--folder", type=str, default=None, help="Filtra e processa apenas uma pasta específica (pelo nome)")
    args = parser.parse_args()
    
    main(test_mode=args.test, limit=args.limit, no_arrangement=args.no_arrangement, folder=args.folder)

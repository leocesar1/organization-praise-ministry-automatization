import argparse
import logging
from tqdm import tqdm
from services.onedrive import OneDriveClient
from services.telegram import TelegramBot
from services.storage import TelegramStorage
from core.name_parser import parse_music_metadata

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main(test_mode: bool = False, limit: int = None):
    onedrive = OneDriveClient()
    onedrive.authenticate()
    
    bot = TelegramBot()
    storage = TelegramStorage(bot)
    
    logger.info("Recuperando lista de arquivos do OneDrive...")
    music_list = onedrive.get_file_list()
    processed = 0
    
    for item in tqdm(music_list, desc="Processando músicas"):
        if "file" in item:
            continue
            
        folder_id = item["id"]
        folder_name = item["name"]
        
        if storage.is_synced(folder_id):
            logger.debug(f"Pula {folder_name} - já sincronizada")
            continue
            
        try:
            logger.info(f"Processando nova música: {folder_name}")
            metadata = parse_music_metadata(folder_name)
            render_files = onedrive.get_renders(folder_id)
            
            message_id = bot.send_audio_group(metadata, render_files)
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
    args = parser.parse_args()
    
    main(test_mode=args.test, limit=args.limit)

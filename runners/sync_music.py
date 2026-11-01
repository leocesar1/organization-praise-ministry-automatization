import argparse
import logging
from tqdm import tqdm
from services.onedrive import OneDriveClient
from services.telegram import TelegramBot
from services.storage import OneDriveStorage
from core.name_parser import parse_music_metadata

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def process_single_folder(
    folder_id: str,
    folder_name: str,
    onedrive: OneDriveClient,
    bot: TelegramBot,
    storage: OneDriveStorage,
    with_arrangement: bool = True,
    force: bool = False
) -> bool:
    """Processa uma única pasta/música. Retorna True se enviada com sucesso, False caso contrário."""
    try:
        metadata = parse_music_metadata(folder_name)
    except Exception as e:
        logger.error(f"Erro ao analisar nome da pasta {folder_name}: {e}")
        return False

    is_already_synced = storage.is_synced(folder_id, music_name=metadata.name)
    if is_already_synced and not force:
        logger.debug(f"Pula {folder_name} - já sincronizada")
        if with_arrangement:
            try:
                from runners.sync_arrangements import sync_arrangement_for_folder
                sync_arrangement_for_folder(folder_id, folder_name, onedrive, bot, storage, force_update=False)
            except Exception as e:
                logger.error(f"Erro ao sincronizar arranjo complementar para {folder_name}: {e}")
        return False

    try:
        action_label = "Atualizando (forçado)" if (is_already_synced and force) else "Processando nova música"
        logger.info(f"{action_label}: {folder_name}")
        
        map_url = None
        regions = []
        if with_arrangement:
            try:
                from runners.sync_arrangements import sync_arrangement_for_folder
                map_url, regions = sync_arrangement_for_folder(
                    folder_id, folder_name, onedrive, bot, storage, force_update=force
                )
            except Exception as e:
                logger.error(f"Erro ao sincronizar arranjo para {metadata.name}: {e}")

        render_files = onedrive.get_renders(folder_id)
        message_id = bot.send_audio_group(metadata, render_files, map_url=map_url, regions=regions)
        
        if message_id:
            storage.mark_synced(folder_id, message_id, metadata=metadata)
            logger.info(f"✅ {metadata.name} enviada com sucesso (msg_id={message_id})")
            return True
        else:
            logger.error(f"❌ Falha ao enviar para o Telegram: {folder_name}")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao processar música {folder_name}: {e}")
        try:
            storage.mark_error(folder_id, str(e), metadata=metadata if 'metadata' in locals() else None)
        except Exception as inner_e:
            logger.error(f"Não foi possível salvar o erro no database: {inner_e}")
        return False

def main(test_mode: bool = False, limit: int = None, no_arrangement: bool = False, folder: str = None, folder_id: str = None, force: bool = False):
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
            
        item_id = item["id"]
        item_name = item["name"]
        
        if folder_id and item_id != folder_id:
            continue
            
        if folder and folder.lower() not in item_name.lower():
            continue
            
        success = process_single_folder(
            folder_id=item_id,
            folder_name=item_name,
            onedrive=onedrive,
            bot=bot,
            storage=storage,
            with_arrangement=with_arrangement,
            force=force
        )
        if success:
            processed += 1
            
        if folder_id:
            break

        if test_mode and processed >= 1:
            logger.info("Modo teste: 1 música processada. Encerrando.")
            break
        if limit and processed >= limit:
            logger.info(f"Limite de {limit} músicas atingido.")
            break
            
    logger.info(f"Concluído! {processed} música(s) processada(s)/atualizada(s).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sincroniza músicas do OneDrive para o Telegram.")
    parser.add_argument("--test", action="store_true", help="Processa apenas 1 música (modo teste)")
    parser.add_argument("--limit", type=int, default=None, help="Processa no máximo N músicas")
    parser.add_argument("--no-arrangement", action="store_true", help="Não sincroniza o mapa de arranjo (.rpp)")
    parser.add_argument("--folder", type=str, default=None, help="Filtra e processa apenas uma pasta específica (pelo nome)")
    parser.add_argument("--folder-id", type=str, default=None, help="Processa uma pasta específica pelo ID exato")
    parser.add_argument("--force", action="store_true", help="Força a atualização mesmo se já sincronizada")
    args = parser.parse_args()
    
    main(
        test_mode=args.test,
        limit=args.limit,
        no_arrangement=args.no_arrangement,
        folder=args.folder,
        folder_id=args.folder_id,
        force=args.force
    )

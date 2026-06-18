import argparse
import logging
from tqdm import tqdm
from services.onedrive import OneDriveClient
from services.telegram import TelegramBot
from services.storage import TelegramStorage
from core.name_parser import parse_music_metadata
from core.reaper_parser import parse_rpp_regions, format_arrangement_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def sync_arrangement_for_folder(folder_id: str, folder_name: str, onedrive: OneDriveClient, bot: TelegramBot, storage: TelegramStorage, force_update: bool = False, validate_chords: bool = False):
    metadata = parse_music_metadata(folder_name)
    data = storage.load()
    existing_entry = data.get(folder_id, {})
    existing_msg_id = existing_entry.get("arrangement_message_id")
    
    if existing_msg_id and not force_update and not validate_chords:
        logger.debug(f"Pula {metadata.name} - arranjo já sincronizado")
        return existing_msg_id

    try:
        # Busca e baixa o arquivo .rpp no OneDrive
        rpp_name, rpp_content = onedrive.get_rpp_file(folder_id)
        if not rpp_content:
            logger.warning(f"⚠️ Arquivo .rpp não encontrado para {metadata.name}")
            return None
            
        logger.info(f"Processando arranjo para {metadata.name} a partir de {rpp_name}...")
        
        # Parseia as regiões
        rpp_text = rpp_content.decode("utf-8", errors="ignore")
        regions = parse_rpp_regions(rpp_text)
        
        # Tenta obter o tom a partir dos metadados MIDI do RPP
        try:
            from core.reaper_parser import parse_rpp_keysig
            keysig = parse_rpp_keysig(rpp_text)
            if keysig:
                logger.info(f"Tom extraído dos metadados MIDI do RPP: '{keysig}' (anterior era '{metadata.key}')")
                metadata.key = keysig
        except Exception as e:
            logger.warning(f"Não foi possível obter tom do RPP: {e}")
            
        if not regions:
            logger.warning(f"⚠️ Nenhuma região encontrada no arquivo .rpp para {metadata.name}")
            return None
            
        # Parseia as cifras (se existirem)
        chords = None
        try:
            from core.reaper_parser import parse_rpp_chords
            chords = parse_rpp_chords(rpp_text, metadata.bpm)
        except Exception as e:
            logger.warning(f"Não foi possível processar cifras para {metadata.name}: {e}")
            
        if validate_chords and chords:
            from core.chord_theory import PITCH_TO_NOTE, chord_to_roman
            print(f"\n--- Relatório de Validação de Cifras ---")
            print(f"Música: {metadata.name} | Tom: {metadata.key}")
            print(f"{'Grau':<8} | {'Acorde':<8} | {'Pitches Esperados':<20} | {'Pitches Tocados':<20} | Status")
            print("-" * 75)
            for entry in chords:
                if entry.match:
                    grau = chord_to_roman(entry.name, metadata.key)
                    expected_notes = ", ".join(PITCH_TO_NOTE[p] for p in entry.match.expected)
                    played_notes = ", ".join(PITCH_TO_NOTE[p % 12] for p in entry.match.played)
                    status_icon = "✅ OK" if entry.match.status == "ok" else ("⚠️ PARTIAL" if entry.match.status == "partial" else "❌ MISMATCH")
                    print(f"{grau:<8} | {entry.name:<8} | {{{expected_notes}}:<18} | {{{played_notes}}:<18} | {status_icon}")
                else:
                    print(f"{'-':<8} | {entry.name:<8} | {'-':<18} | {'-':<18} | ❓ UNKNOWN")
            print("-" * 75)
            
        # Formata a mensagem para o Telegram
        msg_text = format_arrangement_message(metadata, regions, chords=chords, debug_chords=validate_chords)
        
        if validate_chords:
            # Em modo de validação, evitamos publicar/salvar no Telegram
            logger.info("Modo de validação ativo: publicação no Telegram evitada.")
            return True

        # Publica ou atualiza no Telegram
        msg_id = None
        if existing_msg_id:
            try:
                logger.info(f"Editando mensagem de arranjo existente: msg_id={existing_msg_id}")
                bot.edit_text_message(existing_msg_id, msg_text)
                msg_id = existing_msg_id
            except Exception as e:
                logger.warning(f"Não foi possível editar a mensagem {existing_msg_id} ({e}). Enviando uma nova.")
                
        if not msg_id:
            logger.info(f"Enviando novo mapa de arranjo para o tópico: {bot.arrangement_topic_id}")
            msg_id = bot.send_text_message(msg_text, bot.arrangement_topic_id)
            
        if msg_id:
            storage.mark_arrangement_synced(folder_id, msg_id, metadata=metadata)
            logger.info(f"✅ Arranjo de '{metadata.name}' sincronizado com sucesso! (msg_id={msg_id})")
            
            # Se a mensagem original da música (áudios) já existe, atualiza a legenda dela para incluir o link
            audio_msg_id = existing_entry.get("message_id")
            if audio_msg_id:
                try:
                    logger.info(f"Atualizando a legenda da mensagem de áudio original: {audio_msg_id}")
                    new_caption = bot.make_caption(metadata, arrangement_message_id=msg_id)
                    bot.edit_message_caption(audio_msg_id, new_caption)
                except Exception as e:
                    logger.warning(f"Não foi possível atualizar a legenda da música original: {e}")
                    
            return msg_id
            
    except Exception as e:
        logger.error(f"Erro ao processar arranjo de {metadata.name}: {e}")
        
    return None

def main(test_mode: bool = False, limit: int = None, force_update: bool = False, validate_chords: bool = False):
    onedrive = OneDriveClient()
    onedrive.authenticate()
    
    bot = TelegramBot()
    storage = TelegramStorage(bot)
    
    logger.info("Recuperando lista de músicas do OneDrive...")
    music_list = onedrive.get_file_list()
    processed = 0
    
    for item in tqdm(music_list, desc="Sincronizando arranjos"):
        if "file" in item:
            continue
            
        folder_id = item["id"]
        folder_name = item["name"]
        
        success = sync_arrangement_for_folder(
            folder_id=folder_id,
            folder_name=folder_name,
            onedrive=onedrive,
            bot=bot,
            storage=storage,
            force_update=force_update,
            validate_chords=validate_chords
        )
        
        if success:
            processed += 1
            
        if test_mode and processed >= 1:
            logger.info("Modo teste: 1 arranjo processado. Encerrando.")
            break
        if limit and processed >= limit:
            logger.info(f"Limite de {limit} arranjos atingido.")
            break
            
    logger.info(f"Concluído! {processed} arranjos sincronizados.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sincroniza os mapas de arranjo (.rpp) do OneDrive para o Telegram.")
    parser.add_argument("--test", action="store_true", help="Processa apenas 1 arranjo (modo teste)")
    parser.add_argument("--limit", type=int, default=None, help="Processa no máximo N arranjos")
    parser.add_argument("--update", action="store_true", help="Força a atualização de arranjos já sincronizados")
    parser.add_argument("--validate-chords", action="store_true", help="Valida a escrita das cifras comparando texto com as notas tocadas e exibe graus no terminal")
    args = parser.parse_args()
    
    main(test_mode=args.test, limit=args.limit, force_update=args.update, validate_chords=args.validate_chords)

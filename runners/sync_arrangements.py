import argparse
import logging
from tqdm import tqdm
from services.onedrive import OneDriveClient
from services.telegram import TelegramBot
from services.storage import OneDriveStorage
from core.name_parser import parse_music_metadata
from core.reaper_parser import parse_rpp_regions, format_arrangement_message

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def sync_arrangement_for_folder(folder_id: str, folder_name: str, onedrive: OneDriveClient, bot: TelegramBot, storage: OneDriveStorage, force_update: bool = False, validate_chords: bool = False):
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
        midi_keysig = "C"
        try:
            from core.reaper_parser import parse_rpp_keysig
            keysig = parse_rpp_keysig(rpp_text)
            midi_keysig = keysig or "C"
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
                    expected_str = f"{{{expected_notes}}}"
                    played_str = f"{{{played_notes}}}"
                    print(f"{grau:<8} | {entry.name:<8} | {expected_str:<18} | {played_str:<18} | {status_icon}")
                else:
                    print(f"{'-':<8} | {entry.name:<8} | {'-':<18} | {'-':<18} | ❓ UNKNOWN")
            print("-" * 75)
            
        # Formata a mensagem para o Telegram
        audio_link = None
        audio_msg_id = existing_entry.get("message_id")
        if audio_msg_id:
            chat_clean = str(bot.chat_id).replace("-100", "")
            audio_link = f"https://t.me/c/{chat_clean}/{audio_msg_id}"

        from core.reaper_parser import parse_rpp_tempo_map
        tempo_map = parse_rpp_tempo_map(rpp_text, metadata.bpm)

        # Gera o arquivo TXT
        from core.harmonic_map import build_harmonic_map
        from core.harmonic_layout import format_harmonic_txt
        import re
        import json
        from dataclasses import asdict

        sections = build_harmonic_map(metadata, regions, chords, tempo_map, midi_key=midi_keysig)
        
        safe_name = re.sub(r'[^a-z0-9_]', '', metadata.name.lower().replace(' ', '_'))
        safe_artist = re.sub(r'[^a-z0-9_]', '', metadata.artist.lower().replace(' ', '_'))
        
        # 1. Generate and upload JSON
        sections_dict = [asdict(s) for s in sections]
        json_content = json.dumps(sections_dict, indent=2, ensure_ascii=False)
        json_filename = f"{safe_name}_{safe_artist}_map.json"
        
        try:
            json_link = onedrive.upload_json_file(json_filename, json_content)
            logger.info(f"✅ Arquivo {json_filename} enviado para o OneDrive.")
        except Exception as e:
            logger.error(f"Erro ao fazer upload do JSON: {e}")
            json_link = None

        # 2. Generate and upload TXT (a partir dos dados extraídos)
        txt_content = format_harmonic_txt(metadata, sections)
        txt_filename = f"{safe_name}_{safe_artist}.txt"
        
        try:
            txt_link = onedrive.upload_txt_file(txt_filename, txt_content)
            logger.info(f"✅ Arquivo {txt_filename} enviado para o OneDrive.")
        except Exception as e:
            logger.error(f"Erro ao fazer upload do TXT: {e}")
            txt_link = None

        msg_text = format_arrangement_message(
            metadata, 
            regions, 
            chords=chords, 
            debug_chords=validate_chords,
            audio_link=audio_link,
            midi_key=midi_keysig,
            txt_link=txt_link,
            json_link=json_link
        )
        
        if validate_chords:
            # Em modo de validação, evitamos publicar/salvar no Telegram
            logger.info("Modo de validação ativo: publicação no Telegram evitada.")
            return True

        # Publica ou atualiza no Telegram (Removido: Agora apenas retornamos o txt_link)
        if txt_link:
            storage.mark_arrangement_synced(folder_id, txt_link, metadata=metadata)
            logger.info(f"✅ Arranjo de '{metadata.name}' processado (txt_link={txt_link})")
            
            # Se a mensagem original da música (áudios) já existe, atualiza a legenda dela para incluir o link
            audio_msg_id = existing_entry.get("message_id")
            if audio_msg_id:
                try:
                    logger.info(f"Atualizando a legenda da mensagem de áudio original: {audio_msg_id}")
                    new_caption = bot.make_caption(metadata, map_url=txt_link)
                    bot.edit_message_caption(audio_msg_id, new_caption)
                except Exception as e:
                    logger.warning(f"Não foi possível atualizar a legenda da música original: {e}")
                    
            return txt_link
            
    except Exception as e:
        logger.error(f"Erro ao processar arranjo de {metadata.name}: {e}")
        
    return None

def main(test_mode: bool = False, limit: int = None, force_update: bool = False, validate_chords: bool = False):
    onedrive = OneDriveClient()
    onedrive.authenticate()
    
    bot = TelegramBot()
    storage = OneDriveStorage(onedrive)
    
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

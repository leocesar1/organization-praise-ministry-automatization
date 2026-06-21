import argparse
import logging
import os
import re
from services.onedrive import OneDriveClient
from core.txt_parser import parse_harmonic_txt
from core.midi_writer import sections_to_chords, chords_to_rpp_midi_track

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def inject_track_into_rpp(rpp_content: str, new_item_block: str, new_track_block: str) -> str:
    """
    Se existir uma faixa chamada 'Cifras', substitui todos os seus blocos <ITEM pelo novo.
    Se não existir, injeta uma nova faixa no final.
    """
    lines = rpp_content.splitlines()
    output_lines = []
    
    in_target_track = False
    target_track_found = False
    
    stack = []
    
    i = 0
    skip_item = False
    item_depth = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Detect block opening
        if stripped.startswith("<"):
            block_type = stripped[1:].split()[0]
            stack.append(block_type)
            
            if block_type == "TRACK":
                # Look ahead to find track name
                is_cifras = False
                for j in range(i+1, min(i+15, len(lines))):
                    if lines[j].strip().startswith("NAME "):
                        match = re.match(r'^\s*NAME\s+(?:"([^"]*)"|(\S+))', lines[j])
                        if match:
                            t_name = match.group(1) if match.group(1) is not None else match.group(2)
                            if t_name.lower() in ["cifras", "acordes"]:
                                is_cifras = True
                        break
                
                if is_cifras:
                    in_target_track = True
                    target_track_found = True
                    logger.info("Faixa 'Cifras' encontrada. Substituindo o bloco <ITEM> interno.")
                    
            elif in_target_track and block_type == "ITEM":
                skip_item = True
                item_depth = len(stack)
        
        # If we are skipping an ITEM inside the target track, don't append it
        if not skip_item:
            output_lines.append(line)
            
        # Detect block closing
        if stripped == ">":
            if stack:
                closed_block = stack.pop()
                if skip_item and len(stack) < item_depth:
                    # The ITEM block just closed
                    skip_item = False
                elif in_target_track and len(stack) < stack_depth_when_track_opened:
                    # Target track closed
                    pass # Handled below
            
            # Re-evaluate in_target_track using stack depth
            if in_target_track and "TRACK" not in stack:
                # We just closed the target track.
                # BUT wait! We must insert the new item right BEFORE the `>` that closes the track!
                # Actually, `output_lines.append(line)` already appended the `>`.
                # So we should pop it, insert the item, and append `>` again.
                output_lines.pop()
                output_lines.extend(new_item_block.splitlines())
                output_lines.append(line)
                in_target_track = False
                
        # To robustly handle track open depth:
        if stripped.startswith("<TRACK"):
            stack_depth_when_track_opened = len(stack)

        i += 1
        
    if not target_track_found:
        logger.info("Faixa 'Cifras' não encontrada. Injetando uma nova faixa no final do projeto.")
        # Insert before the last ">"
        for j in range(len(output_lines) - 1, -1, -1):
            if output_lines[j].strip() == ">":
                new_track_lines = new_track_block.splitlines()
                output_lines = output_lines[:j] + new_track_lines + output_lines[j:]
                break
                
    return "\n".join(output_lines)

from core.midi_writer import sections_to_chords, chords_to_rpp_midi_track, chords_to_rpp_midi_item

def process_inverse_flow(txt_content: str, rpp_content: str) -> str:
    logger.info("Parseando TXT...")
    metadata, sections = parse_harmonic_txt(txt_content)
    
    logger.info("Convertendo seções para acordes...")
    chords = sections_to_chords(sections, metadata)
    
    logger.info(f"Gerando bloco MIDI para {len(chords)} acordes...")
    midi_item = chords_to_rpp_midi_item(chords, metadata.bpm, key=metadata.key)
    midi_track = chords_to_rpp_midi_track(chords, metadata.bpm, key=metadata.key)
    
    logger.info("Injetando faixa/item no RPP...")
    new_rpp_content = inject_track_into_rpp(rpp_content, midi_item, midi_track)
    
    return new_rpp_content

def main():
    parser = argparse.ArgumentParser(description="Atualiza um arquivo .rpp a partir de um mapa harmônico .txt.")
    parser.add_argument("--txt", help="Caminho para o arquivo TXT local")
    parser.add_argument("--rpp", help="Caminho para o arquivo RPP local")
    parser.add_argument("--folder", help="Nome exato da pasta no OneDrive (para buscar TXT e RPP)")
    parser.add_argument("--output", help="Caminho de saída para o novo .rpp (local)")
    parser.add_argument("--upload", action="store_true", help="Faz upload do .rpp modificado de volta para o OneDrive")
    args = parser.parse_args()
    
    if args.folder:
        logger.info(f"Buscando arquivos na pasta '{args.folder}' no OneDrive...")
        onedrive = OneDriveClient()
        onedrive.authenticate()
        
        folders = onedrive.get_file_list()
        folder_id = None
        for f in folders:
            if f.get("name") == args.folder:
                folder_id = f["id"]
                break
                
        if not folder_id:
            logger.error(f"Pasta '{args.folder}' não encontrada.")
            return
            
        rpp_name, rpp_bytes = onedrive.get_rpp_file(folder_id)
        if not rpp_bytes:
            logger.error("Arquivo .rpp não encontrado.")
            return
        rpp_content = rpp_bytes.decode("utf-8", errors="ignore")
        
        if args.txt:
            logger.info(f"Usando arquivo TXT local: {args.txt}")
            with open(args.txt, "r", encoding="utf-8") as f:
                txt_content = f.read()
        else:
            # The TXT file is inside the 'Mapas' folder
            mapas_folder_id = next((f['id'] for f in folders if f['name'].lower() == 'mapas'), None)
            if not mapas_folder_id:
                logger.error("Pasta 'Mapas' não encontrada no OneDrive.")
                return
                
            children = onedrive.get_file_list(mapas_folder_id)
            
            # We need to construct the expected filename. `sync_arrangements.py` creates it via:
            from core.name_parser import parse_music_metadata
            metadata = parse_music_metadata(args.folder)
            safe_name = re.sub(r'[^a-z0-9_]', '', metadata.name.lower().replace(' ', '_'))
            safe_artist = re.sub(r'[^a-z0-9_]', '', metadata.artist.lower().replace(' ', '_'))
            expected_txt_name = f"{safe_name}_{safe_artist}.txt"
            
            txt_file_id = None
            for c in children:
                if c.get("name") == expected_txt_name:
                    txt_file_id = c["id"]
                    break
                    
            if not txt_file_id:
                logger.error(f"Arquivo TXT '{expected_txt_name}' não encontrado na pasta Mapas.")
                return
                
            txt_bytes = onedrive.download_file(txt_file_id)
            txt_content = txt_bytes.decode("utf-8", errors="ignore")
            
        new_rpp = process_inverse_flow(txt_content, rpp_content)
        
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(new_rpp)
            logger.info(f"RPP salvo localmente em {args.output}")
        else:
            logger.info(f"Fazendo upload e substituindo '{rpp_name}' no OneDrive...")
            url = onedrive.upload_file(rpp_name, new_rpp.encode("utf-8"), folder_id)
            logger.info(f"Upload concluído com sucesso! Link: {url}")
            
    elif args.txt and args.rpp:
        with open(args.txt, "r", encoding="utf-8") as f:
            txt_content = f.read()
            
        with open(args.rpp, "r", encoding="utf-8", errors="ignore") as f:
            rpp_content = f.read()
            
        new_rpp = process_inverse_flow(txt_content, rpp_content)
        
        out_path = args.output or args.rpp.replace(".rpp", "_updated.rpp")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(new_rpp)
        logger.info(f"RPP atualizado salvo em {out_path}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

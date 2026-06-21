import os
from core.name_parser import parse_music_metadata
from core.reaper_parser import parse_rpp_regions, parse_rpp_chords, parse_rpp_tempo_map, parse_rpp_keysig
from core.harmonic_map import build_harmonic_map
from core.harmonic_layout import format_harmonic_txt

def test_local_file():
    filepath = '/Users/marques/Documents/Música/Louvor/Primeira Essencia [Elite] _ Ab _ Felipe Rodrigues _ 69BPM _ 4.4.rpp'
    if not os.path.exists(filepath):
        print(f"Arquivo não encontrado: {filepath}")
        return
        
    filename = os.path.basename(filepath)
    folder_name = filename.replace('.rpp', '')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        rpp_text = f.read()
        
    metadata = parse_music_metadata(folder_name)
    regions = parse_rpp_regions(rpp_text)
    tempo_map = parse_rpp_tempo_map(rpp_text, metadata.bpm)
    chords = parse_rpp_chords(rpp_text, metadata.bpm)
    midi_keysig = parse_rpp_keysig(rpp_text) or metadata.key
    
    sections = build_harmonic_map(metadata, regions, chords, tempo_map, midi_key=midi_keysig)
    txt_content = format_harmonic_txt(metadata, sections)
    
    print(txt_content)

if __name__ == '__main__':
    test_local_file()

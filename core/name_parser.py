import re
import unicodedata
from core.models import MusicMetadata

INSTRUMENTS = {
    "baixo", "bateria", "guitarra", "teclado", "violão",
    "vocal", "voz", "piano", "contrabaixo", "percussão", "acústico"
}

def normalize_compass(compass: str) -> str:
    """Normalizes compass strings like '4.4', '6 1.8' to '4/4', '6/8'."""
    compass = compass.replace(".", "/").replace(" ", "")
    if "1/8" in compass or "1.8" in compass:
        compass = compass.replace("1/8", "/8").replace("1.8", "/8")
    if "2/4" in compass or "2.4" in compass:
        compass = compass.replace("2/4", "/4").replace("2.4", "/4")
    return compass.strip()

def parse_music_metadata(folder_name: str) -> MusicMetadata:
    """
    Padrão A: Nome [Elite?] _ Tom _ Artista(s) _ BPMbpm _ Compasso
    Padrão B: Instrumento _ Nome [Elite?] _ Tom _ Artista(s) _ BPMbpm _ Compasso
    """
    segments = [s.strip() for s in folder_name.split(" _ ")]
    
    first = segments[0].strip().lower()
    is_pattern_b = first in INSTRUMENTS
    
    instrument = None
    if is_pattern_b:
        instrument = segments[0].strip()
        segments = segments[1:]
    
    if len(segments) >= 5:
        name_segment = segments[0]
        key = segments[1]
        artist = segments[2]
        bpm_str = segments[-2]
        compass_str = segments[-1]
    elif len(segments) == 4:
        # Padrão A, mas sem compasso ou sem BPM? Tentativa de parse
        name_segment = segments[0]
        key = segments[1]
        artist = segments[2]
        bpm_str = segments[3]
        compass_str = "4/4" # fallback
    else:
        # Fallback genérico para menos segmentos
        name_segment = segments[0]
        key = segments[1] if len(segments) > 1 else ""
        artist = segments[2] if len(segments) > 2 else ""
        bpm_str = segments[3] if len(segments) > 3 else "0BPM"
        compass_str = segments[4] if len(segments) > 4 else "4/4"

    elite = False
    name = name_segment
    if "[Elite]" in name_segment or "[ELITE]" in name_segment or "(Elite)" in name_segment:
        elite = True
        name = re.sub(r'\[Elite\]|\[ELITE\]|\(Elite\)', '', name_segment, flags=re.IGNORECASE).strip()

    bpm = 0.0
    try:
        bpm_match = re.search(r'([\d.]+)', bpm_str)
        if bpm_match:
            bpm = float(bpm_match.group(1).replace(',', '.'))
    except ValueError:
        pass
    
    name = unicodedata.normalize('NFC', name.strip())
    artist = unicodedata.normalize('NFC', artist.strip())
    compass = normalize_compass(compass_str)
    
    return MusicMetadata(
        name=name,
        artist=artist,
        key=key,
        bpm=bpm,
        compass=compass,
        elite=elite,
        instrument=instrument
    )

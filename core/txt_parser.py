import re
from core.models import MusicMetadata
from core.harmonic_map import HarmonicSection, HarmonicMeasure, HarmonicBeat
from core.chord_theory import NOTE_TO_PITCH, PITCH_TO_NOTE_SHARP, PITCH_TO_NOTE_FLAT, FLAT_KEYS, parse_chord_name

# Mapping superscripts back to normal characters
_SUPERSCRIPT_REVERSE: dict[str, str] = {
    "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
    "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    "ᵃ": "a", "ᵇ": "b", "ᶜ": "c", "ᵈ": "d", "ᵉ": "e",
    "ᶠ": "f", "ᵍ": "g", "ʰ": "h", "ⁱ": "i", "ʲ": "j",
    "ᵏ": "k", "ˡ": "l", "ᵐ": "m", "ⁿ": "n", "ᵒ": "o",
    "ᵖ": "p", "ʳ": "r", "ˢ": "s", "ᵗ": "t", "ᵘ": "u",
    "ᵛ": "v", "ʷ": "w", "ˣ": "x", "ʸ": "y", "ᶻ": "z",
    "⁺": "+", "⁻": "-", "⁼": "=", "°": "dim", "ᴹ": "M", "♭": "b", "♯": "#", "⁽": "(", "⁾": ")"
}

def from_superscript(text: str) -> str:
    """Converts a string from Unicode superscript characters to normal ones."""
    result = ""
    i = 0
    while i < len(text):
        char = text[i]
        # Handle special dim7 case (often written as °⁷)
        if char == "°" and i + 1 < len(text) and text[i+1] == "⁷":
            result += "dim7"
            i += 2
            continue
        result += _SUPERSCRIPT_REVERSE.get(char, char)
        i += 1
    return result

def parse_roman(roman: str) -> tuple[str, str]:
    """
    Parses a roman numeral string like 'IIm7' or 'bVImaj7' into (numeral, quality/extension).
    """
    # Regex to extract the base numeral (including optional flat/sharp) and the rest
    match = re.match(r"^([b♭#♯]?[IViv]+)(.*)$", roman.strip())
    if not match:
        return roman, ""
    
    numeral = match.group(1).replace('♭', 'b').replace('♯', '#')
    extension = match.group(2)
    return numeral, extension

def roman_to_chord_name(roman_token: str, key: str) -> str:
    """
    Converts a roman numeral token (e.g., 'IIm⁷', 'V') to an absolute chord name (e.g., 'Bm7', 'E')
    given the key. If the token is already an absolute chord name, returns it as is.
    """
    if not roman_token or roman_token in ["-", "%", "/"]:
        return roman_token

    # Handle slash chords
    if "/" in roman_token:
        parts = roman_token.split("/")
        if len(parts) == 2:
            base = roman_to_chord_name(parts[0], key)
            bass = roman_to_chord_name(parts[1], key)
            return f"{base}/{bass}"

    # Clean superscripts
    cleaned_token = from_superscript(roman_token)
    
    # Check if it's already an absolute chord name
    chord_info = parse_chord_name(cleaned_token)
    if NOTE_TO_PITCH.get(chord_info.root) is not None:
        # It's an absolute chord
        return cleaned_token

    # It's a roman numeral (or unparseable). Let's convert it.
    key_info = parse_chord_name(key)
    key_root_pitch = NOTE_TO_PITCH.get(key_info.root)
    if key_root_pitch is None:
        return cleaned_token # Give up if key is invalid
        
    is_minor_key = key_info.quality.endswith("m") or "minor" in key_info.quality.lower()

    numeral, extension = parse_roman(cleaned_token)
    
    # Determine minor quality from numeral casing
    # Roman numeral is lowercase if it represents a minor/diminished chord
    is_minor_numeral = numeral.lower() == numeral and numeral != numeral.upper()
    
    # Ensure extension is consistent with minorness
    if is_minor_numeral and not extension.startswith("m") and not extension.startswith("dim"):
        if extension.startswith("7"):
            extension = "m" + extension
        elif not extension:
            extension = "m"
            
    numeral_upper = numeral.upper()

    if not is_minor_key:
        # Major key mapping (Semitone diffs from root)
        numeral_map = {
            "I": 0, "BII": 1, "II": 2, "BIII": 3, "III": 4, "IV": 5,
            "#IV": 6, "V": 7, "BVI": 8, "VI": 9, "BVII": 10, "VII": 11
        }
    else:
        # Minor key mapping (Semitone diffs from root)
        numeral_map = {
            "I": 0, "BII": 1, "II": 2, "BIII": 3, "III": 4, "IV": 5,
            "#IV": 6, "V": 7, "BVI": 8, "VI": 9, "BVII": 10, "VII": 11
        }
        
    diff = numeral_map.get(numeral_upper)
    if diff is None:
        return cleaned_token # Unrecognized numeral
        
    target_pitch = (key_root_pitch + diff) % 12
    
    # Choose sharp or flat note names based on key
    note_map = PITCH_TO_NOTE_FLAT if key in FLAT_KEYS else PITCH_TO_NOTE_SHARP
    root_name = note_map.get(target_pitch, PITCH_TO_NOTE_SHARP[target_pitch])
    
    return f"{root_name}{extension}"

def parse_harmonic_txt(txt_content: str) -> tuple[MusicMetadata, list[HarmonicSection]]:
    """
    Parses a harmonic map TXT file and reconstructs the MusicMetadata and the structure.
    """
    lines = txt_content.splitlines()
    
    # 1. Parse Metadata
    metadata_dict = {
        "name": "Desconhecido",
        "artist": "Desconhecido",
        "key": "C",
        "bpm": 120.0,
        "compass": "4/4"
    }
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if "MÚSICA" in line and ":" in line:
            metadata_dict["name"] = line.split(":", 1)[1].strip()
        elif "ARTISTA" in line and ":" in line:
            metadata_dict["artist"] = line.split(":", 1)[1].strip()
        elif "TOM" in line and ":" in line:
            metadata_dict["key"] = line.split(":", 1)[1].strip()
        elif "BPM" in line and ":" in line:
            bpm_str = line.split(":", 1)[1].strip()
            bpm_match = re.search(r'([\d.]+)', bpm_str)
            if bpm_match:
                metadata_dict["bpm"] = float(bpm_match.group(1))
        elif "COMPASSO" in line and ":" in line:
            metadata_dict["compass"] = line.split(":", 1)[1].strip()
        elif "ROADMAP" in line:
            pass # Ignore for now
        elif "compassos" in line and "(" in line and ")" in line:
            # Reached the first section
            break
        i += 1
        
    metadata = MusicMetadata(
        name=metadata_dict["name"],
        artist=metadata_dict["artist"],
        key=metadata_dict["key"],
        bpm=metadata_dict["bpm"],
        compass=metadata_dict["compass"],
        elite=False
    )
    
    # Parse Sections
    sections = []
    
    current_section = None
    current_measures = []
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Section Header: NOME (compassos X-Y)
        if "compassos" in line and "(" in line and ")" in line:
            if current_section:
                current_section.measures = current_measures
                sections.append(current_section)
                
            match = re.match(r"^(.*?)\s*\(compassos\s*(\d+)-(\d+)\)", line.replace("=", "").strip())
            if match:
                sec_name = match.group(1).strip()
                start_m = int(match.group(2))
                end_m = int(match.group(3))
                current_section = HarmonicSection(
                    name=sec_name,
                    start_measure=start_m,
                    end_measure=end_m,
                    measures=[]
                )
                current_measures = []
        
        # Table rows: | chord | chord |
        elif line.startswith("|"):
            # If the line contains ONLY slashes, pipes, spaces, and syncopation arrows, it's a beat row (orphaned). Skip it.
            if re.match(r'^[\s\|\/←→]+$', line):
                i += 1
                continue
                
            chord_row = [c.strip() for c in line.split("|")[1:-1]]
            
            # Look ahead for beat row
            beat_row_line = ""
            if i + 1 < len(lines) and lines[i+1].strip().startswith("|") and re.match(r'^[\s\|\/←→]+$', lines[i+1].strip()):
                beat_row_line = lines[i+1].strip()
                i += 1
                
            beat_row = [b.strip() for b in beat_row_line.split("|")[1:-1]]
            
            # Combine into measures
            for m_idx in range(len(chord_row)):
                c_str = chord_row[m_idx]
                b_str = beat_row[m_idx] if m_idx < len(beat_row) else ""
                
                chord_matches = list(re.finditer(r'\S+', c_str))
                beat_matches = list(re.finditer(r'\S+', b_str))
                
                chords_in_m = [m.group() for m in chord_matches]
                beats_in_m = [m.group() for m in beat_matches]
                
                if not chords_in_m:
                    continue
                    
                # Parse beats
                measure_beats = []
                
                # Handling single chord for whole measure
                if len(chords_in_m) == 1 and (not beats_in_m or len(beats_in_m) > 1 and chords_in_m[0] not in ["-", "%"]):
                    chord_name = chords_in_m[0]
                    # Check syncopation on the only chord
                    sync = ""
                    if chord_name.startswith("←"):
                        sync = "←"
                        chord_name = chord_name[1:]
                    elif chord_name.startswith("→"):
                        sync = "→"
                        chord_name = chord_name[1:]
                        
                    for b_idx in range(len(beats_in_m) if beats_in_m else 4):
                        if b_idx == 0:
                            measure_beats.append(HarmonicBeat(
                                chord_roman=chord_name,
                                sync=sync,
                                is_start=True
                            ))
                        else:
                            measure_beats.append(HarmonicBeat(
                                chord_roman=chord_name,
                                sync="",
                                is_start=False
                            ))
                else:
                    # Distribute chords across beats by visual alignment
                    num_chords = len(chords_in_m)
                    num_beats = len(beats_in_m) if beats_in_m else 4
                    
                    # Map each chord to the closest beat index
                    chord_to_beat_idx = {}
                    if beat_matches:
                        for c_match in chord_matches:
                            c_start = c_match.start()
                            # Find beat with minimum distance
                            closest_b_idx = 0
                            min_dist = float('inf')
                            for b_idx, b_match in enumerate(beat_matches):
                                dist = abs(c_start - b_match.start())
                                if dist < min_dist:
                                    min_dist = dist
                                    closest_b_idx = b_idx
                            # If two chords map to the same beat, they will override (should not happen in well-formatted text)
                            chord_to_beat_idx[closest_b_idx] = c_match.group()
                    else:
                        # Fallback if no explicit beats (just map 0 to first chord)
                        chord_to_beat_idx[0] = chords_in_m[0]

                    last_chord = "-"
                    
                    for b_idx in range(num_beats):
                        b_token = beats_in_m[b_idx] if b_idx < len(beats_in_m) else "/"
                        is_start = False
                        sync = ""
                        
                        # See if we should switch to the next chord at this beat
                        if b_idx in chord_to_beat_idx:
                            cand = chord_to_beat_idx[b_idx]
                            cand_sync = ""
                            if cand.startswith("←"):
                                cand_sync = "←"
                                cand = cand[1:]
                            elif cand.startswith("→"):
                                cand_sync = "→"
                                cand = cand[1:]
                                
                            current_chord = cand
                            sync = cand_sync
                            is_start = True
                        else:
                            current_chord = last_chord
                            
                        # If the beat token itself implies a syncopation (though less common in this format)
                        if b_token.startswith("←") and sync == "":
                            sync = "←"
                        elif b_token.startswith("→") and sync == "":
                            sync = "→"

                        measure_beats.append(HarmonicBeat(
                            chord_roman=current_chord,
                            sync=sync,
                            is_start=is_start
                        ))
                        last_chord = current_chord
                        
                # Determine measure number
                m_num = current_section.start_measure + len(current_measures) if current_section else 1
                
                current_measures.append(HarmonicMeasure(
                    number=m_num,
                    beats=measure_beats
                ))

        i += 1
        
    if current_section:
        current_section.measures = current_measures
        sections.append(current_section)
        
    return metadata, sections

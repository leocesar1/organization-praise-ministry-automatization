import re
from dataclasses import dataclass

# Note names and their pitch classes
NOTE_TO_PITCH = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
    "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11
}

PITCH_TO_NOTE = {
    0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F",
    6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"
}

PITCH_TO_NOTE_SHARP = PITCH_TO_NOTE
PITCH_TO_NOTE_FLAT = {
    0: "C", 1: "Db", 2: "D", 3: "Eb", 4: "E", 5: "F",
    6: "Gb", 7: "G", 8: "Ab", 9: "A", 10: "Bb", 11: "B"
}
FLAT_KEYS = {"F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb", "Dm", "Gm", "Cm", "Fm", "Bbm", "Ebm", "Abm"}

# Supported chord qualities and their intervals in semitones relative to root
QUALITY_INTERVALS = {
    "": [0, 4, 7],               # Major
    "m": [0, 3, 7],              # Minor
    "min": [0, 3, 7],            # Minor alias
    "7": [0, 4, 7, 10],          # Dominant 7th
    "maj7": [0, 4, 7, 11],       # Major 7th
    "m7": [0, 3, 7, 10],         # Minor 7th
    "min7": [0, 3, 7, 10],       # Minor 7th alias
    "dim": [0, 3, 6],            # Diminished
    "dim7": [0, 3, 6, 9],        # Diminished 7th
    "aug": [0, 4, 8],            # Augmented
    "sus2": [0, 2, 7],           # Suspended 2nd
    "sus4": [0, 5, 7],           # Suspended 4th
    "9": [0, 4, 7, 10, 14],      # Dominant 9th
    "add9": [0, 4, 7, 14],       # Major add 9
    "m9": [0, 3, 7, 10, 14],     # Minor 9th
    "6": [0, 4, 7, 9],           # Major 6th
    "m6": [0, 3, 7, 9],          # Minor 6th
    "7M": [0, 4, 7, 11],         # Major 7th alias
    "7(9)": [0, 4, 7, 10, 14],   # Dominant 7(9)
    "9sus4": [0, 5, 7, 10, 14],  # 9sus4
    "m7(b5)": [0, 3, 6, 10],     # Half-diminished
    "°": [0, 3, 6],              # Dim alias
    "+": [0, 4, 8],              # Aug alias
}

ROMAN_NUMERALS = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI", 7: "VII"
}

# Character-level superscript map (covers digits + common chord quality letters)
_SUPERSCRIPT_CHARS: dict[str, str] = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
    "a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ",
    "f": "ᶠ", "g": "ᵍ", "h": "ʰ", "i": "ⁱ", "j": "ʲ",
    "k": "ᵏ", "l": "ˡ", "m": "ᵐ", "n": "ⁿ", "o": "ᵒ",
    "p": "ᵖ", "r": "ʳ", "s": "ˢ", "t": "ᵗ", "u": "ᵘ",
    "v": "ᵛ", "w": "ʷ", "x": "ˣ", "y": "ʸ", "z": "ᶻ",
    "+": "⁺", "-": "⁻", "=": "⁼",
}

def to_superscript(text: str) -> str:
    """Converts a string to Unicode superscript characters where available."""
    return "".join(_SUPERSCRIPT_CHARS.get(c, c) for c in text)


# Chord quality display rules for Roman numeral notation:
# Each entry maps the written quality suffix to (superscript_display, prepend_minor_m)
# 'superscript_display' is what goes as superscript after the Roman numeral.
# When the quality is empty (""), nothing is added (major chord).
QUALITY_SUPERSCRIPT: dict[str, str] = {
    "": "",
    "m": "",         # minor conveyed by lowercase numeral
    "min": "",       # alias for "m"
    "7": "⁷",
    "maj7": "ᵐᵃʲ⁷",
    "m7": "⁷",       # 'm' shown via lowercase numeral
    "min7": "⁷",     # alias for "m7"
    "dim": "°",
    "dim7": "°⁷",
    "aug": "⁺",
    "sus2": "ˢᵘˢ²",
    "sus4": "ˢᵘˢ⁴",
    "9": "⁹",
    "add9": "ᵃᵈᵈ⁹",
    "m9": "⁹",
    "min9": "⁹",
    "6": "⁶",
    "m6": "⁶",
    "min6": "⁶",
    "7M": "⁷ᴹ",
    "7(9)": "⁷⁽⁹⁾",
    "9sus4": "⁹ˢᵘˢ⁴",
    "m7(b5)": "⁷⁽♭⁵⁾",
    "°": "°",
    "+": "⁺",
}

@dataclass
class ChordEntry:
    beat: float
    duration: float
    name: str            # nome escrito (ou inferido)
    pitches: list[int]   # pitches MIDI tocados
    match: ChordMatch | None
    inferred: bool = False   # True se nome foi inferido (sem texto)

@dataclass
class ChordInfo:
    root: str
    quality: str
    bass: str | None = None

@dataclass
class ChordMatch:
    status: str           # "ok" | "partial" | "mismatch" | "unknown"
    score: float          # 0.0 to 1.0
    expected: frozenset[int]
    played: frozenset[int]
    missing: frozenset[int]
    extra: frozenset[int]
    note: str

def parse_chord_name(name: str) -> ChordInfo:
    """
    Parses a chord name like 'C#m7/E' into root, quality, and bass.
    """
    # Regex to capture root note (including accidentals), quality and optional slash bass
    match = re.match(r"^([A-G][#b]?)(.*?)(?:/([A-G][#b]?))?$", name.strip())
    if not match:
        return ChordInfo(root=name, quality="")
    
    root = match.group(1)
    quality = match.group(2)
    bass = match.group(3)
    return ChordInfo(root=root, quality=quality, bass=bass)

def chord_pitch_classes(info: ChordInfo) -> frozenset[int]:
    """
    Returns the set of pitch classes (0-11) expected for the given ChordInfo.
    """
    root_pitch = NOTE_TO_PITCH.get(info.root)
    if root_pitch is None:
        return frozenset()
        
    intervals = QUALITY_INTERVALS.get(info.quality)
    if intervals is None:
        # Fallback to major triad if quality is not fully known/supported
        intervals = QUALITY_INTERVALS[""]
        
    pitches = {(root_pitch + interval) % 12 for interval in intervals}
    if info.bass:
        bass_pitch = NOTE_TO_PITCH.get(info.bass)
        if bass_pitch is not None:
            pitches.add(bass_pitch)
            
    return frozenset(pitches)

def match_chord(written: str, played_pitches: list[int]) -> ChordMatch:
    """
    Compares the written chord name with the played MIDI pitches.
    """
    played_classes = frozenset({p % 12 for p in played_pitches})
    
    # If no notes played, we cannot validate
    if not played_classes:
        return ChordMatch(
            status="unknown",
            score=0.0,
            expected=frozenset(),
            played=played_classes,
            missing=frozenset(),
            extra=frozenset(),
            note="Sem notas tocadas"
        )
        
    info = parse_chord_name(written)
    expected_classes = chord_pitch_classes(info)
    
    if not expected_classes:
        return ChordMatch(
            status="unknown",
            score=0.0,
            expected=expected_classes,
            played=played_classes,
            missing=frozenset(),
            extra=frozenset(),
            note=f"Acorde desconhecido: {written}"
        )
        
    missing = expected_classes - played_classes
    extra = played_classes - expected_classes
    
    # Calculate score based on how many expected notes are present
    matched_count = len(expected_classes & played_classes)
    score = matched_count / len(expected_classes)
    
    if score >= 1.0:
        status = "ok"
        note = "Combinação perfeita"
    elif score > 0.0:
        status = "partial"
        note = f"Parcial (faltam: {', '.join(PITCH_TO_NOTE[m] for m in missing)})"
    else:
        status = "mismatch"
        note = "Nenhuma nota bate"
        
    return ChordMatch(
        status=status,
        score=score,
        expected=expected_classes,
        played=played_classes,
        missing=missing,
        extra=extra,
        note=note
    )

def chord_to_roman(chord_name: str, key: str) -> str:
    """
    Converts a chord name to its Roman numeral harmonic degree representation relative to key.
    Extensions (7, maj7, m7, dim, etc.) are rendered as Unicode superscript characters.
    Minor degrees use lowercase Roman numerals.
    """
    if not key or chord_name in ["", "-", "%"]:
        return chord_name

    # Standardize/clean key
    key_info = parse_chord_name(key)
    key_root_pitch = NOTE_TO_PITCH.get(key_info.root)
    if key_root_pitch is None:
        return chord_name

    is_minor_key = key_info.quality.endswith("m") or "minor" in key_info.quality.lower()

    chord_info = parse_chord_name(chord_name)
    chord_root_pitch = NOTE_TO_PITCH.get(chord_info.root)
    if chord_root_pitch is None:
        return chord_name

    # Distance in semitones (0-11)
    diff = (chord_root_pitch - key_root_pitch) % 12

    # Map semitone diff to (Roman base, is_diatonic_minor)
    if not is_minor_key:
        roman_map = {
            0: ("I", False),
            1: ("♭II", False),
            2: ("II", True),
            3: ("♭III", False),
            4: ("III", True),
            5: ("IV", False),
            6: ("♯IV", False),
            7: ("V", False),
            8: ("♭VI", False),
            9: ("VI", True),
            10: ("♭VII", False),
            11: ("VII", False),
        }
    else:
        roman_map = {
            0: ("I", True),
            1: ("♭II", False),
            2: ("II", False),
            3: ("♭III", False),
            4: ("III", True),
            5: ("IV", True),
            6: ("♯IV", False),
            7: ("V", True),
            8: ("♭VI", False),
            9: ("VI", True),
            10: ("♭VII", False),
            11: ("VII", False),
        }

    roman_base, is_naturally_minor = roman_map.get(diff, (chord_info.root, False))
    orig_quality = chord_info.quality

    # Determine if the chord sounds minor (for lowercase Roman numeral)
    # Note: "maj7" starts with "m" but is major — must be excluded explicitly
    # Note: "min" / "min7" etc. are also minor variants
    chord_is_minor = (
        (orig_quality.startswith("m") and not orig_quality.startswith("maj"))
        or orig_quality.startswith("min")
        or orig_quality in ("dim", "dim7")
    )

    # Use lowercase Roman numeral for minor-sounding chords
    if chord_is_minor:
        numeral = roman_base.lower()
    else:
        numeral = roman_base

    # Extension superscript: look up in QUALITY_SUPERSCRIPT, fall back to to_superscript
    extension = QUALITY_SUPERSCRIPT.get(orig_quality, to_superscript(orig_quality))

    roman_chord = f"{numeral}{extension}"

    # Handle slash bass if present
    if chord_info.bass:
        bass_roman = chord_to_roman(chord_info.bass, key)
        roman_chord = f"{roman_chord}/{bass_roman}"

    return roman_chord

def infer_chord_name(played_pitches: list[int], key: str | None = None) -> str:
    """
    Infers the chord name from played MIDI pitches, considering the key signature.
    """
    played_classes = frozenset({p % 12 for p in played_pitches})
    if not played_classes:
        return "-"
        
    best_chord = "-"
    best_score = 0.0
    
    note_map = PITCH_TO_NOTE_FLAT if key in FLAT_KEYS else PITCH_TO_NOTE_SHARP
    
    # Try all possible pitch classes as roots (0-11)
    for root_pitch in range(12):
        root_name = note_map.get(root_pitch, PITCH_TO_NOTE_SHARP[root_pitch])
        for quality, intervals in QUALITY_INTERVALS.items():
            expected = frozenset({(root_pitch + interval) % 12 for interval in intervals})
            # Check intersection
            match_count = len(expected & played_classes)
            # Precision & Recall score
            score = match_count / max(len(expected), len(played_classes))
            if score > best_score:
                best_score = score
                best_chord = f"{root_name}{quality}"
                
    return best_chord if best_score >= 0.7 else "-"

from core.models import MusicMetadata
from core.harmonic_map import HarmonicSection, HarmonicMeasure

def _format_measure_cells(measure: HarmonicMeasure) -> tuple[str, str]:
    """
    Format a single measure into two lines (chords and beats).
    Returns (chord_string, beat_string).
    """
    chord_parts = []
    beat_parts = []
    
    # Check if measure is uniform (same chord everywhere, no syncopation except maybe first beat)
    first_chord = measure.beats[0].chord_roman
    is_uniform = True
    for b in measure.beats:
        if b.chord_roman != first_chord or b.sync != "":
            is_uniform = False
            break
            
    # Check if empty
    has_real_chords = any(b.chord_roman is not None and b.chord_roman != "-" for b in measure.beats)
    if not has_real_chords:
        chord_parts.append("-")
        beat_parts = ["/" for _ in measure.beats]
        return " " + " ".join(chord_parts), " " + "  ".join(beat_parts)

    if is_uniform:
        return f" {first_chord if first_chord else '-'}", " " + "  ".join(["/"] * len(measure.beats))
        
    for i, b in enumerate(measure.beats):
        label = b.chord_roman if b.chord_roman else "-"
        
        # If it's the first beat or there's a change/syncopation
        prev_chord = measure.beats[i-1].chord_roman if i > 0 else None
        is_change = b.is_start or (label != prev_chord)
        
        if is_change:
            chord_parts.append(f"{b.sync}{label}")
            beat_parts.append(f"{b.sync}/")
        else:
            chord_parts.append(" ") # empty space for chord
            beat_parts.append("/")
            
    # Assemble lines
    chord_line = ""
    beat_line = ""
    for i in range(len(measure.beats)):
        cp = chord_parts[i]
        bp = beat_parts[i]
        
        if cp.strip():
            chord_line += cp + " "
        else:
            chord_line += "   "
            
        beat_line += bp + "  "
        
    return chord_line.rstrip(), beat_line.rstrip()

def format_harmonic_txt(metadata: MusicMetadata, sections: list[HarmonicSection]) -> str:
    lines = []
    
    def sep():
        lines.append("=" * 80)
        
    sep()
    lines.append(" MAPA HARMÔNICO")
    sep()
    lines.append(f" MÚSICA  : {metadata.name}")
    lines.append(f" ARTISTA : {metadata.artist}")
    lines.append(f" TOM     : {metadata.key}")
    bpm_text = f"{metadata.bpm} BPM" if metadata.bpm > 0 else "0 BPM"
    lines.append(f" BPM     : {bpm_text}")
    lines.append(f" COMPASSO: {metadata.compass}")
    sep()
    lines.append("")
    
    # Roadmap
    if sections:
        roadmap = " | ".join(s.name for s in sections)
        lines.append(f" ROADMAP  →  {roadmap}")
        lines.append("")
        
    # Sections
    CELL_WIDTH = max(14, (int(metadata.compass.split('/')[0]) if metadata.compass else 4) * 3 + 2)
    
    for section in sections:
        sep()
        lines.append(f" {section.name.upper()} (compassos {section.start_measure}-{section.end_measure})")
        sep()
        
        measures = section.measures
        for i in range(0, len(measures), 4):
            chunk = measures[i:i+4]
            
            chord_row = []
            beat_row = []
            
            for m in chunk:
                c_str, b_str = _format_measure_cells(m)
                
                # Dynamic width
                c_str = f" {c_str}"
                b_str = f" {b_str}"
                
                col_width = max(CELL_WIDTH, len(c_str), len(b_str))
                
                c_str = c_str + " " * (col_width - len(c_str))
                b_str = b_str + " " * (col_width - len(b_str))
                
                chord_row.append(c_str)
                beat_row.append(b_str)
                
            lines.append("|" + "|".join(chord_row) + "|")
            lines.append("|" + "|".join(beat_row) + "|")
            lines.append("")
            
    return "\n".join(lines)

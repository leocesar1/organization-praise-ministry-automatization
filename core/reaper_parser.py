import re
import base64
from dataclasses import dataclass
from core.models import MusicMetadata
from core.chord_theory import (
    ChordEntry,
    ChordMatch,
    match_chord,
    chord_to_roman,
    infer_chord_name
)

@dataclass
class ReaperRegion:
    id: int
    name: str
    start_seconds: float
    end_seconds: float = 0.0

def parse_rpp_keysig(rpp_content: str) -> str | None:
    """
    Parseia a Key Signature do arquivo .rpp.
    O Reaper armazena isso na tag <KEYSIG:
    <KEYSIG
      num_accidentals mode ...
    >
    onde num_accidentals é um inteiro (positivo para sustenidos, negativo para bemóis)
    e mode é 0 para maior, 1 para menor.
    """
    # Procura por <KEYSIG seguido por linhas de números e fechamento >
    keysig_match = re.search(r'<\s*KEYSIG\s*\n\s*(-?\d+)\s+(\d+)', rpp_content, re.IGNORECASE)
    if not keysig_match:
        return None
        
    accidentals = int(keysig_match.group(1))
    mode = int(keysig_match.group(2)) # 0 = major, 1 = minor
    
    # Mapeamento do círculo de quintas (num_accidentals -> nota)
    # Maior:
    # 0=C, 1=G, 2=D, 3=A, 4=E, 5=B, 6=F#, 7=C#
    # -1=F, -2=Bb, -3=Eb, -4=Ab, -5=Db, -6=Gb, -7=Cb
    major_keys = {
        0: "C", 1: "G", 2: "D", 3: "A", 4: "E", 5: "B", 6: "F#", 7: "C#",
        -1: "F", -2: "Bb", -3: "Eb", -4: "Ab", -5: "Db", -6: "Gb", -7: "Cb"
    }
    
    # Menor (relativa):
    # 0=Am, 1=Em, 2=Bm, 3=F#m, 4=C#m, 5=G#m, 6=D#m, 7=A#m
    # -1=Dm, -2=Gm, -3=Cm, -4=Fm, -5=Bbm, -6=Ebm, -7=Abm
    minor_keys = {
        0: "Am", 1: "Em", 2: "Bm", 3: "F#m", 4: "C#m", 5: "G#m", 6: "D#m", 7: "A#m",
        -1: "Dm", -2: "Gm", -3: "Cm", -4: "Fm", -5: "Bbm", -6: "Ebm", -7: "Abm"
    }
    
    if mode == 1:
        return minor_keys.get(accidentals)
    return major_keys.get(accidentals)


def parse_rpp_regions(rpp_content: str) -> list[ReaperRegion]:
    """
    Parseia o conteúdo de um arquivo .rpp para extrair as regiões.
    As regiões no Reaper são identificadas por linhas que começam com 'MARKER'
    onde o campo flags tem o bit 0 ativo (número ímpar, ex: 1, 9).
    """
    marker_pattern = re.compile(
        r'^\s*MARKER\s+(\d+)\s+([\d.]+)\s+(?:"([^"]*)"|([^\s]+))\s+(\d+)',
        re.MULTILINE
    )
    
    starts = {}
    ends = {}
    
    for match in marker_pattern.finditer(rpp_content):
        r_id = int(match.group(1))
        r_pos = float(match.group(2))
        r_name = match.group(3) if match.group(3) is not None else match.group(4)
        r_flags = int(match.group(5))
        
        # Verifica se o bit 0 está ativo (flags é ímpar), indicando que é uma região
        if r_flags & 1:
            if r_name == "":
                ends[r_id] = r_pos
            else:
                starts[r_id] = (r_name, r_pos)
                
    regions = []
    for r_id, (name, start) in starts.items():
        end = ends.get(r_id, start)
        regions.append(ReaperRegion(id=r_id, name=name, start_seconds=start, end_seconds=end))
        
    regions.sort(key=lambda r: r.start_seconds)
    return regions

def parse_rpp_chords(rpp_content: str, project_bpm: float) -> list[ChordEntry]:
    """
    Varre o RPP buscando faixas MIDI que contêm acordes.
    Calcula as posições e durações dos acordes em batidas (beats) absolutas do projeto.
    Prioriza faixas chamadas 'Cifras' ou 'Acordes'.
    Se não encontrar, pega a primeira track MIDI que contiver acordes ou notas válidos.
    """
    bpm = project_bpm if project_bpm > 0 else 120.0
    tempo_match = re.search(r'PT\s+0\.000000000000\s+([\d.]+)', rpp_content)
    if tempo_match:
        bpm = float(tempo_match.group(1))
    else:
        tempo_match = re.search(r'TEMPO\s+([\d.]+)', rpp_content)
        if tempo_match:
            bpm = float(tempo_match.group(1))

    tracks = []
    lines = rpp_content.splitlines()
    
    current_track = None
    in_midi = False
    midi_depth = 0
    current_tick = 0
    ppq = 960
    current_item_pos = 0.0
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if line.startswith("<TRACK"):
            current_track = {"name": "", "events": [], "item_pos": 0.0, "item_bpm": bpm}
            in_midi = False
            current_item_pos = 0.0
            
        elif current_track is not None:
            if line.startswith("NAME "):
                name_match = re.match(r'^NAME\s+"([^"]*)"|NAME\s+([^\s]+)', line)
                if name_match:
                    val1 = name_match.group(1)
                    val2 = name_match.group(2)
                    current_track["name"] = val1 if val1 is not None else (val2 if val2 is not None else "")
            
            elif line.startswith("POSITION "):
                pos_match = re.match(r'^POSITION\s+([\d.-]+)', line)
                if pos_match:
                    current_item_pos = float(pos_match.group(1))
                    current_track["item_pos"] = current_item_pos
                    
            elif line.startswith("<SOURCE MIDI"):
                in_midi = True
                midi_depth = 1
                current_tick = 0
                hasdata_match = re.match(r'HASDATA\s+\d+\s+(\d+)', lines[i+1].strip())
                if hasdata_match:
                    ppq = int(hasdata_match.group(1))
                
                ign_tempo = None
                depth = 1
                j = i + 1
                while j < len(lines) and depth > 0:
                    l = lines[j].strip()
                    if l.startswith("<") and not l.startswith("</"):
                        depth += 1
                    elif l == ">":
                        depth -= 1
                    
                    if depth > 0:
                        ign_match = re.search(r'IGNTEMPO\s+1\s+([\d.]+)', l)
                        if ign_match:
                            ign_tempo = float(ign_match.group(1))
                    j += 1
                
                current_track["item_bpm"] = ign_tempo if ign_tempo else bpm
                
            elif in_midi:
                if line.startswith("<") and not line.startswith("</"):
                    if not line.startswith("<SOURCE"):
                        midi_depth += 1
                elif line == ">":
                    midi_depth -= 1
                    if midi_depth <= 0:
                        in_midi = False
                        continue
                
                match_e = re.match(r'^[Ee]\s+(\d+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)\s+([0-9a-fA-F]+)', line)
                match_x = re.match(r'^<[Xx]\s+(\d+)', line)
                
                if match_e:
                    delta = int(match_e.group(1))
                    current_tick += delta
                    status = int(match_e.group(2), 16)
                    pitch = int(match_e.group(3), 16)
                    vel = int(match_e.group(4), 16)
                    
                    event_type = status & 0xF0
                    if event_type == 0x90 and vel > 0:
                        current_track["events"].append({
                            "tick": current_tick,
                            "type": "note_on",
                            "pitch": pitch
                        })
                    elif event_type == 0x80 or (event_type == 0x90 and vel == 0):
                        current_track["events"].append({
                            "tick": current_tick,
                            "type": "note_off",
                            "pitch": pitch
                        })
                elif match_x:
                    delta = int(match_x.group(1))
                    current_tick += delta
                    i += 1
                    b64_data = lines[i].strip()
                    try:
                        decoded = base64.b64decode(b64_data)
                        if decoded.startswith(b'\xff'):
                            text_str = "".join([chr(b) for b in decoded if 32 <= b <= 126])
                            if "text" in text_str:
                                text_str = text_str.split("text")[-1].strip()
                            elif "lyric" in text_str:
                                text_str = text_str.split("lyric")[-1].strip()
                                
                            if text_str:
                                current_track["events"].append({
                                    "tick": current_tick,
                                    "type": "text",
                                    "text": text_str
                                })
                    except Exception:
                        pass
                        
            elif line == ">" and not in_midi:
                if current_track["events"] or (current_track["name"] or "").lower() in ["cifras", "acordes"]:
                    chords_resolved = []
                    events = current_track["events"]
                    
                    text_events = [ev for ev in events if ev["type"] == "text"]
                    note_ons = [ev for ev in events if ev["type"] == "note_on"]
                    note_offs = [ev for ev in events if ev["type"] == "note_off"]
                    
                    # If we have no text events, but we have note events, we can infer chords from note groups
                    if not text_events and note_ons:
                        # Group notes that start close to each other (e.g. within 40 ticks)
                        note_ons_sorted = sorted(note_ons, key=lambda n: n["tick"])
                        ticks_seen = set()
                        for no in note_ons_sorted:
                            t = no["tick"]
                            window = 40
                            if any(abs(t - ts) < window for ts in ticks_seen):
                                continue
                            ticks_seen.add(t)
                            
                            window_notes = [n for n in note_ons if abs(n["tick"] - t) < window]
                            window_pitches = [n["pitch"] for n in window_notes]
                            
                            inferred_name = infer_chord_name(window_pitches)
                            if inferred_name != "-":
                                text_events.append({
                                    "tick": t,
                                    "type": "text",
                                    "text": inferred_name,
                                    "inferred": True
                                })
                    
                    for te in text_events:
                        chord_tick = te["tick"]
                        chord_name = te["text"]
                        inferred = te.get("inferred", False)
                        
                        same_tick_notes = [no for no in note_ons if abs(no["tick"] - chord_tick) <= 40]
                        played_pitches = [no["pitch"] for no in same_tick_notes]
                        
                        duration_ticks = 960 * 4 # Default 4 tempos
                        
                        if same_tick_notes:
                            max_dur = 0
                            for no in same_tick_notes:
                                offs = [nf for nf in note_offs if nf["tick"] > chord_tick and nf["pitch"] == no["pitch"]]
                                if offs:
                                    dur = offs[0]["tick"] - chord_tick
                                    if dur > max_dur:
                                        max_dur = dur
                            if max_dur > 0:
                                duration_ticks = max_dur
                        
                        beat_in_item = chord_tick / ppq
                        item_start_beat = current_track["item_pos"] * (bpm / 60.0)
                        proj_beat = item_start_beat + beat_in_item * (bpm / current_track["item_bpm"])
                        
                        duration_beats = (duration_ticks / ppq) * (bpm / current_track["item_bpm"])
                        
                        # Validate pitches
                        match_res = None
                        if played_pitches:
                            match_res = match_chord(chord_name, played_pitches)
                            
                        chords_resolved.append(
                            ChordEntry(
                                beat=proj_beat,
                                duration=duration_beats,
                                name=chord_name,
                                pitches=played_pitches,
                                match=match_res,
                                inferred=inferred
                            )
                        )
                        
                    chords_resolved.sort(key=lambda x: x.beat)
                    chords_extended = []
                    for idx, entry in enumerate(chords_resolved):
                        next_start = chords_resolved[idx+1].beat if idx + 1 < len(chords_resolved) else (entry.beat + entry.duration)
                        gap = next_start - (entry.beat + entry.duration)
                        if gap <= 4.05:
                            extended_dur = next_start - entry.beat
                        else:
                            extended_dur = entry.duration
                        entry.duration = extended_dur
                        chords_extended.append(entry)
                        
                    current_track["chords"] = chords_extended
                    tracks.append(current_track)
                current_track = None
                
        i += 1

    if not tracks:
        return []
        
    selected_track = None
    for t in tracks:
        if (t["name"] or "").lower() in ["cifras", "acordes"] and t["chords"]:
            selected_track = t
            break
            
    if not selected_track:
        for t in tracks:
            if t["chords"]:
                selected_track = t
                break
                
    if selected_track:
        selected_track["chords"].sort(key=lambda x: x.beat)
        return selected_track["chords"]
        
    return []

def format_arrangement_message(
    metadata: MusicMetadata,
    regions: list[ReaperRegion],
    chords: list[ChordEntry] = None,
    debug_chords: bool = False
) -> str:
    """
    Formata o mapa de arranjo em MarkdownV2 para o Telegram,
    incluindo a grade de acordes por compasso abaixo de cada região se disponível.
    """
    def escape(text: str) -> str:
        if not text:
            return ""
        for char in ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']:
            text = text.replace(char, f'\\{char}')
        return text

    bpm = metadata.bpm if metadata.bpm > 0 else 120.0
    
    time_sig_numerator = 4
    time_sig_denominator = 4
    if metadata.compass:
        parts = metadata.compass.split("/")
        if len(parts) >= 2:
            try:
                time_sig_numerator = int(parts[0])
                time_sig_denominator = int(parts[1])
            except ValueError:
                pass
        elif len(parts) == 1:
            try:
                time_sig_numerator = int(parts[0])
            except ValueError:
                pass

    # For each chord entry, calculate its nominal beat and syncopation
    nominal_starts = {}
    if chords:
        for entry in chords:
            nb = int(round(entry.beat))
            dev = entry.beat - nb
            sync = ""
            if -0.62 <= dev <= -0.38:
                sync = "←"
            elif 0.38 <= dev <= 0.62:
                sync = "→"
            
            if debug_chords:
                if entry.match:
                    if entry.match.status == "ok":
                        chord_display = entry.name
                    elif entry.match.status == "partial":
                        chord_display = f"~{entry.name}"
                    else: # mismatch
                        chord_display = f"!{entry.name}"
                else:
                    chord_display = f"?{entry.name}"
            else:
                chord_display = chord_to_roman(entry.name, metadata.key)
                
            nominal_starts[nb] = (chord_display, sync)

    def get_nominal_chord_info_at(nb: int) -> tuple[str | None, str, bool]:
        if nb in nominal_starts:
            chord_display, sync = nominal_starts[nb]
            return chord_display, sync, True
            
        # Check if any chord is physically active at this beat
        if chords:
            for entry in chords:
                if entry.beat - 0.1 <= nb < entry.beat + entry.duration - 0.1:
                    if debug_chords:
                        if entry.match:
                            if entry.match.status == "ok":
                                chord_display = entry.name
                            elif entry.match.status == "partial":
                                chord_display = f"~{entry.name}"
                            else:
                                chord_display = f"!{entry.name}"
                        else:
                            chord_display = f"?{entry.name}"
                    else:
                        chord_display = chord_to_roman(entry.name, metadata.key)
                    return chord_display, "", False
        return None, "", False

    msg = f"🎵 *{escape(metadata.name)}*\n"
    msg += f"🎤 _{escape(metadata.artist)}_\n"
    
    bpm_text = f"{metadata.bpm} BPM" if metadata.bpm > 0 else "0 BPM"
    msg += f"🔑 Tom: *{escape(metadata.key)}* \\| ⏱ *{escape(bpm_text)}* \\| 🎼 Compasso: *{escape(metadata.compass)}*\n"
    msg += "━━━━━━━━━━━━━━━━━━━━\n\n"
    msg += "📋 *Estrutura / Arranjo:*\n"

    def format_measure_anticipation(m_state, prev_m_state) -> str:
        """Formats a single measure using the syncopation and slash notation.
        - Returns "-" if the measure has no chords
        - Returns "%" if identical to the previous measure
        - Otherwise returns chord labels with ←/→ and /
        """
        has_real_chords = any(chord[0] is not None and chord[0] != "-" for chord in m_state)
        if not has_real_chords:
            return "-"
            
        if prev_m_state is not None:
            if [c[0] for c in m_state] == [c[0] for c in prev_m_state] and [c[1] for c in m_state] == [c[1] for c in prev_m_state]:
                return "%"
                
        # Check if uniform
        first_chord = m_state[0][0]
        is_uniform = True
        for b in range(len(m_state)):
            if m_state[b][0] != first_chord or m_state[b][1] != "":
                is_uniform = False
                break
                
        if is_uniform:
            return first_chord if first_chord else "-"
            
        parts = []
        for b in range(len(m_state)):
            chord_display, sync, is_start = m_state[b]
            label = chord_display if chord_display else "-"
            if b == 0:
                parts.append(sync + label)
            else:
                prev_chord_display = m_state[b-1][0]
                is_change = is_start or (chord_display != prev_chord_display)
                if is_change:
                    parts.append(sync + label)
                else:
                    parts.append("/")
        return " ".join(parts)

    for r in regions:
        minutos = int(r.start_seconds) // 60
        segundos = int(r.start_seconds) % 60
        time_str = f"{minutos:02d}:{segundos:02d}"
        msg += f"`{time_str}` *{escape(r.name)}*\n"

        if chords:
            start_beat = r.start_seconds * (bpm / 60.0)
            end_beat = r.end_seconds * (bpm / 60.0)
            has_future_chords = any(cb.beat >= start_beat for cb in chords)

            if has_future_chords:
                nominal_start = int(round(start_beat))
                nominal_end = int(round(end_beat))
                total_beats = nominal_end - nominal_start

                if total_beats > 0:
                    num_measures = total_beats // time_sig_numerator
                    if num_measures == 0:
                        num_measures = 1
                        
                    slots_needed = num_measures * time_sig_numerator
                    beat_states = []
                    for offset in range(slots_needed):
                        nb = nominal_start + offset
                        chord_display, sync, is_start = get_nominal_chord_info_at(nb)
                        beat_states.append((chord_display, sync, is_start))

                    measures_states = [
                        beat_states[m * time_sig_numerator:(m + 1) * time_sig_numerator]
                        for m in range(num_measures)
                    ]

                    grid_lines = []
                    prev_m_state = None
                    formatted_measures = []
                    for m_state in measures_states:
                        formatted_measures.append(format_measure_anticipation(m_state, prev_m_state))
                        prev_m_state = m_state

                    for idx in range(0, len(formatted_measures), 4):
                        chunk = formatted_measures[idx:idx + 4]
                        chord_line = "┃ " + " ┃ ".join(chunk) + " ┃"
                        chord_line_esc = chord_line.replace('\\', '\\\\').replace('`', '\\`')
                        grid_lines.append(f"  `{chord_line_esc}`")

                    if grid_lines:
                        msg += "\n".join(grid_lines) + "\n"
        
    if regions:
        # A duração total é o fim da última região
        total_seconds = regions[-1].end_seconds
        tot_min = int(total_seconds) // 60
        tot_seg = int(total_seconds) % 60
        msg += f"\n*\\(Duração Total: {tot_min:02d}:{tot_seg:02d}\\)*"
        
    return msg

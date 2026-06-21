import base64
from core.models import MusicMetadata
from core.harmonic_map import HarmonicSection
from core.chord_theory import ChordEntry, chord_pitch_classes, parse_chord_name
from core.txt_parser import roman_to_chord_name

def sections_to_chords(sections: list[HarmonicSection], metadata: MusicMetadata) -> list[ChordEntry]:
    """
    Converts a list of HarmonicSections into a flat list of ChordEntry objects
    with absolute beat positions and absolute chord names.
    """
    chords = []
    
    time_sig_numerator = 4
    if metadata.compass:
        parts = metadata.compass.split("/")
        if len(parts) >= 1:
            try:
                time_sig_numerator = int(parts[0])
            except ValueError:
                pass
                
    current_chord_name = None
    current_start_beat = 0.0
    
    # We will accumulate the duration of the current chord until it changes
    for section in sections:
        for measure in section.measures:
            # Measure starts at beat: (measure.number - 1) * time_sig_numerator
            m_start_beat = (measure.number - 1) * time_sig_numerator
            
            for b_idx, beat in enumerate(measure.beats):
                abs_beat = m_start_beat + b_idx
                
                # Apply syncopation
                if beat.sync == "←":
                    abs_beat -= 0.5
                elif beat.sync == "→":
                    abs_beat += 0.5
                    
                if beat.chord_roman in ["%", "-"]:
                    chord_display = "-"
                else:
                    chord_display = beat.chord_roman
                    
                abs_name = roman_to_chord_name(chord_display, metadata.key)
                
                if abs_name and abs_name != "-" and (beat.is_start or abs_name != current_chord_name):
                    # Save previous chord
                    if current_chord_name and current_chord_name != "-":
                        duration = abs_beat - current_start_beat
                        if duration > 0:
                            chords.append(ChordEntry(
                                beat=current_start_beat,
                                duration=duration,
                                name=current_chord_name,
                                pitches=chord_to_midi_pitches(current_chord_name),
                                match=None,
                                inferred=False
                            ))
                            
                    current_chord_name = abs_name
                    current_start_beat = abs_beat
                    
    # Handle the very last chord
    if current_chord_name and current_chord_name != "-":
        # Estimate duration as 1 measure or remaining beats in last measure
        duration = time_sig_numerator
        chords.append(ChordEntry(
            beat=current_start_beat,
            duration=duration,
            name=current_chord_name,
            pitches=chord_to_midi_pitches(current_chord_name),
            match=None,
            inferred=False
        ))
        
    return chords

def chord_to_midi_pitches(chord_name: str, octave: int = 4) -> list[int]:
    """
    Converts a chord name into a list of MIDI pitches.
    Assumes a default octave if not specified.
    """
    info = parse_chord_name(chord_name)
    pitch_classes = chord_pitch_classes(info)
    
    if not pitch_classes:
        return []
        
    base_midi = (octave + 1) * 12
    
    pitches = []
    # If there's a bass note, ensure it's the lowest pitch
    bass_pitch_class = None
    if info.bass:
        from core.chord_theory import NOTE_TO_PITCH
        bass_pitch_class = NOTE_TO_PITCH.get(info.bass)
        
    for pc in pitch_classes:
        pitch = base_midi + pc
        
        # Adjust bass note to be an octave lower if necessary
        if bass_pitch_class is not None and pc == bass_pitch_class:
            pitches.append(pitch - 12)
        else:
            pitches.append(pitch)
            
    return sorted(pitches)

def generate_text_event_b64(text: str) -> str:
    """
    Encodes a text event for Reaper MIDI.
    Reaper text events are stored as base64 strings containing the binary MIDI event data.
    """
    # Meta event for Text (0x01)
    # Format: FF 01 length text
    # In Reaper <X events, we just need the raw bytes of the text, sometimes prefixed, but Reaper 
    # handles the FF 01 part itself if we just provide the base64 of the string or specific binary format.
    # Actually, Reaper's <X event data format:
    # First byte is event type. 0x01 = text event, 0x05 = lyric
    data = b'\x01' + text.encode('utf-8')
    # Prepend \xff ? No, the parser looks for \xff for standard meta events.
    # Actually, meta events start with FF, type, length, data.
    data = b'\xff\x01'
    
    # We must encode length as variable-length quantity (VLQ), but for short strings (<128) it's just the length byte
    length = len(text.encode('utf-8'))
    data += bytes([length]) + text.encode('utf-8')
    
    return base64.b64encode(data).decode('ascii')

def generate_keysig_event_b64(key_name: str) -> str:
    """
    Encodes a key signature event (0x59) for Reaper MIDI.
    """
    KEY_SIGNATURES = {
        "C": (0, 0), "G": (1, 0), "D": (2, 0), "A": (3, 0), "E": (4, 0), "B": (5, 0), "F#": (6, 0), "C#": (7, 0),
        "F": (-1, 0), "Bb": (-2, 0), "Eb": (-3, 0), "Ab": (-4, 0), "Db": (-5, 0), "Gb": (-6, 0), "Cb": (-7, 0),
        "Am": (0, 1), "Em": (1, 1), "Bm": (2, 1), "F#m": (3, 1), "C#m": (4, 1), "G#m": (5, 1), "D#m": (6, 1), "A#m": (7, 1),
        "Dm": (-1, 1), "Gm": (-2, 1), "Cm": (-3, 1), "Fm": (-4, 1), "Bbm": (-5, 1), "Ebm": (-6, 1), "Abm": (-7, 1)
    }
    sf, mi = KEY_SIGNATURES.get(key_name.replace(" ", ""), (0, 0))
    data = b'\xff\x59\x02' + bytes([sf & 0xFF, mi & 0xFF])
    return base64.b64encode(data).decode('ascii')

def chords_to_rpp_midi_item(chords: list[ChordEntry], bpm: float, key: str = "C", ppq: int = 960) -> str:
    """
    Generates a Reaper `<ITEM` block for a MIDI item containing the given chords.
    Includes key signature based on the provided key.
    """
    lines = []
    
    # Let's find the total length in seconds or beats to size the MIDI item
    if not chords:
        return ""
        
    last_chord = chords[-1]
    total_beats = last_chord.beat + last_chord.duration
    length_seconds = total_beats * (60.0 / bpm)
    
    lines.append('    <ITEM')
    lines.append('      POSITION 0')
    lines.append('      SNAPOFFS 0')
    lines.append(f'      LENGTH {length_seconds}')
    lines.append('      LOOP 0')
    lines.append('      ALLTAKES 0')
    lines.append('      FADEIN 1 0.000000 0 1 0 0.000000')
    lines.append('      FADEOUT 1 0.000000 0 1 0 0.000000')
    lines.append('      MUTE 0 0')
    lines.append('      SEL 0')
    lines.append('      IGUID {00000000-0000-0000-0000-000000000000}')
    lines.append('      IID 1')
    lines.append('      NAME "Cifras - Geradas"')
    lines.append('      VOLPAN 1 0 -1 -1')
    lines.append('      SOFFS 0')
    lines.append('      PLAYRATE 1 1 0 -1 0')
    lines.append('      CHANMODE 0')
    lines.append('      GUID {00000000-0000-0000-0000-000000000000}')
    lines.append('      <SOURCE MIDI')
    lines.append(f'        HASDATA 1 {ppq} QN')
    lines.append(f'        IGNTEMPO 1 {bpm} 4 4') # Using default 4/4 as it doesn't strictly matter for MIDI playback
    
    current_tick = 0
    
    # Sort chords by beat just in case
    sorted_chords = sorted(chords, key=lambda c: c.beat)
    
    # Generate events
    # We need:
    # 0. Key Signature event (<X 0 \n base64 \n >)
    # 1. Text events (<X tick_delta \n base64 \n >)
    # 2. Note On events (e tick_delta 90 pitch vel)
    # 3. Note Off events (e tick_delta 80 pitch 0)
    
    # Create an absolute timeline of events
    events = []
    
    # Add key signature at tick 0
    events.append({'tick': 0, 'type': 'keysig', 'text': key})
    
    for chord in sorted_chords:
        start_tick = int(chord.beat * ppq)
        end_tick = int((chord.beat + chord.duration) * ppq)
        
        # Text event
        events.append({'tick': start_tick, 'type': 'text', 'text': chord.name})
        
        # Note On
        for pitch in chord.pitches:
            events.append({'tick': start_tick, 'type': 'note_on', 'pitch': pitch, 'vel': 96})
            # Note Off
            events.append({'tick': end_tick, 'type': 'note_off', 'pitch': pitch, 'vel': 0})
            
    events.sort(key=lambda e: (e['tick'], 0 if e['type'] in ('text', 'keysig') else 1 if e['type'] == 'note_off' else 2))
    
    for ev in events:
        delta = ev['tick'] - current_tick
        
        if ev['type'] == 'text':
            lines.append(f'        <X {delta} 0')
            lines.append(f'          {generate_text_event_b64(ev["text"])}')
            lines.append('        >')
            current_tick = ev['tick']
            
        elif ev['type'] == 'keysig':
            lines.append(f'        <X {delta} 0')
            lines.append(f'          {generate_keysig_event_b64(ev["text"])}')
            lines.append('        >')
            current_tick = ev['tick']
            
        elif ev['type'] == 'note_on':
            # e delta 90 pitch vel
            hex_pitch = f"{ev['pitch']:02x}"
            hex_vel = f"{ev['vel']:02x}"
            lines.append(f'        E {delta} 90 {hex_pitch} {hex_vel}')
            current_tick = ev['tick']
            
        elif ev['type'] == 'note_off':
            hex_pitch = f"{ev['pitch']:02x}"
            lines.append(f'        E {delta} 80 {hex_pitch} 00')
            current_tick = ev['tick']
            
    lines.append('        >') # End SOURCE MIDI
    lines.append('    >') # End ITEM
    
    return "\n".join(lines)

def chords_to_rpp_midi_track(chords: list[ChordEntry], bpm: float, key: str = "C", ppq: int = 960) -> str:
    """
    Generates a full Reaper `<TRACK` block.
    """
    lines = []
    lines.append('  <TRACK')
    lines.append('    NAME "Cifras"')
    lines.append('    PEAKCOL 16576')
    lines.append('    BEAT -1')
    
    item_block = chords_to_rpp_midi_item(chords, bpm, key, ppq)
    if item_block:
        lines.append(item_block)
        
    lines.append('  >')
    return "\n".join(lines)

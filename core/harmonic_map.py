from dataclasses import dataclass
from core.models import MusicMetadata
from core.chord_theory import ChordEntry, chord_to_roman
from core.reaper_parser import ReaperRegion, TempoMap

@dataclass
class HarmonicBeat:
    chord_roman: str | None
    sync: str
    is_start: bool

@dataclass
class HarmonicMeasure:
    number: int
    beats: list[HarmonicBeat]

@dataclass
class HarmonicSection:
    name: str
    start_measure: int
    end_measure: int
    measures: list[HarmonicMeasure]

def build_harmonic_map(
    metadata: MusicMetadata,
    regions: list[ReaperRegion],
    chords: list[ChordEntry] | None,
    tempo_map: TempoMap | None,
    midi_key: str | None = None
) -> list[HarmonicSection]:
    if not regions:
        return []
        
    chords = chords or []

    time_sig_numerator = 4
    if metadata.compass:
        parts = metadata.compass.split("/")
        if len(parts) >= 1:
            try:
                time_sig_numerator = int(parts[0])
            except ValueError:
                pass

    key_to_use = midi_key or metadata.key

    # Pre-calculate chord positions
    nominal_starts = {}
    for entry in chords:
        nb = int(round(entry.beat))
        dev = entry.beat - nb
        sync = ""
        if -0.62 <= dev <= -0.38:
            sync = "←"
        elif 0.38 <= dev <= 0.62:
            sync = "→"
            
        chord_display = chord_to_roman(entry.name, key_to_use)
        nominal_starts[nb] = (chord_display, sync)

    def get_nominal_chord_info_at(nb: int) -> tuple[str | None, str, bool]:
        if nb in nominal_starts:
            chord_display, sync = nominal_starts[nb]
            return chord_display, sync, True
            
        # Check if any chord is physically active at this beat
        for entry in chords:
            if entry.beat - 0.1 <= nb < entry.beat + entry.duration - 0.1:
                chord_display = chord_to_roman(entry.name, key_to_use)
                return chord_display, "", False
                
        return None, "", False

    bpm = metadata.bpm if metadata.bpm > 0 else 120.0
    sections = []
    global_measure_counter = 1

    for r in regions:
        if tempo_map:
            start_beat = tempo_map.time_to_beat(r.start_seconds)
            end_beat = tempo_map.time_to_beat(r.end_seconds)
        else:
            start_beat = r.start_seconds * (bpm / 60.0)
            end_beat = r.end_seconds * (bpm / 60.0)

        # Sempre processa a região mesmo sem acordes futuros

        nominal_start = int(round(start_beat))
        nominal_end = int(round(end_beat))
        total_beats = nominal_end - nominal_start

        if total_beats > 0:
            num_measures = total_beats // time_sig_numerator
            if num_measures == 0:
                num_measures = 1
                
            slots_needed = num_measures * time_sig_numerator
            
            section_measures = []
            for m in range(num_measures):
                measure_beats = []
                for b in range(time_sig_numerator):
                    nb = nominal_start + (m * time_sig_numerator) + b
                    chord_display, sync, is_start = get_nominal_chord_info_at(nb)
                    measure_beats.append(HarmonicBeat(
                        chord_roman=chord_display,
                        sync=sync,
                        is_start=is_start
                    ))
                
                section_measures.append(HarmonicMeasure(
                    number=global_measure_counter,
                    beats=measure_beats
                ))
                global_measure_counter += 1
                
            sections.append(HarmonicSection(
                name=r.name,
                start_measure=section_measures[0].number,
                end_measure=section_measures[-1].number,
                measures=section_measures
            ))

    return sections

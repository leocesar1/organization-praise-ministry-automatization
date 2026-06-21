import sys
from core.reaper_parser import parse_rpp_regions, parse_rpp_chords, format_arrangement_message
from core.name_parser import parse_music_metadata

def test_local_file(file_path: str):
    print(f"Reading file: {file_path}")
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        print(f"Failed to read file: {e}")
        return

    import os
    folder_name = os.path.splitext(os.path.basename(file_path))[0]
    metadata = parse_music_metadata(folder_name)
    
    # Override key using RPP keysig
    from core.reaper_parser import parse_rpp_keysig
    keysig = parse_rpp_keysig(content)
    midi_key = keysig or "C"
    if keysig:
        print(f"Tom extraído dos metadados RPP: '{keysig}' (anterior: '{metadata.key}')")
        metadata.key = keysig

    regions = parse_rpp_regions(content)
    print(f"Found {len(regions)} regions:")
    for r in regions:
        print(f"  - {r.name} ({r.start_seconds:.2f}s -> {r.end_seconds:.2f}s)")

    chords = parse_rpp_chords(content, metadata.bpm)
    print(f"\nFound {len(chords)} chords:")
    
    from core.chord_theory import PITCH_TO_NOTE, chord_to_roman
    print(f"\n--- Relatório de Validação de Cifras (Local) ---")
    print(f"{'Grau':<8} | {'Acorde':<8} | {'Pitches Esperados':<20} | {'Pitches Tocados':<20} | Status")
    print("-" * 75)
    for entry in chords:
        if entry.match:
            grau = chord_to_roman(entry.name, midi_key)
            expected_notes = ", ".join(PITCH_TO_NOTE[p] for p in entry.match.expected)
            played_notes = ", ".join(PITCH_TO_NOTE[p % 12] for p in entry.match.played)
            status_icon = "✅ OK" if entry.match.status == "ok" else ("⚠️ PARTIAL" if entry.match.status == "partial" else "❌ MISMATCH")
            expected_str = f"{{{expected_notes}}}"
            played_str = f"{{{played_notes}}}"
            print(f"{grau:<8} | {entry.name:<8} | {expected_str:<18} | {played_str:<18} | {status_icon}")
        else:
            print(f"{'-':<8} | {entry.name:<8} | {'-':<18} | {'-':<18} | ❓ UNKNOWN")
    print("-" * 75)

    from core.reaper_parser import parse_rpp_tempo_map
    tempo_map = parse_rpp_tempo_map(content, metadata.bpm)

    print("\nVisualização no modo normal (Graus Harmônicos):")
    msg_normal = format_arrangement_message(metadata, regions, chords=chords, debug_chords=False, audio_link="https://t.me/c/123456789/42", midi_key=midi_key, tempo_map=tempo_map)
    print(msg_normal)

    print("\nVisualização no modo diagnóstico (Marcadores de erro):")
    msg_debug = format_arrangement_message(metadata, regions, chords=chords, debug_chords=True, audio_link="https://t.me/c/123456789/42", midi_key=midi_key, tempo_map=tempo_map)
    print(msg_debug)

if __name__ == "__main__":
    path = "/Users/marques/Documents/Música/Louvor/Seu Sangue [Elite] - A - Fernandinho - 161BPM - 4.4.rpp"
    if len(sys.argv) > 1:
        path = sys.argv[1]
    test_local_file(path)


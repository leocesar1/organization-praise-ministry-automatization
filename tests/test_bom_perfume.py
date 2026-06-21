import unittest
from core.txt_parser import roman_to_chord_name, parse_harmonic_txt
from core.midi_writer import chord_to_midi_pitches, chords_to_rpp_midi_track, sections_to_chords

BOM_PERFUME_TXT = """================================================================================
 MAPA HARMÔNICO
================================================================================
 MÚSICA  : Bom Perfume
 ARTISTA : Gabi Sampaio
 TOM     : G
 BPM     : 71.0 BPM
 COMPASSO: 4/4
================================================================================

 ROADMAP  →  Intro | Verso 1 | Pré-Refrão | Refrão

================================================================================
 Intro (compassos 1-4)
================================================================================
| I             | IV            | I             | IV            |
| /  /  /  /    | /  /  /  /    | /  /  /  /    | /  /  /  /    |

================================================================================
 Verso 1 (compassos 5-8)
================================================================================
| I             | V             | VIm⁷          | IV            |
| /  /  /  /    | /  /  /  /    | /  /  /  /    | /  /  /  /    |

================================================================================
 Pré-Refrão (compassos 9-10)
================================================================================
| IIm⁷          | V             |
| /  /  /  /    | /  /  /  /    |

================================================================================
 Refrão (compassos 11-14)
================================================================================
| I             | V             | VIm⁷          | IV            |
| /  /  /  /    | /  /  /  /    | /  /  /  /    | /  /  /  /    |

"""

class TestBomPerfumeInverseFlow(unittest.TestCase):
    
    def test_roman_to_chord_name(self):
        # Tom de G Maior
        key = "G"
        
        self.assertEqual(roman_to_chord_name("I", key), "G")
        self.assertEqual(roman_to_chord_name("IV", key), "C")
        self.assertEqual(roman_to_chord_name("V", key), "D")
        
        # Testando minúsculo (menor)
        self.assertEqual(roman_to_chord_name("vi", key), "Em")
        self.assertEqual(roman_to_chord_name("VIm", key), "Em")
        
        # Extensões com superscripts
        self.assertEqual(roman_to_chord_name("VIm⁷", key), "Em7")
        self.assertEqual(roman_to_chord_name("IIm⁷", key), "Am7")
        
        # Absolute chord fallback
        self.assertEqual(roman_to_chord_name("Em7", key), "Em7")
        
        # Slash chords
        self.assertEqual(roman_to_chord_name("I/III", key), "G/B")
        
    def test_parse_harmonic_txt_sections(self):
        metadata, sections = parse_harmonic_txt(BOM_PERFUME_TXT)
        
        self.assertEqual(metadata.name, "Bom Perfume")
        self.assertEqual(metadata.artist, "Gabi Sampaio")
        self.assertEqual(metadata.key, "G")
        self.assertEqual(metadata.bpm, 71.0)
        self.assertEqual(metadata.compass, "4/4")
        
        self.assertEqual(len(sections), 4)
        self.assertEqual(sections[0].name, "Intro")
        self.assertEqual(sections[0].start_measure, 1)
        self.assertEqual(sections[0].end_measure, 4)
        
        self.assertEqual(sections[1].name, "Verso 1")
        self.assertEqual(sections[1].start_measure, 5)
        
    def test_parse_harmonic_txt_chords(self):
        metadata, sections = parse_harmonic_txt(BOM_PERFUME_TXT)
        chords = sections_to_chords(sections, metadata)
        
        # Total measures = 14
        # Intro: G, C, G, C (4 measures)
        # Verso: G, D, Em7, C (4 measures)
        # Pre: Am7, D (2 measures)
        # Refrao: G, D, Em7, C (4 measures)
        
        # We expect chords to be aggregated by consecutive blocks
        self.assertEqual(len(chords), 14)
        
        self.assertEqual(chords[0].name, "G")
        self.assertEqual(chords[0].beat, 0.0)
        self.assertEqual(chords[0].duration, 4.0)
        
        self.assertEqual(chords[1].name, "C")
        self.assertEqual(chords[1].beat, 4.0)
        self.assertEqual(chords[1].duration, 4.0)
        
        # Verso 1 starts at measure 5, beat 16.0
        self.assertEqual(chords[4].name, "G")
        self.assertEqual(chords[4].beat, 16.0)
        
        self.assertEqual(chords[5].name, "D")
        self.assertEqual(chords[5].beat, 20.0)
        
        self.assertEqual(chords[6].name, "Em7")
        self.assertEqual(chords[6].beat, 24.0)

    def test_chord_to_midi_pitches(self):
        # G Major Triad: G(7), B(11), D(2)
        # In Octave 4, base is 60. G=67, B=71, D=62. Sorted: [62, 67, 71]
        pitches_g = chord_to_midi_pitches("G", octave=4)
        self.assertEqual(pitches_g, [62, 67, 71])
        
        # Em7: E(4), G(7), B(11), D(2) -> 64, 67, 71, 62. Sorted: [62, 64, 67, 71]
        pitches_em7 = chord_to_midi_pitches("Em7", octave=4)
        self.assertEqual(pitches_em7, [62, 64, 67, 71])
        
        # Slash chord G/B
        # B as bass note should be dropped an octave: B3=59, D4=62, G4=67
        pitches_g_b = chord_to_midi_pitches("G/B", octave=4)
        self.assertEqual(pitches_g_b, [59, 62, 67])

    def test_full_inverse_flow(self):
        metadata, sections = parse_harmonic_txt(BOM_PERFUME_TXT)
        chords = sections_to_chords(sections, metadata)
        midi_block = chords_to_rpp_midi_track(chords, metadata.bpm)
        
        self.assertIn('<TRACK', midi_block)
        self.assertIn('NAME "Cifras"', midi_block)
        self.assertIn('<SOURCE MIDI', midi_block)
        # Should have hex code 90 for note on
        self.assertIn(' 90 ', midi_block)
        # Should have text events <X
        self.assertIn('<X ', midi_block)

if __name__ == "__main__":
    unittest.main()

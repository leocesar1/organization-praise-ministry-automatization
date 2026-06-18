import unittest
from core.chord_theory import (
    parse_chord_name,
    chord_pitch_classes,
    match_chord,
    chord_to_roman,
    infer_chord_name,
    ChordInfo,
    ChordMatch
)

class TestChordTheory(unittest.TestCase):
    def test_parse_chord_name(self):
        # Test basic chords
        info = parse_chord_name("C")
        self.assertEqual(info.root, "C")
        self.assertEqual(info.quality, "")
        self.assertIsNone(info.bass)
        
        info = parse_chord_name("Am")
        self.assertEqual(info.root, "A")
        self.assertEqual(info.quality, "m")
        
        info = parse_chord_name("F#7")
        self.assertEqual(info.root, "F#")
        self.assertEqual(info.quality, "7")
        
        info = parse_chord_name("Bbmaj7")
        self.assertEqual(info.root, "Bb")
        self.assertEqual(info.quality, "maj7")
        
        info = parse_chord_name("G/B")
        self.assertEqual(info.root, "G")
        self.assertEqual(info.quality, "")
        self.assertEqual(info.bass, "B")

    def test_chord_pitch_classes(self):
        # C major: C(0), E(4), G(7)
        info = parse_chord_name("C")
        self.assertEqual(chord_pitch_classes(info), frozenset({0, 4, 7}))
        
        # Am: A(9), C(0), E(4)
        info = parse_chord_name("Am")
        self.assertEqual(chord_pitch_classes(info), frozenset({9, 0, 4}))
        
        # C#7: C#(1), F(5), G#(8), B(11)
        info = parse_chord_name("C#7")
        self.assertEqual(chord_pitch_classes(info), frozenset({1, 5, 8, 11}))

        # G/B: G(7), B(11), D(2) with bass B(11) -> frozenset({7, 11, 2})
        info = parse_chord_name("G/B")
        self.assertEqual(chord_pitch_classes(info), frozenset({7, 11, 2}))

    def test_match_chord(self):
        # Match OK
        match = match_chord("C", [60, 64, 67])  # C4, E4, G4
        self.assertEqual(match.status, "ok")
        self.assertEqual(match.score, 1.0)
        
        # Partial (missing G)
        match = match_chord("C", [60, 64])  # C4, E4
        self.assertEqual(match.status, "partial")
        self.assertLess(match.score, 1.0)
        self.assertIn(7, match.missing)
        
        # Mismatch
        match = match_chord("C", [61, 65, 68])  # C#4, F4, G#4
        self.assertEqual(match.status, "mismatch")

    def test_chord_to_roman(self):
        # Key: C Major
        self.assertEqual(chord_to_roman("C", "C"), "I")
        self.assertEqual(chord_to_roman("Am7", "C"), "VIm7")
        self.assertEqual(chord_to_roman("G", "C"), "V")
        self.assertEqual(chord_to_roman("F", "C"), "IV")
        
        # Key: A Major
        self.assertEqual(chord_to_roman("A", "A"), "I")
        self.assertEqual(chord_to_roman("C#m", "A"), "IIIm")
        self.assertEqual(chord_to_roman("D", "A"), "IV")
        self.assertEqual(chord_to_roman("E", "A"), "V")
        self.assertEqual(chord_to_roman("F#m", "A"), "VIm")
        self.assertEqual(chord_to_roman("Bm", "A"), "IIm")

        # Key: Am (Natural Minor)
        self.assertEqual(chord_to_roman("Am", "Am"), "Im")
        self.assertEqual(chord_to_roman("C", "Am"), "bIII")
        self.assertEqual(chord_to_roman("Dm", "Am"), "IVm")
        self.assertEqual(chord_to_roman("Em", "Am"), "Vm")
        self.assertEqual(chord_to_roman("G", "Am"), "bVII")

    def test_infer_chord_name(self):
        # {0, 4, 7} -> C
        self.assertEqual(infer_chord_name([60, 64, 67]), "C")
        # {9, 0, 4} -> Am
        self.assertEqual(infer_chord_name([57, 60, 64]), "Am")

if __name__ == "__main__":
    unittest.main()

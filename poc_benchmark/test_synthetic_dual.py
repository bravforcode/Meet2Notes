import tempfile
import unittest
from pathlib import Path

import numpy as np
from benchmark import term_checks
from synthetic_dual import RATE, generate, mix_tracks


class SyntheticMixerTests(unittest.TestCase):
    def test_both_simulated_speakers_survive_separate_time_windows(self):
        first = np.array([10000, -8000] * 100, dtype="<i2")
        second = np.array([-6000, 4000] * 200, dtype="<i2")
        mixed, a, b, regions = mix_tracks([first, second])
        left_start, left_end = regions[0]
        right_start, right_end = regions[1]
        np.testing.assert_array_equal(mixed[left_start:left_end], first // 2)
        np.testing.assert_array_equal(mixed[right_start:right_end], second // 2)
        self.assertFalse(np.any(b[left_start:left_end]))
        self.assertFalse(np.any(a[right_start:right_end]))
        self.assertEqual(right_start - left_end, RATE // 2)

    def test_literal_term_checks_keep_thai_and_english_explicit(self):
        self.assertEqual(
            term_checks(["report", "วันศุกร์", "email"], "ส่ง REPORT วันศุกร์"),
            {"report": True, "วันศุกร์": True, "email": False},
        )

    def test_generator_refuses_existing_output_before_network_or_audio(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(FileExistsError):
            generate(Path(directory))


if __name__ == "__main__":
    unittest.main()

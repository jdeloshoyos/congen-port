"""Headless tests for the windowed auto-scale computation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from congen2.config import Config, compute_windowed_scale  # noqa: E402


class WindowedScaleTests(unittest.TestCase):
    def test_known_resolutions(self):
        self.assertEqual(compute_windowed_scale(2880, 1800), 8)
        self.assertEqual(compute_windowed_scale(1920, 1080), 4)
        self.assertEqual(compute_windowed_scale(1366, 768), 3)
        self.assertEqual(compute_windowed_scale(3840, 2160), 10)

    def test_clamps_to_one(self):
        self.assertEqual(compute_windowed_scale(320, 200), 1)
        self.assertEqual(compute_windowed_scale(100, 100), 1)
        self.assertEqual(compute_windowed_scale(0, 0), 1)

    def test_margins_reduce_scale(self):
        # Without margins the raw fit would be larger.
        self.assertGreater(compute_windowed_scale(1920, 1080, 0, 0),
                           compute_windowed_scale(1920, 1080))

    def test_auto_scale_default_on(self):
        self.assertTrue(Config().auto_scale)


if __name__ == "__main__":
    unittest.main()

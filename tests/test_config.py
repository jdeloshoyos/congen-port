"""Headless tests for persistent user settings (no pyglet needed)."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ["CONGEN2_USER_DIR"] = tempfile.mkdtemp(prefix="congen2-tests-")

from congen2.config import Config  # noqa: E402


class ConfigTests(unittest.TestCase):
    def test_default_difficulty_is_normal(self):
        self.assertEqual(Config().difficulty, "normal")

    def test_roundtrip(self):
        cfg = Config(difficulty="easy", music_on=True, sfx_on=False)
        cfg.save()
        loaded = Config.load()
        self.assertEqual(loaded.difficulty, "easy")
        self.assertTrue(loaded.music_on)
        self.assertFalse(loaded.sfx_on)

    def test_known_keys(self):
        self.assertEqual(set(Config().bindings), {
            "up", "down", "left", "right", "fire", "missile",
            "pause", "enter", "escape",
        })


if __name__ == "__main__":
    unittest.main()

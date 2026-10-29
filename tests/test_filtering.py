"""Headless regression test: textures must be point-sampled (nearest)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pyglet  # noqa: E402
from pyglet import gl  # noqa: E402

import congen2.assets  # noqa: F401,E402  (sets the texture filter defaults)


class FilteringTests(unittest.TestCase):
    def test_nearest_neighbour_defaults(self):
        # pyglet's sprite path binds textures by id without re-applying the
        # sampler, so the class defaults must be nearest for crisp pixels.
        self.assertEqual(pyglet.image.Texture.default_min_filter, gl.GL_NEAREST)
        self.assertEqual(pyglet.image.Texture.default_mag_filter, gl.GL_NEAREST)


if __name__ == "__main__":
    unittest.main()

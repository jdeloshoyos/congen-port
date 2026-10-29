"""Headless tests for the PCX -> RGBA-PNG asset conversion (no pyglet needed)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from congen2.dataformats import decode_pcx  # noqa: E402
from congen2.png import (decode_rgba_png, encode_rgba_png,  # noqa: E402
                         pcx_to_rgba, silhouette_rgba)

DATA = ROOT / "data"
LEGACY = ROOT / "legacy_app" / "Cg2data"


class PngCodecTests(unittest.TestCase):
    def test_roundtrip(self):
        rgba = bytes((255, 0, 0, 255, 0, 255, 0, 255,
                      0, 0, 255, 0, 255, 255, 255, 255))
        w, h, back = decode_rgba_png(encode_rgba_png(2, 2, rgba))
        self.assertEqual((w, h), (2, 2))
        self.assertEqual(back, rgba)


class ConversionTests(unittest.TestCase):
    def test_palette_pal_matches_nave(self):
        nave = decode_pcx((LEGACY / "nave.pcx").read_bytes())
        self.assertEqual((DATA / "palette.pal").read_bytes(), nave.palette)

    def test_all_png_match_pcx(self):
        for pcx in sorted(LEGACY.glob("*.pcx")):
            img = decode_pcx(pcx.read_bytes())
            expected = pcx_to_rgba(img.indices, img.palette)
            w, h, actual = decode_rgba_png(
                (DATA / (pcx.stem + ".png")).read_bytes())
            self.assertEqual((w, h), (img.width, img.height), pcx.name)
            self.assertEqual(actual, expected, pcx.name)

    def test_nave_sil_is_white_mask(self):
        nave = decode_pcx((LEGACY / "nave.pcx").read_bytes())
        w, h, actual = decode_rgba_png((DATA / "nave_sil.png").read_bytes())
        self.assertEqual((w, h), (nave.width, nave.height))
        self.assertEqual(actual, silhouette_rgba(nave.indices))

    def test_cmp_tileset_names(self):
        self.assertEqual((DATA / "MAPA1.CMP").read_bytes()[:12], b"tileset1.png")
        self.assertEqual((DATA / "MAPA2.CMP").read_bytes()[:12], b"tileset2.png")

    def test_expected_files_present(self):
        for n in (1, 2):
            self.assertTrue((DATA / f"MAPA{n}.CMP").exists())
            self.assertTrue((DATA / f"Mapa{n}.dat").exists())
            self.assertTrue((DATA / f"tileset{n}.png").exists())
            self.assertTrue((DATA / f"boss{n}.png").exists())
            self.assertTrue((DATA / f"boss{n}wk.png").exists())
        self.assertTrue((DATA / "HITECH.FNT").exists())
        self.assertTrue((DATA / "CANCION1.WAV").exists())


if __name__ == "__main__":
    unittest.main()

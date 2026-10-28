"""Headless tests for the asset/data decoders (no pyglet/display needed)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from congen2 import dataformats as df  # noqa: E402

DATA = ROOT / "legacy_app" / "Cg2data"


class PcxTests(unittest.TestCase):
    def test_ship_size_and_shared_palette(self):
        img = df.load_pcx(str(DATA / "nave.pcx"))
        self.assertEqual((img.width, img.height), (32, 32))
        self.assertEqual(len(img.palette), 768)
        self.assertEqual(tuple(img.palette[0:3]), (0, 0, 0))

    def test_rle_roundtrip_pixels(self):
        img = df.load_pcx(str(DATA / "tileset1.pcx"))
        self.assertEqual((img.width, img.height), (320, 64))
        self.assertEqual(len(img.indices), 320 * 64)
        self.assertTrue(all(0 <= v <= 255 for v in img.indices[:100]))

    def test_all_pcx_decode(self):
        for p in DATA.glob("*.pcx"):
            img = df.load_pcx(str(p))
            self.assertEqual(len(img.indices), img.width * img.height, p.name)


class FontTests(unittest.TestCase):
    def test_glyph_count_and_A(self):
        font = df.load_fnt(str(DATA / "HITECH.FNT"))
        self.assertEqual(len(font.glyphs), 256)
        self.assertEqual(font.rows("A"), bytes.fromhex("7c6464fee6e6e600"))

    def test_space_is_blank(self):
        font = df.load_fnt(str(DATA / "HITECH.FNT"))
        self.assertEqual(font.rows(" "), b"\x00" * 8)


class MapTests(unittest.TestCase):
    def test_map1(self):
        m = df.load_cmp(str(DATA / "MAPA1.CMP"))
        self.assertEqual(m.tileset, "tileset1.pcx")
        self.assertEqual(m.height, 400)
        self.assertEqual(len(m.rows[0]), 10)
        self.assertTrue(all(0 <= t <= 19 for row in m.rows for t in row))

    def test_map2_tileset(self):
        m = df.load_cmp(str(DATA / "MAPA2.CMP"))
        self.assertEqual(m.tileset, "tileset2.pcx")


class EventTests(unittest.TestCase):
    def test_line_parsing(self):
        ev = df.parse_event_line("250_1M_94_-31")
        self.assertEqual((ev.frame, ev.kind, ev.buff, ev.x, ev.y),
                         (250, "1", "M", 94, -31))

    def test_text_event_with_spaces(self):
        ev = df.parse_event_line("2700_TCuidado por atras!!!_96_96")
        self.assertEqual(ev.kind, "T")
        self.assertEqual(ev.buff, "Cuidado por atras!!!")
        self.assertEqual((ev.x, ev.y), (96, 96))

    def test_map1_events(self):
        e = df.load_dat(str(DATA / "Mapa1.dat"))
        self.assertEqual(e.boss, "boss1")
        self.assertEqual(e.boss_health, 60)
        self.assertEqual(e.events[0].kind, "T")
        self.assertEqual(e.events[-1].kind, "F")
        self.assertEqual(e.events[-1].frame, 2850)

    def test_map2_events(self):
        e = df.load_dat(str(DATA / "Mapa2.dat"))
        self.assertEqual(e.boss, "boss2")
        self.assertEqual(e.boss_health, 70)
        self.assertEqual(e.events[-1].frame, 2100)


class SaveTests(unittest.TestCase):
    def test_decode(self):
        s = df.decode_savegame("  0 \n  1 \n")
        self.assertEqual((s.max_score, s.max_level_reached), (0, 1))

    def test_roundtrip(self):
        s = df.SaveGame(12345, 2)
        self.assertEqual(df.decode_savegame(df.encode_savegame(s)), s)


class AngleTests(unittest.TestCase):
    def test_cardinals(self):
        self.assertEqual(df.angle_256(0, 0, 0, -10), 0)       # up
        self.assertEqual(df.angle_256(0, 0, 10, 0), 64)       # right
        self.assertEqual(df.angle_256(0, 0, 0, 10), 128)      # down
        self.assertEqual(df.angle_256(0, 0, -10, 0), 192)     # left


if __name__ == "__main__":
    unittest.main()

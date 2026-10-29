"""Headless tests for the ICO generation and nearest-neighbour scaling."""

from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from congen2.png import encode_ico, nearest_scale  # noqa: E402


class NearestScaleTests(unittest.TestCase):
    def test_solid_block_is_replicated(self):
        rgba = bytes((10, 20, 30, 255))
        out = nearest_scale(rgba, 1, 1, 4, 4)
        self.assertEqual(out, rgba * 16)

    def test_downscale_picks_source_pixels(self):
        # 2x1: red, green -> 1x1 picks the first (left) pixel
        rgba = bytes((255, 0, 0, 255, 0, 255, 0, 255))
        out = nearest_scale(rgba, 2, 1, 1, 1)
        self.assertEqual(out, bytes((255, 0, 0, 255)))


class IcoTests(unittest.TestCase):
    def test_header_and_entries(self):
        rgba16 = bytes(16 * 16 * 4)
        rgba256 = bytes(256 * 256 * 4)
        data = encode_ico([(16, 16, rgba16), (256, 256, rgba256)])
        reserved, kind, count = struct.unpack("<HHH", data[:6])
        self.assertEqual((reserved, kind, count), (0, 1, 2))

        w, h, cc, res, planes, bits, size, offset = struct.unpack(
            "<BBBBHHII", data[6:22])
        self.assertEqual((w, h, bits), (16, 16, 32))
        self.assertGreater(size, 0)
        self.assertEqual(offset, 6 + 16 * 2)

        # 256px dimensions are stored as 0, per the ICO spec.
        w2, h2 = struct.unpack("<BB", data[22:24])
        self.assertEqual((w2, h2), (0, 0))

    def test_committed_icon_is_valid(self):
        icon = ROOT / "icon.ico"
        self.assertTrue(icon.exists(), "icon.ico should be committed")
        data = icon.read_bytes()
        _, kind, count = struct.unpack("<HHH", data[:6])
        self.assertEqual(kind, 1)
        self.assertGreaterEqual(count, 1)
        # all declared image payloads fit inside the file
        offset = 6
        for _ in range(count):
            _, _, _, _, _, _, size, data_off = struct.unpack(
                "<BBBBHHII", data[offset:offset + 16])
            offset += 16
            self.assertLessEqual(data_off + size, len(data))


if __name__ == "__main__":
    unittest.main()

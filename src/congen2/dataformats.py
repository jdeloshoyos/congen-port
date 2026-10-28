"""Pure decoders for the original CG2DATA formats.

No pyglet / display dependency: everything here is testable headlessly.

Formats (see specs/02-asset-formats.md):
  * PCX  -- 8-bit, single-plane, RLE, trailing 256-colour palette
  * FNT  -- 256 glyphs x 8 bytes, 8x8 monochrome (MSB = left pixel)
  * CMP  -- 12-byte tileset name + 4000 tile bytes (tile_index = byte - 35)
  * DAT  -- boss name / boss health / event lines "FRAME_KINDBUFF_X_Y"
  * savegame.dat -- two integer lines
"""

from __future__ import annotations

import os
import struct
from dataclasses import dataclass, field
from typing import Iterator

# ---------------------------------------------------------------------------
# PCX
# ---------------------------------------------------------------------------


@dataclass
class Image:
    """A decoded 8-bit indexed image plus its palette."""

    width: int
    height: int
    indices: bytes            # len == width * height
    palette: bytes            # 768 bytes RGB

    def pixel(self, x: int, y: int) -> int:
        return self.indices[y * self.width + x]

    def rgba(self, transparent_zero: bool = True) -> bytes:
        """Convert to RGBA bytes (row-major, top-down)."""
        pal = self.palette
        out = bytearray(self.width * self.height * 4)
        for i, idx in enumerate(self.indices):
            a = 0 if (transparent_zero and idx == 0) else 255
            j = i * 4
            out[j] = pal[idx * 3]
            out[j + 1] = pal[idx * 3 + 1]
            out[j + 2] = pal[idx * 3 + 2]
            out[j + 3] = a
        return bytes(out)


def decode_pcx(data: bytes) -> Image:
    """Decode an 8-bit single-plane PCX image."""
    if len(data) < 128 or data[0] != 0x0A:
        raise ValueError("not a PCX image")
    if data[2] != 1:
        raise ValueError("only RLE-encoded PCX is supported")
    if data[3] != 8 or data[65] != 1:
        raise ValueError("only 8-bit single-plane PCX is supported")

    xmin, ymin, xmax, ymax = struct.unpack_from("<HHHH", data, 4)
    width = xmax - xmin + 1
    height = ymax - ymin + 1
    bytes_per_line = struct.unpack_from("<H", data, 66)[0]

    total = bytes_per_line * height
    raw = bytearray(total)
    pos = 128
    written = 0
    n = len(data)
    while written < total and pos < n:
        b = data[pos]
        pos += 1
        if (b & 0xC0) == 0xC0:
            run = b & 0x3F
            if pos >= n:
                break
            val = data[pos]
            pos += 1
            for _ in range(run):
                if written < total:
                    raw[written] = val
                    written += 1
        else:
            raw[written] = b
            written += 1

    # Strip per-scanline padding.
    indices = bytearray(width * height)
    for y in range(height):
        row = raw[y * bytes_per_line: y * bytes_per_line + width]
        indices[y * width: (y + 1) * width] = row

    palette = b""
    if len(data) >= 769 and data[-769] == 0x0C:
        palette = data[-768:]
    else:  # pragma: no cover - all shipped PCX files carry a palette
        palette = b"\x00" * 768

    return Image(width, height, bytes(indices), palette)


def load_pcx(path: str) -> Image:
    with open(path, "rb") as fh:
        return decode_pcx(fh.read())


# ---------------------------------------------------------------------------
# FNT
# ---------------------------------------------------------------------------

GLYPH_COUNT = 256
GLYPH_W = 8
GLYPH_H = 8


@dataclass
class BitmapFont:
    glyphs: list[bytes]        # 256 entries, each 8 bytes (8 rows)

    def rows(self, ch: str) -> bytes:
        code = ord(ch) & 0xFF
        return self.glyphs[code]


def decode_fnt(data: bytes) -> BitmapFont:
    need = GLYPH_COUNT * GLYPH_H
    if len(data) < need:
        raise ValueError("font file too short")
    glyphs = [data[i * GLYPH_H:(i + 1) * GLYPH_H] for i in range(GLYPH_COUNT)]
    return BitmapFont(glyphs)


def load_fnt(path: str) -> BitmapFont:
    with open(path, "rb") as fh:
        return decode_fnt(fh.read())


# ---------------------------------------------------------------------------
# CMP (map)
# ---------------------------------------------------------------------------

TILE_W = 32
TILE_H = 32
MAP_COLS = 10
MAP_ROWS = 400
MAP_HEADER = 12
TILE_INDEX_OFFSET = 35  # '#' == tile 0


@dataclass
class TileMap:
    tileset: str                       # e.g. "tileset1.pcx"
    # rows[y][x] -> tile index 0..19 ; len(rows) == 400, each len == 10
    rows: list[list[int]] = field(default_factory=list)

    @property
    def height(self) -> int:
        return len(self.rows)

    @property
    def width(self) -> int:
        return MAP_COLS

    def row(self, y: int) -> list[int]:
        return self.rows[y]


def decode_cmp(data: bytes) -> TileMap:
    expected = MAP_HEADER + MAP_COLS * MAP_ROWS
    if len(data) < expected:
        raise ValueError(f"CMP too short: {len(data)} < {expected}")
    tileset = data[:MAP_HEADER].decode("latin-1").rstrip("\x00 ")
    rows: list[list[int]] = []
    pos = MAP_HEADER
    for _y in range(MAP_ROWS):
        row = [data[pos + i] - TILE_INDEX_OFFSET for i in range(MAP_COLS)]
        pos += MAP_COLS
        rows.append(row)
    return TileMap(tileset=tileset, rows=rows)


def load_cmp(path: str) -> TileMap:
    with open(path, "rb") as fh:
        return decode_cmp(fh.read())


def load_tileset(path: str) -> Image:
    """Load a 320x64 tileset PCX (2 rows x 10 cols of 32x32)."""
    img = load_pcx(path)
    if img.width != TILE_W * 10 or img.height != TILE_H * 2:
        raise ValueError(f"unexpected tileset size {img.width}x{img.height}")
    return img


# ---------------------------------------------------------------------------
# DAT (events)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Event:
    frame: int
    kind: str        # '1'..'9', 'T', 'F'
    buff: str        # power-up letter or text
    x: int
    y: int


@dataclass
class EventFile:
    boss: str
    boss_health: int
    events: list[Event]

    def __iter__(self) -> Iterator[Event]:
        return iter(self.events)


def parse_event_line(line: str) -> Event:
    """Parse ``FRAME_KINDBUFF_X_Y``.

    Kind is the single character after the first underscore.  Buff is
    everything between the character after that and the second underscore,
    which is why text events can contain spaces (but not underscores).
    """
    first = line.index("_")
    frame = int(line[:first])
    kind = line[first + 1]
    second = line.index("_", first + 1)
    buff = line[first + 2: second]
    third = line.index("_", second + 1)
    x = int(line[second + 1: third])
    y = int(line[third + 1:])
    return Event(frame, kind, buff, x, y)


def decode_dat(text: str) -> EventFile:
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    if len(lines) < 2:
        raise ValueError("event file needs boss name and health")
    boss = lines[0].strip()
    boss_health = int(lines[1])
    events: list[Event] = []
    for line in lines[2:]:
        ev = parse_event_line(line)
        events.append(ev)
        if ev.kind == "F":          # original EXIT DO after boss event
            break
    return EventFile(boss=boss, boss_health=boss_health, events=events)


def load_dat(path: str) -> EventFile:
    with open(path, "r", encoding="latin-1") as fh:
        return decode_dat(fh.read())


# ---------------------------------------------------------------------------
# savegame.dat
# ---------------------------------------------------------------------------


@dataclass
class SaveGame:
    max_score: int = 0
    max_level_reached: int = 1


def decode_savegame(text: str) -> SaveGame:
    parts = [p for p in text.replace("\n", " ").split() if p]
    score = int(parts[0]) if len(parts) > 0 else 0
    level = int(parts[1]) if len(parts) > 1 else 1
    return SaveGame(max_score=score, max_level_reached=level)


def load_savegame(path: str) -> SaveGame:
    try:
        with open(path, "r", encoding="latin-1") as fh:
            return decode_savegame(fh.read())
    except (OSError, ValueError):
        return SaveGame()


def encode_savegame(save: SaveGame) -> str:
    return f"{save.max_score}\n{save.max_level_reached}\n"


def save_savegame(path: str, save: SaveGame) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="latin-1", newline="\n") as fh:
        fh.write(encode_savegame(save))


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


def angle_256(x1: float, y1: float, x2: float, y2: float) -> int:
    """DirectQB ``DQBangle`` equivalent: 0..255 clockwise from up."""
    import math

    dx = x2 - x1
    dy = y2 - y1
    ang = math.atan2(dx, -dy) * 256.0 / (2.0 * math.pi)
    return int(ang) & 0xFF

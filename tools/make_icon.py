"""Generate ``icon.ico`` from the ship sprite (nearest-neighbour, multi-size)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from congen2.png import decode_rgba_png, encode_ico, nearest_scale  # noqa: E402

ICON_SIZES = (16, 32, 48, 64, 128, 256)


def build_icon(dest: Path | None = None) -> Path:
    src = ROOT / "data" / "nave.png"
    w, h, rgba = decode_rgba_png(src.read_bytes())
    images = [(s, s, nearest_scale(rgba, w, h, s, s)) for s in ICON_SIZES]
    dest = dest or (ROOT / "icon.ico")
    dest.write_bytes(encode_ico(images))
    return dest


if __name__ == "__main__":
    print("wrote", build_icon())

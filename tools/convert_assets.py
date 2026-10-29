"""One-time asset converter: legacy_app/Cg2data -> data/ (RGBA PNG + copies).

Converts every PCX to a true-colour RGBA PNG (index 0 -> transparent), copies
audio/font/maps/events unchanged, rewrites the .cmp tileset filename to the
.png extension, and emits `palette.pal` (the original 256-colour palette, used
for text / after-image tinting) plus `nave_sil.png` (white mask for the ship
after-image).

Usage:
    uv run python tools/convert_assets.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from congen2.dataformats import decode_pcx  # noqa: E402
from congen2.png import (encode_rgba_png, pcx_to_rgba,  # noqa: E402
                         silhouette_rgba)

LEGACY = ROOT / "legacy_app" / "Cg2data"
OUT = ROOT / "data"

# Files copied verbatim (everything that isn't PCX, except savegame.dat).
COPY_VERBATIM = [
    "CANCION1.WAV",
    "Disparo.wav",
    "Disparo2.wav",
    "Disparo3.wav",
    "Explo.wav",
    "FINJEFE.WAV",
    "Golpe.wav",
    "Muerte.wav",
    "Pausa.wav",
    "Powerup.wav",
    "RocketL.wav",
    "Salud.wav",
    "Texto.wav",
    "menu.wav",
    "misil.wav",
    "HITECH.FNT",
    "Mapa1.dat",
    "Mapa2.dat",
]


def rewrite_cmp(src: Path, dst: Path) -> None:
    data = src.read_bytes()
    old = data[:12].decode("latin-1").rstrip("\x00 ")
    new = old.replace(".pcx", ".png")
    assert len(new) <= 12, f"tileset name too long: {new!r}"
    name = new.encode("latin-1").ljust(12, b"\x00")
    dst.write_bytes(name + data[12:])


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    converted = 0

    for pcx in sorted(LEGACY.glob("*.pcx")):
        img = decode_pcx(pcx.read_bytes())
        rgba = pcx_to_rgba(img.indices, img.palette)
        (OUT / (pcx.stem + ".png")).write_bytes(
            encode_rgba_png(img.width, img.height, rgba))
        converted += 1

    # Shared palette for text / after-image tinting.
    nave = decode_pcx((LEGACY / "nave.pcx").read_bytes())
    (OUT / "palette.pal").write_bytes(nave.palette)

    # White mask for the ship after-image.
    mask = silhouette_rgba(nave.indices)
    (OUT / "nave_sil.png").write_bytes(
        encode_rgba_png(nave.width, nave.height, mask))

    for name in COPY_VERBATIM:
        shutil.copy2(LEGACY / name, OUT / name)

    for cmp in sorted(LEGACY.glob("*.cmp")):
        rewrite_cmp(cmp, OUT / cmp.name)

    print(f"converted {converted} PCX -> PNG, wrote palette.pal + nave_sil.png")
    print(f"copied {len(COPY_VERBATIM)} audio/font/event files, rewrote .cmp tileset names")
    print(f"output: {OUT}")


if __name__ == "__main__":
    main()

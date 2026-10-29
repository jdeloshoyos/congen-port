"""Build a standalone onedir distribution of Congeneration 2 with PyInstaller.

Usage:
    uv run python tools/build.py

Produces ``dist/Congen2/`` containing ``Congen2.exe`` and an ``_internal/``
folder with the Python runtime, pyglet, and the bundled ``data/`` directory.
Distribute that folder (zipped) as-is.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from congen2.png import decode_rgba_png, encode_ico, nearest_scale  # noqa: E402

ICON_SIZES = (16, 32, 48, 64, 128, 256)


def ensure_icon() -> Path:
    """Use an existing icon.ico, or generate one from the ship sprite."""
    icon = ROOT / "icon.ico"
    if icon.exists():
        return icon
    w, h, rgba = decode_rgba_png((ROOT / "data" / "nave.png").read_bytes())
    images = [(s, s, nearest_scale(rgba, w, h, s, s)) for s in ICON_SIZES]
    icon.write_bytes(encode_ico(images))
    print("generated", icon)
    return icon


def main() -> None:
    icon = ensure_icon()
    data = ROOT / "data"
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean",
        "--onedir", "--windowed",
        "--name", "Congen2",
        "--icon", str(icon),
        "--add-data", f"{data}{os.pathsep}data",
        "--paths", str(ROOT / "src"),
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build"),
        "--specpath", str(ROOT / "build"),
        str(ROOT / "entry.py"),
    ]
    print("running:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("built:", ROOT / "dist" / "Congen2" / "Congen2.exe")


if __name__ == "__main__":
    main()

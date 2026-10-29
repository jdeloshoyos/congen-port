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
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from congen2 import __version__  # noqa: E402
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


def write_version_file(version: str, dest: Path) -> Path:
    """Write a PyInstaller VSVersionInfo resource for the executable."""
    parts = [int(p) for p in version.split(".")[:3]]
    while len(parts) < 3:
        parts.append(0)
    filevers = f"({parts[0]}, {parts[1]}, {parts[2]}, 0)"
    dest.write_text(
        f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={filevers},
    prodvers={filevers},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', 'Congeneration 2'),
         StringStruct('FileDescription', 'Congeneration 2'),
         StringStruct('FileVersion', '{version}'),
         StringStruct('InternalName', 'Congen2'),
         StringStruct('OriginalFilename', 'Congen2.exe'),
         StringStruct('ProductName', 'Congeneration 2'),
         StringStruct('ProductVersion', '{version}')])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
""",
        encoding="utf-8",
    )
    return dest


def main() -> None:
    icon = ensure_icon()
    data = ROOT / "data"
    with tempfile.TemporaryDirectory(prefix="congen2-build-") as td:
        version_file = write_version_file(__version__, Path(td) / "version_info.txt")
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--noconfirm", "--clean",
            "--onedir", "--windowed",
            "--name", "Congen2",
            "--icon", str(icon),
            "--version-file", str(version_file),
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

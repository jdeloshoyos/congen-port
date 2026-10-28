"""Asset loading: PCX -> textures, FNT -> glyph textures, WAV -> sources.

Must be constructed *after* a pyglet window/GL context exists.
"""

from __future__ import annotations

from pathlib import Path

import pyglet
from pyglet import gl

from . import dataformats as df
from .config import data_dir

# Sound id -> filename (original load order, 1..14)
SOUND_FILES = {
    1: "disparo.wav",
    2: "explo.wav",
    3: "golpe.wav",
    4: "muerte.wav",
    5: "pausa.wav",
    6: "texto.wav",
    7: "disparo2.wav",
    8: "disparo3.wav",
    9: "powerup.wav",
    10: "salud.wav",
    11: "finjefe.wav",
    12: "misil.wav",
    13: "rocketl.wav",
    14: "menu.wav",
}
MUSIC_FILE = "CANCION1.WAV"


def _rgba(img: df.Image, x: int, y: int, w: int, h: int,
          silhouette: bool = False) -> bytes:
    """Crop (top-left based) and convert to RGBA, flipping vertically because
    pyglet's ImageData treats the first row as the bottom of the texture."""
    pal = img.palette
    out = bytearray(w * h * 4)
    for row in range(h):
        src_y = y + row
        dst_row = h - 1 - row
        base = dst_row * w * 4
        for col in range(w):
            idx = img.indices[src_y * img.width + x + col]
            j = base + col * 4
            if idx == 0:
                # alpha stays 0
                continue
            if silhouette:
                out[j] = out[j + 1] = out[j + 2] = 255
            else:
                p = idx * 3
                out[j] = pal[p]
                out[j + 1] = pal[p + 1]
                out[j + 2] = pal[p + 2]
            out[j + 3] = 255
    return bytes(out)


class Assets:
    def __init__(self, directory: Path | None = None):
        self.dir = Path(directory) if directory else data_dir()
        if not self.dir.is_dir():
            raise FileNotFoundError(
                f"CG2 data directory not found: {self.dir}\n"
                f"Run from the project root or pass --data <path>."
            )
        self.images: dict[str, df.Image] = {}
        self.textures: dict[str, pyglet.image.Texture] = {}
        self._image_data: list[pyglet.image.ImageData] = []   # keep alive
        self._glyph_tex: dict[int, pyglet.image.Texture] = {}
        self.sounds: dict[int, pyglet.media.Source] = {}
        self.music: pyglet.media.Source | None = None

        self.palette = df.load_pcx(str(self.dir / "nave.pcx")).palette
        self.font = df.load_fnt(str(self.dir / "HITECH.FNT"))
        self._load_sprites()
        self._load_tilesets()
        self._load_backgrounds()
        self._load_sounds()

    # -- palette ---------------------------------------------------------

    def rgb(self, index: int) -> tuple[int, int, int]:
        i = (index & 0xFF) * 3
        return self.palette[i], self.palette[i + 1], self.palette[i + 2]

    # -- texture helpers -------------------------------------------------

    def _make_tex(self, w: int, h: int, data: bytes) -> pyglet.image.Texture:
        im = pyglet.image.ImageData(w, h, "RGBA", data, pitch=w * 4)
        self._image_data.append(im)
        tex = im.get_texture()
        tex.min_filter = gl.GL_NEAREST
        tex.mag_filter = gl.GL_NEAREST
        # Sprites are positioned by their centre so rotation/mirroring match
        # DirectQB's centre-anchored puts.
        tex.anchor_x = w // 2
        tex.anchor_y = h // 2
        return tex

    def _add_sheet(self, key: str, filename: str, *, frame_w: int,
                   frame_h: int, cols: int, rows: int = 1,
                   silhouette: bool = False) -> list[str]:
        img = df.load_pcx(str(self.dir / filename))
        self.images[key] = img
        names: list[str] = []
        for r in range(rows):
            for c in range(cols):
                name = f"{key}_{r * cols + c}" if rows * cols > 1 else key
                data = _rgba(img, c * frame_w, r * frame_h, frame_w, frame_h,
                             silhouette=silhouette)
                self.textures[name] = self._make_tex(frame_w, frame_h, data)
                names.append(name)
        return names

    def _add_full(self, key: str, filename: str, silhouette: bool = False) -> None:
        img = df.load_pcx(str(self.dir / filename))
        self.images[key] = img
        data = _rgba(img, 0, 0, img.width, img.height, silhouette=silhouette)
        self.textures[key] = self._make_tex(img.width, img.height, data)

    # -- sprite sheets ---------------------------------------------------

    def _load_sprites(self) -> None:
        self._add_sheet("ship0", "nave.pcx", frame_w=32, frame_h=32, cols=1)
        self._add_sheet("ship1", "nave2.pcx", frame_w=32, frame_h=32, cols=1)
        self._add_sheet("ship2", "nave3.pcx", frame_w=32, frame_h=32, cols=1)
        for i, f in enumerate(("disparo.pcx", "disparo2.pcx", "disparo3.pcx")):
            self._add_sheet(f"shot{i}", f, frame_w=32, frame_h=32, cols=1)
        self._add_sheet("powerup", "powerup.pcx", frame_w=32, frame_h=32, cols=1)
        self._add_sheet("health", "salud.pcx", frame_w=32, frame_h=32, cols=1)
        self._add_sheet("missilebox", "Misilbox.pcx", frame_w=32, frame_h=32, cols=1)
        self._add_sheet("missile", "Misil.pcx", frame_w=32, frame_h=32, cols=1)

        # Silhouettes for the after-image effect (3 ship frames).
        for i, f in enumerate(("nave.pcx", "nave2.pcx", "nave3.pcx")):
            img = df.load_pcx(str(self.dir / f))
            data = _rgba(img, 0, 0, 32, 32, silhouette=True)
            self.textures[f"ship{i}_sil"] = self._make_tex(32, 32, data)

        self._add_sheet("expl", "explo.pcx", frame_w=32, frame_h=32, cols=6)
        self._add_sheet("hit", "hit.pcx", frame_w=32, frame_h=32, cols=2)
        self._add_sheet("debris", "debris.pcx", frame_w=8, frame_h=8, cols=8)

        self._add_sheet("malo1", "malo1.pcx", frame_w=32, frame_h=32, cols=2)
        self._add_sheet("malo2", "malo2.pcx", frame_w=32, frame_h=32, cols=3)
        self._add_sheet("malo3", "malo3.pcx", frame_w=32, frame_h=32, cols=2)
        self._add_sheet("mina", "mina.pcx", frame_w=32, frame_h=32, cols=1)
        self._add_sheet("malo4", "malo4.pcx", frame_w=32, frame_h=32, cols=2)
        self._add_sheet("malo5", "malo5.pcx", frame_w=32, frame_h=32, cols=1)

        for n in (1, 2):
            self._add_sheet(f"bossA{n}", f"boss{n}.pcx", frame_w=32, frame_h=32,
                            cols=3, rows=2)
            self._add_sheet(f"bossW{n}", f"boss{n}wk.pcx", frame_w=32, frame_h=32,
                            cols=3, rows=2)

    def _load_tilesets(self) -> None:
        for n in (1, 2):
            self._add_sheet(f"ts{n}", f"tileset{n}.pcx", frame_w=32, frame_h=32,
                            cols=10, rows=2)

    def _load_backgrounds(self) -> None:
        self._add_full("menu1", "menu1.pcx")
        self._add_full("menu2", "menu2.pcx")
        self._add_full("menu3", "menu3.pcx")
        self._add_full("menu4", "menu4.pcx")
        self._add_full("final", "final.pcx")

    # -- font ------------------------------------------------------------

    def glyph(self, ch: str) -> pyglet.image.Texture:
        code = ord(ch) & 0xFF
        tex = self._glyph_tex.get(code)
        if tex is None:
            rows = self.font.glyphs[code]
            data = bytearray(8 * 8 * 4)
            for y in range(8):
                bits = rows[y]
                dst_row = 7 - y
                base = dst_row * 8 * 4
                for x in range(8):
                    if (bits >> (7 - x)) & 1:
                        j = base + x * 4
                        data[j] = data[j + 1] = data[j + 2] = 255
                        data[j + 3] = 255
            tex = self._make_tex(8, 8, bytes(data))
            self._glyph_tex[code] = tex
        return tex

    # -- sound -----------------------------------------------------------

    def _load_sounds(self) -> None:
        for sid, fname in SOUND_FILES.items():
            p = self.dir / fname
            try:
                self.sounds[sid] = pyglet.media.load(str(p), streaming=False)
            except Exception:
                pass
        try:
            self.music = pyglet.media.load(str(self.dir / MUSIC_FILE),
                                           streaming=False)
        except Exception:
            self.music = None

    # -- lookup ----------------------------------------------------------

    def tex(self, name: str) -> pyglet.image.Texture:
        return self.textures[name]

    def has(self, name: str) -> bool:
        return name in self.textures

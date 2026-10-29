"""Asset loading: PNG -> textures, FNT -> glyph textures, WAV -> sources.

Graphics are true-colour RGBA PNGs (converted from the original PCX art; index
0 is transparent).  The original 256-colour palette is kept in ``palette.pal``
and used only for tinting the HUD/menu text and the ship's after-image.

Must be constructed *after* a pyglet window/GL context exists.
"""

from __future__ import annotations

from pathlib import Path

import pyglet
from pyglet import gl

from . import dataformats as df
from .config import data_dir

# pyglet's sprite path binds textures by id and never re-applies the sampler
# filter, so a per-texture ``mag_filter`` assignment never reaches OpenGL.
# Setting the class defaults (used by ``Texture.create``) before any texture
# is created makes every texture point-sampled: crisp, square pixels rather
# than bilinear blur.
pyglet.image.Texture.default_min_filter = gl.GL_NEAREST
pyglet.image.Texture.default_mag_filter = gl.GL_NEAREST

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


class Assets:
    def __init__(self, directory: Path | None = None):
        self.dir = Path(directory) if directory else data_dir()
        if not self.dir.is_dir():
            raise FileNotFoundError(
                f"CG2 data directory not found: {self.dir}\n"
                f"Run from the project root or pass --data <path>."
            )
        self.textures: dict[str, pyglet.image.Texture] = {}
        self._glyph_tex: dict[int, pyglet.image.Texture] = {}
        self.sounds: dict[int, pyglet.media.Source] = {}
        self.music: pyglet.media.Source | None = None

        self.palette = (self.dir / "palette.pal").read_bytes()
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

    def _finalize(self, img: pyglet.image.AbstractImage) -> pyglet.image.Texture:
        # Filtering is set globally via ``Texture.default_*_filter`` above.
        tex = img.get_texture()
        tex.anchor_x = img.width // 2
        tex.anchor_y = img.height // 2
        return tex

    def _add_sheet(self, key: str, filename: str, *, frame_w: int,
                   frame_h: int, cols: int, rows: int = 1) -> list[str]:
        img = pyglet.image.load(str(self.dir / filename))
        names: list[str] = []
        for r in range(rows):
            # pyglet's get_region uses a bottom-up y origin, so invert the row.
            src_y = (rows - 1 - r) * frame_h
            for c in range(cols):
                name = f"{key}_{r * cols + c}" if rows * cols > 1 else key
                region = img.get_region(c * frame_w, src_y, frame_w, frame_h)
                self.textures[name] = self._finalize(region)
                names.append(name)
        return names

    def _add_full(self, key: str, filename: str) -> None:
        img = pyglet.image.load(str(self.dir / filename))
        self.textures[key] = self._finalize(img)

    # -- sprite sheets ---------------------------------------------------

    def _load_sprites(self) -> None:
        self._add_sheet("ship0", "nave.png", frame_w=32, frame_h=32, cols=1)
        self._add_sheet("ship1", "nave2.png", frame_w=32, frame_h=32, cols=1)
        self._add_sheet("ship2", "nave3.png", frame_w=32, frame_h=32, cols=1)
        self._add_full("ship0_sil", "nave_sil.png")
        for i, f in enumerate(("disparo.png", "disparo2.png", "disparo3.png")):
            self._add_sheet(f"shot{i}", f, frame_w=32, frame_h=32, cols=1)
        self._add_sheet("powerup", "powerup.png", frame_w=32, frame_h=32, cols=1)
        self._add_sheet("health", "salud.png", frame_w=32, frame_h=32, cols=1)
        self._add_sheet("missilebox", "Misilbox.png", frame_w=32, frame_h=32, cols=1)
        self._add_sheet("missile", "Misil.png", frame_w=32, frame_h=32, cols=1)

        self._add_sheet("expl", "explo.png", frame_w=32, frame_h=32, cols=6)
        self._add_sheet("hit", "hit.png", frame_w=32, frame_h=32, cols=2)
        self._add_sheet("debris", "debris.png", frame_w=8, frame_h=8, cols=8)

        self._add_sheet("malo1", "malo1.png", frame_w=32, frame_h=32, cols=2)
        self._add_sheet("malo2", "malo2.png", frame_w=32, frame_h=32, cols=3)
        self._add_sheet("malo3", "malo3.png", frame_w=32, frame_h=32, cols=2)
        self._add_sheet("mina", "mina.png", frame_w=32, frame_h=32, cols=1)
        self._add_sheet("malo4", "malo4.png", frame_w=32, frame_h=32, cols=2)
        self._add_sheet("malo5", "malo5.png", frame_w=32, frame_h=32, cols=1)

        for n in (1, 2):
            self._add_sheet(f"bossA{n}", f"boss{n}.png", frame_w=32, frame_h=32,
                            cols=3, rows=2)
            self._add_sheet(f"bossW{n}", f"boss{n}wk.png", frame_w=32, frame_h=32,
                            cols=3, rows=2)

    def _load_tilesets(self) -> None:
        for n in (1, 2):
            self._add_sheet(f"ts{n}", f"tileset{n}.png", frame_w=32, frame_h=32,
                            cols=10, rows=2)

    def _load_backgrounds(self) -> None:
        self._add_full("menu1", "menu1.png")
        self._add_full("menu2", "menu2.png")
        self._add_full("menu3", "menu3.png")
        self._add_full("menu4", "menu4.png")
        self._add_full("final", "final.png")

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
            im = pyglet.image.ImageData(8, 8, "RGBA", bytes(data), pitch=8 * 4)
            tex = self._finalize(im)
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

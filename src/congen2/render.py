"""Drawing layer: turns world/menu state into pyglet sprites.

Sprites are pooled per (layer, texture) so that after warm-up no vertex lists
are recreated and no texture swaps happen during the frame.
"""

from __future__ import annotations

import random
from typing import Optional

import pyglet
from pyglet import gl

from . import __version__
from . import constants as C
from .assets import Assets
from .dataformats import MAP_COLS

# Layer (draw-order) constants.
L_BG = 0
L_AFTER = 1
L_PLAYER = 2
L_DEBRIS = 3
L_MISSILE = 4
L_ENEMY = 5
L_SPARK = 6
L_PSHOT = 7
L_ESHOT = 8
L_HUD = 9

L_MENU_PANEL = 20
L_MENU_LABEL = 21
L_MENU_TITLE = 22
L_MENU_CURSOR = 23
L_MENU_TOP = 24

L_CREDITS_BG = 20
L_CREDITS_TEXT = 21

L_PAUSE_DIM = 30
L_PAUSE_TEXT = 31


def _angle_deg(ang: int) -> float:
    return ang * 360.0 / 256.0


def _qstr(n: int) -> str:
    """QuickBasic STR$: non-negative numbers get a leading space."""
    return f" {n}" if n >= 0 else f"{n}"


class _Pool:
    __slots__ = ("batch", "group", "tex", "sprites", "n")

    def __init__(self, batch, group, tex):
        self.batch = batch
        self.group = group
        self.tex = tex
        self.sprites: list[pyglet.sprite.Sprite] = []
        self.n = 0

    def get(self) -> pyglet.sprite.Sprite:
        if self.n < len(self.sprites):
            s = self.sprites[self.n]
        else:
            s = pyglet.sprite.Sprite(self.tex, batch=self.batch,
                                     group=self.group, subpixel=True)
            self.sprites.append(s)
        self.n += 1
        s.visible = True
        return s

    def finish(self) -> None:
        for s in self.sprites[self.n:]:
            if s.visible:
                s.visible = False
        self.n = 0


class Renderer:
    def __init__(self, assets: Assets):
        self.assets = assets
        self.batch = pyglet.graphics.Batch()
        self._groups: dict[int, pyglet.graphics.Group] = {}
        self._pools: dict[tuple, _Pool] = {}
        # Integer presentation scale / letterbox offsets, set by the app.
        self.view_scale = 1
        self.ox = 0
        self.oy = 0
        # Preserve exact palette colours; no texture tinting by default.
        self.pixel = "pixel"
        self._make_pixel()

    def set_viewport(self, scale: int, ox: int, oy: int) -> None:
        self.view_scale = max(1, scale)
        self.ox = ox
        self.oy = oy

    def _make_pixel(self) -> None:
        data = bytes((255, 255, 255, 255))
        im = pyglet.image.ImageData(1, 1, "RGBA", data, pitch=4)
        tex = im.get_texture()
        tex.anchor_x = 0
        tex.anchor_y = 0
        self.assets.textures["pixel"] = tex
        self._pixel_img = im

    # -- primitives ------------------------------------------------------

    def _group(self, order: int) -> pyglet.graphics.Group:
        g = self._groups.get(order)
        if g is None:
            g = pyglet.graphics.Group(order)
            self._groups[order] = g
        return g

    def _pool(self, layer: int, key, tex) -> _Pool:
        k = (layer, key)
        p = self._pools.get(k)
        if p is None:
            p = _Pool(self.batch, self._group(layer), tex)
            self._pools[k] = p
        return p

    def sprite(self, layer: int, texname: str, left: float, top: float,
               *, angle: float = 0.0, scale: float = 1.0,
               scale_x: float = 1.0, scale_y: float = 1.0,
               tint: Optional[tuple[int, int, int]] = None,
               alpha: int = 255) -> None:
        tex = self.assets.tex(texname)
        s = self._pool(layer, texname, tex).get()
        w, h = tex.width, tex.height
        sc = self.view_scale
        # Snap to the logical pixel grid so adjacent tiles/sections never show
        # sub-pixel seams.
        cx = round(left + w / 2.0)
        cy = round(top + h / 2.0)
        s.x = self.ox + cx * sc
        s.y = self.oy + (C.SCREEN_H - cy) * sc
        s.rotation = angle
        s.scale = sc * scale
        s.scale_x = scale_x
        s.scale_y = scale_y
        s.color = tint if tint is not None else (255, 255, 255)
        s.opacity = alpha

    def text(self, layer: int, s: str, x: float, y: float,
             color_index: int) -> None:
        tint = self.assets.rgb(color_index)
        sc = self.view_scale
        for i, ch in enumerate(s):
            if ch == " ":
                continue
            tex = self.assets.glyph(ch)
            sp = self._pool(layer, ("font", ord(ch)), tex).get()
            sp.x = self.ox + (x + i * 8 + 4) * sc
            sp.y = self.oy + (C.SCREEN_H - (y + 4)) * sc
            sp.rotation = 0.0
            sp.scale = sc
            sp.scale_x = 1.0
            sp.scale_y = 1.0
            sp.color = tint
            sp.opacity = 255

    def rect(self, layer: int, left: float, top: float, w: float, h: float,
             color: tuple[int, int, int], alpha: int = 255) -> None:
        tex = self.assets.tex(self.pixel)
        s = self._pool(layer, self.pixel, tex).get()
        sc = self.view_scale
        s.x = self.ox + round(left) * sc
        s.y = self.oy + (C.SCREEN_H - round(top + h)) * sc
        s.rotation = 0.0
        s.scale = 1.0
        s.scale_x = w * sc
        s.scale_y = h * sc
        s.color = color
        s.opacity = alpha

    # -- frame lifecycle -------------------------------------------------

    def clear(self) -> None:
        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    def flush(self) -> None:
        for p in self._pools.values():
            p.finish()
        self.batch.draw()

    # -- world -----------------------------------------------------------

    def draw_world(self, world, alpha: float) -> None:
        self._draw_background(world, alpha)
        self.player_ref = world.player

        def lerp(a: float, b: float) -> float:
            return a + (b - a) * alpha

        art = self._level_art(world)

        # Player + after-image.
        p = world.player
        if p.deathflag < 300:
            if world.curframe % 2 == 0:
                self.sprite(
                    L_AFTER, "ship0_sil",
                    lerp(p.px, p.x) - (lerp(p.px, p.x) - 160) * 0.2,
                    lerp(p.py, p.y) - (lerp(p.py, p.y) - 100) * 0.2,
                    tint=self.assets.rgb(C.COL_AFTERIMAGE),
                )
            frame = p.turnflag
            mirrored = False
            if frame == 0:
                texname = "ship0"
            elif frame == 1:
                texname = "ship1"
            elif frame == 2:
                texname = "ship2"
            else:
                texname = "ship2"
                mirrored = True
            self.sprite(L_PLAYER, texname, lerp(p.px, p.x), lerp(p.py, p.y),
                        scale_x=-1.0 if mirrored else 1.0)

        # Debris / particles.
        for d in world.debris:
            self._draw_debris(d, lerp(d.px, d.x), lerp(d.py, d.y))

        # Missiles.
        for m in world.missiles:
            if m.owner > -1 and self._on_screen(lerp(m.px, m.x), lerp(m.py, m.y), 32, 32):
                self.sprite(L_MISSILE, "missile", lerp(m.px, m.x), lerp(m.py, m.y),
                            angle=_angle_deg(m.ang))

        # Enemies (including power-ups and boss sections).
        for e in world.enemies:
            if e.kind != 0:
                self._draw_enemy(e, lerp(e.px, e.x), lerp(e.py, e.y), world.curframe, art)

        # Player shots.
        for s in world.pshots:
            if s.x > -32:
                self.sprite(L_PSHOT, f"shot{s.cls}", lerp(s.px, s.x), lerp(s.py, s.y))

        # Enemy shots.
        for s in world.eshots:
            if not (s.x == -10 and s.y == 0):
                self.sprite(L_ESHOT, "debris_6", lerp(s.px, s.x), lerp(s.py, s.y),
                            angle=_angle_deg(s.ang))

        # Impact sparks (one-frame flashes).
        for (sx, sy) in world.sparks:
            for _ in range(3):
                dx = sx + random.randint(-8, 8)
                dy = sy + random.randint(-8, 8)
                self.rect(L_SPARK, dx, dy, random.choice((2, 3, 4)),
                          random.choice((2, 3, 4)), (255, 255, 255))

        self._draw_hud(world)
        if world.text_ticks > 0 and world.text:
            self.text(L_HUD, world.text, world.text_x, world.text_y, C.COL_TEXT_EVENT)

        if world.fade_active:
            dim = min(255, int(255 * world.fade_counter / 100))
            self.rect(L_PAUSE_DIM, 0, 0, C.SCREEN_W, C.SCREEN_H, (0, 0, 0), dim)

    def _level_art(self, world) -> dict:
        ts = "ts1" if "1" in world.tilemap.tileset else "ts2"
        boss = "1" if "1" in world.events.boss else "2"
        return {"ts": ts, "bossA": f"bossA{boss}", "bossW": f"bossW{boss}"}

    def _on_screen(self, x: float, y: float, w: int, h: int) -> bool:
        return not (x + w <= 0 or x >= C.SCREEN_W or y + h <= 0 or y >= C.SCREEN_H)

    def _draw_background(self, world, alpha: float) -> None:
        rows = world.tilemap.rows
        ts = self._level_art(world)["ts"]
        if world.curframe == 0:
            for i in range(8):
                row = rows[i + 392]
                for x in range(MAP_COLS):
                    self.sprite(L_BG, f"{ts}_{row[x]}", x * 32, i * 32)
            return
        n = world.curframe - 1
        mappos = ((392 - (n // 32) - 1) % 392) + 1
        scrollpos = -31 + (n % 32)
        k = 0
        while True:
            y = scrollpos + 32 * k
            if y >= C.SCREEN_H:
                break
            mrow = mappos + k
            if mrow > 400:
                break
            row = rows[mrow - 1]
            for x in range(MAP_COLS):
                self.sprite(L_BG, f"{ts}_{row[x]}", x * 32, y)
            k += 1

    def _draw_debris(self, d, x: float, y: float) -> None:
        u = d.userflag
        if u < C.DEBRIS_EXPLOSION_END:
            if self._on_screen(x, y, 32, 32):
                self.sprite(L_DEBRIS, f"expl_{min(u // 3, 5)}", x, y)
        elif C.DEBRIS_SHARD_START <= u < C.DEBRIS_SHARD_END:
            if self._on_screen(x, y, 8, 8):
                self.sprite(L_DEBRIS, f"debris_{(u - 20) // 3 + 3}", x, y)
        elif C.DEBRIS_TRAIL_START <= u < C.DEBRIS_TRAIL_END:
            if self._on_screen(x, y, 8, 8):
                self.sprite(L_DEBRIS, f"debris_{(u - 30) // 9}", x, y)
        elif C.DEBRIS_SPARK_START <= u < C.DEBRIS_SPARK_END:
            if self._on_screen(x, y, 32, 32):
                if u in (60, 61):
                    self.sprite(L_DEBRIS, "hit_0", x, y)
                elif u in (62, 63):
                    self.sprite(L_DEBRIS, "hit_1", x, y)
                elif u in (64, 65):
                    self.sprite(L_DEBRIS, "hit_0", x, y, scale_x=-1.0)
                else:
                    self.sprite(L_DEBRIS, "hit_1", x, y, scale_x=-1.0)
        elif C.DEBRIS_GUNTRAIL_START <= u < C.DEBRIS_GUNTRAIL_END:
            if self._on_screen(x, y, 8, 8):
                self.sprite(L_DEBRIS, "debris_7", x, y)

    def _draw_enemy(self, e, x: float, y: float, curframe: int, art: dict) -> None:
        k = e.kind
        if not self._on_screen(x, y, 32, 32):
            return
        if k == 1:
            self.sprite(L_ENEMY, f"malo1_{e.userflag & 1}", x, y)
        elif k == 2:
            f = min(e.userflag // 5, 2)
            self.sprite(L_ENEMY, f"malo2_{f}", x, y)
        elif k == 3:
            if e.userflag in (0, 1):
                self.sprite(L_ENEMY, f"malo3_{e.userflag}", x, y)
            else:
                self.sprite(L_ENEMY, f"malo3_{e.userflag - 2}", x, y, scale_x=-1.0)
        elif k == 4:
            self.sprite(L_ENEMY, f"malo1_{e.userflag & 1}", x, y, scale_y=-1.0)
        elif k == 5:
            ang = _angle_deg(self._angle_to_player(e))
            self.sprite(L_ENEMY, "mina", x, y, angle=ang)
        elif k == 6:
            frame = 0 if curframe % 2 == 1 else 1
            self.sprite(L_ENEMY, f"malo4_{frame}", x, y, angle=_angle_deg(e.userflag & 0xFF))
        elif k == 7:
            self.sprite(L_ENEMY, "malo5", x, y, angle=_angle_deg(e.userflag & 0xFF))
        elif k == 100:
            self._draw_powerup("powerup", e, x, y)
        elif k == 101:
            self._draw_powerup("health", e, x, y)
        elif k == 102:
            self._draw_powerup("missilebox", e, x, y)
        elif 10 <= k <= 21:
            idx = k - 10
            key = art["bossW"] if idx >= 6 else art["bossA"]
            self.sprite(L_ENEMY, f"{key}_{idx % 6}", x, y)

    def _angle_to_player(self, e) -> int:
        p = self.player_ref
        from .dataformats import angle_256
        return angle_256(e.x, e.y, p.x, p.y)

    def _draw_powerup(self, texname: str, e, x: float, y: float) -> None:
        u = max(25, min(40, e.userflag))
        # Centre-anchored scaling already reproduces the original's fixed-centre
        # pulse, so no top-left compensation offset is applied here.
        scale = u / 32.0
        self.sprite(L_ENEMY, texname, x, y, scale=scale)

    def _draw_hud(self, world) -> None:
        p = world.player
        y = 10
        self.text(L_HUD, "Energia P" + _qstr(1) + " :", 10, y, C.COL_HUD_MAIN)
        self.text(L_HUD, _qstr(p.health) + "%", 100, y, C.COL_HUD_HEALTH)
        self.text(L_HUD, _qstr(p.score), 200, y, C.COL_HUD_SCORE)
        self.text(L_HUD, "Arma Nivel" + _qstr(p.gunlevel + 1), 10, y + 8, C.COL_HUD_WEAPON)
        self.text(L_HUD, "Misiles :" + _qstr(p.ammo), 208, y + 8, C.COL_HUD_WEAPON)
        if world.noharm != 0 or p.invencible == 1:
            self.text(L_HUD, "ESCUDO", 140, y, C.COL_HUD_SHIELD)

    # -- menus -----------------------------------------------------------

    def _draw_version(self, layer: int) -> None:
        """Right-aligned version label in the bottom-right corner."""
        s = f"v{__version__}"
        x = C.SCREEN_W - 8 * len(s) - 2
        self.text(layer, s, x, C.SCREEN_H - 8, C.COL_MENU_TEXT)

    def draw_menu(self, menuopt: int, mapnumber: int, maxscore: int,
                  cursorframe: int) -> None:
        panel = f"menu{menuopt + 1}"
        self.sprite(L_MENU_PANEL, panel, 0, 0)
        self.text(L_MENU_LABEL, C.MENU_OPTIONS[0], 180, 60, C.COL_MENU_TEXT)
        self.text(L_MENU_LABEL, C.MENU_OPTIONS[1], 180, 100, C.COL_MENU_TEXT)
        self.text(L_MENU_LABEL, C.MENU_OPTIONS[2], 180, 140, C.COL_MENU_TEXT)
        self.text(L_MENU_LABEL, "Maximo puntaje:", 10, 191, C.COL_MENU_SCORE_LABEL)
        self.text(L_MENU_LABEL, _qstr(maxscore), 120, 191, C.COL_MENU_SCORE_VALUE)
        # Title art overlays the panel, colour 0 already transparent.
        self.sprite(L_MENU_TITLE, "menu1", 0, 0)
        # Animated cursor reuses an enemy sprite, as in the original.
        f = min(cursorframe // 5, 2)
        self.sprite(L_MENU_CURSOR, f"malo2_{f}", 140, (menuopt - 1) * 40 + 48)
        self.text(L_MENU_TOP, _qstr(mapnumber), 180, 108, C.COL_MENU_LEVEL)
        self.text(L_MENU_TOP, "Maximo puntaje:", 10, 191, C.COL_MENU_SCORE_LABEL)
        self._draw_version(L_MENU_TOP)

    def draw_controls(self, cfg, cursor: int, awaiting: str | None) -> None:
        self.rect(L_PAUSE_DIM, 0, 0, C.SCREEN_W, C.SCREEN_H, (0, 0, 0), 180)
        self.text(L_PAUSE_TEXT, "CONTROLES", 100, 20, 255)
        actions = list(cfg.bindings.keys())
        for i, action in enumerate(actions):
            col = 60 if i == cursor and awaiting is None else 125
            self.text(L_PAUSE_TEXT, f"{action:<12}{cfg.bindings[action]}",
                      20, 45 + i * 12, col)
        if awaiting is not None:
            self.text(L_PAUSE_TEXT, f"Presione tecla para {awaiting}...", 20, 175, 60)
        else:
            self.text(L_PAUSE_TEXT, "ENTER cambiar  ESC volver", 20, 175, 60)

    def draw_credits(self) -> None:
        self.sprite(L_CREDITS_BG, "final", 0, 0)
        lines = [
            ("CONGENERATION 2", 20, 10, 50),
            ("Desarrollado usando las librerias DirectQB", 20, 30, 125),
            ("creadas por Angelo Mottola.", 20, 40, 125),
            ("Programacion : Jaime de los Hoyos M.", 20, 60, 125),
            ("Arte : Vicente de los Hoyos M.", 20, 70, 125),
            ("Agradecimientos a :", 20, 80, 125),
            ("Francisca de los Hoyos M.", 20, 90, 125),
            ("jhoyos@entelchile.net", 20, 110, 125),
            ("Presione ENTER para seguir.", 20, 150, 50),
        ]
        for text, x, y, col in lines:
            self.text(L_CREDITS_TEXT, text, x, y, col)

    def draw_pause(self, cfg, cursor: int) -> None:
        self.rect(L_PAUSE_DIM, 0, 0, C.SCREEN_W, C.SCREEN_H, (0, 0, 0), 170)
        self.text(L_PAUSE_TEXT, "PAUSA", 140, 30, 255)
        opts = [
            "Continuar",
            f"Musica: {'SI' if cfg.music_on else 'NO'}",
            f"Sonido: {'SI' if cfg.sfx_on else 'NO'}",
            "Dificultad: " + C.DIFFICULTY_LABELS.get(cfg.difficulty, "NORMAL"),
            "Controles",
            "Salir al menu",
        ]
        for i, opt in enumerate(opts):
            col = 60 if i == cursor else 125
            self.text(L_PAUSE_TEXT, opt, 110, 70 + i * 16, col)
        self._draw_version(L_PAUSE_TEXT)

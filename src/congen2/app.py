"""Main application: window, fixed-timestep loop, state machine, input."""

from __future__ import annotations

from pathlib import Path

import pyglet
from pyglet import display
from pyglet.window import key

from . import constants as C
from .assets import Assets
from .audio import Audio
from .config import (Config, compute_windowed_scale, data_dir, load_save,
                     persist_save)
from .dataformats import SaveGame, load_cmp, load_dat
from .render import Renderer
from .world import Controls, Player, World

MENU = "menu"
LEVEL = "level"
CREDITS = "credits"


def _primary_screen():
    """Return the primary screen, or None when no display is available."""
    try:
        screens = display.get_display().get_screens()
        return screens[0] if screens else None
    except Exception:
        return None


class App(pyglet.window.Window):
    def __init__(self, data_directory: str | Path | None = None,
                 scale: int | None = None,
                 auto_scale: bool | None = None):
        self.cfg = Config.load()
        if scale is not None:
            self.cfg.auto_scale = False
            self.cfg.scale = max(1, int(scale))
            self.cfg.save()
        elif auto_scale:
            self.cfg.auto_scale = True
            self.cfg.save()

        self._primary = _primary_screen()
        win_scale = self._windowed_scale()
        w = C.SCREEN_W * win_scale
        h = C.SCREEN_H * win_scale
        super().__init__(width=w, height=h, caption="Congeneration 2",
                         resizable=True, vsync=True)
        self.set_minimum_size(C.SCREEN_W // 2, C.SCREEN_H // 2)

        self.data_dir = Path(data_directory) if data_directory else data_dir()
        self.assets = Assets(self.data_dir)
        self.renderer = Renderer(self.assets)
        self.audio = Audio(self.assets, self.cfg)
        self.save: SaveGame = load_save()

        self.max_level = self._count_levels()
        self.state = MENU
        self.menuopt = 1
        self.mapnumber = max(1, min(self.save.max_level_reached, self.max_level))
        self.keydelay = 0
        self.cursorframe = 0

        self.world: World | None = None
        self.paused = False
        self.pause_cursor = 0
        self.controls_mode = False
        self.controls_cursor = 0
        self.awaiting_key: str | None = None

        self.acc = 0.0
        self.alpha = 0.0
        self.keys: set[int] = set()
        self.press_queue: list[int] = []
        self._resolve_bindings()

        if self.cfg.fullscreen:
            self.set_fullscreen(True)
        else:
            self._center_on_screen()
        self._layout()
        self.audio.refresh_music()
        pyglet.clock.schedule_interval(self._advance, 1 / 240.0)

    # -- bindings --------------------------------------------------------

    def _resolve_bindings(self) -> None:
        self.binding: dict[str, int | None] = {}
        for action, name in self.cfg.bindings.items():
            self.binding[action] = getattr(key, name, None)

    def _controls(self) -> Controls:
        def down(action: str) -> bool:
            sym = self.binding.get(action)
            return sym is not None and sym in self.keys

        return Controls(
            up=down("up"), down=down("down"),
            left=down("left"), right=down("right"),
            fire=down("fire"), missile=down("missile"),
            f1=key.F1 in self.keys, f2=key.F2 in self.keys,
            f3=key.F3 in self.keys, f4=key.F4 in self.keys,
            f5=key.F5 in self.keys,
        )

    # -- data files ------------------------------------------------------

    def _find(self, name: str) -> Path | None:
        direct = self.data_dir / name
        if direct.exists():
            return direct
        low = name.lower()
        try:
            for f in self.data_dir.iterdir():
                if f.name.lower() == low:
                    return f
        except OSError:
            pass
        return None

    def _count_levels(self) -> int:
        n = 1
        while self._find(f"mapa{n}.cmp") and self._find(f"mapa{n}.dat"):
            n += 1
        return max(1, n - 1)

    def _clamp_mapnumber(self) -> None:
        if self.mapnumber < 1:
            self.mapnumber = 1
        if self.mapnumber > self.max_level:
            self.mapnumber = self.max_level
        if self.mapnumber > self.save.max_level_reached:
            self.mapnumber = self.save.max_level_reached

    # -- level lifecycle -------------------------------------------------

    def _start_level(self, n: int, carry: Player | None = None) -> None:
        cmp_path = self._find(f"mapa{n}.cmp")
        dat_path = self._find(f"mapa{n}.dat")
        if cmp_path is None or dat_path is None:
            self.state = MENU
            self.world = None
            return
        tilemap = load_cmp(str(cmp_path))
        events = load_dat(str(dat_path))
        player = self._carry_player(carry) if carry is not None else Player()
        fire_chance = C.FIRE_CHANCES.get(self.cfg.difficulty,
                                         C.ENEMY_FIRE_CHANCE)
        self.world = World(tilemap, events, events.boss_health, player,
                           fire_chance=fire_chance)
        self.state = LEVEL
        self.paused = False
        self.controls_mode = False
        self.awaiting_key = None
        self.acc = 0.0

    @staticmethod
    def _carry_player(p: Player) -> Player:
        return Player(
            x=C.PLAYER_START_X, y=C.PLAYER_START_Y,
            vel_x=C.PLAYER_VEL_X, vel_y=C.PLAYER_VEL_Y,
            turnflag=0, shotdelay=0,
            health=p.health, deathflag=0, score=p.score,
            gunlevel=p.gunlevel, invencible=0, ammo=p.ammo,
            px=C.PLAYER_START_X, py=C.PLAYER_START_Y,
        )

    def _finish_level(self) -> None:
        assert self.world is not None
        p = self.world.player
        if p.score > self.save.max_score:
            self.save.max_score = p.score

        if not self.world.level_passed:
            persist_save(self.save)
            self._to_menu()
            return

        nxt = self.mapnumber + 1
        if self._find(f"mapa{nxt}.cmp") and self._find(f"mapa{nxt}.dat"):
            self.mapnumber = nxt
            if nxt > self.save.max_level_reached:
                self.save.max_level_reached = nxt
            persist_save(self.save)
            self._start_level(nxt, carry=p)
        else:
            self.save.max_level_reached = max(self.save.max_level_reached, self.mapnumber)
            persist_save(self.save)
            self.state = CREDITS
            self.world = None

    def _abandon_level(self) -> None:
        if self.world is not None:
            if self.world.player.score > self.save.max_score:
                self.save.max_score = self.world.player.score
        persist_save(self.save)
        self._to_menu()

    def _to_menu(self) -> None:
        self.state = MENU
        self.world = None
        self.paused = False
        self.controls_mode = False
        self.awaiting_key = None
        self.menuopt = 1
        self.keydelay = 0
        self.mapnumber = max(1, min(self.mapnumber, self.max_level,
                                    self.save.max_level_reached))

    # -- main loop -------------------------------------------------------

    def _advance(self, dt: float) -> None:
        self.acc += dt
        steps = 0
        while self.acc >= C.TICK_DT and steps < 5:
            self._step()
            self.acc -= C.TICK_DT
            steps += 1
        if self.acc > C.TICK_DT * 5:
            self.acc = 0.0
        self.alpha = min(1.0, self.acc / C.TICK_DT)
        self.audio.update()

    def _step(self) -> None:
        edges = set(self.press_queue)
        self.press_queue.clear()
        if self.state == MENU:
            self._step_menu(edges)
        elif self.state == LEVEL:
            self._step_level(edges)
        elif self.state == CREDITS:
            if key.ENTER in edges:
                self.state = MENU
                self.menuopt = 1
                self.keydelay = 0

    # -- menu ------------------------------------------------------------

    def _step_menu(self, edges: set[int]) -> None:
        nav = (key.UP, key.DOWN, key.LEFT, key.RIGHT)
        if any(k in self.keys for k in nav):
            if self.keydelay > 0:
                self.keydelay -= 1
        else:
            self.keydelay = 0

        if self.keydelay == 0:
            if key.UP in self.keys:
                self.menuopt -= 1
                if self.menuopt == 0:
                    self.menuopt = 3
                self.keydelay = C.MAX_KEY_DELAY
                self.audio.play(C.SND_MENU)
            elif key.DOWN in self.keys:
                self.menuopt += 1
                if self.menuopt == 4:
                    self.menuopt = 1
                self.keydelay = C.MAX_KEY_DELAY
                self.audio.play(C.SND_MENU)
            elif key.LEFT in self.keys and self.menuopt == 2:
                self.mapnumber -= 1
                self._clamp_mapnumber()
                self.keydelay = C.MAX_KEY_DELAY
                self.audio.play(C.SND_MENU)
            elif key.RIGHT in self.keys and self.menuopt == 2:
                self.mapnumber += 1
                self._clamp_mapnumber()
                self.keydelay = C.MAX_KEY_DELAY
                self.audio.play(C.SND_MENU)

        if key.ENTER in edges:
            if self.menuopt == 1:
                self.audio.play(C.SND_MENU)
                self._start_level(self.mapnumber)
            elif self.menuopt == 3:
                self._quit()

        self.cursorframe = (self.cursorframe + 1) % 15

    # -- level -----------------------------------------------------------

    def _step_level(self, edges: set[int]) -> None:
        if self.paused:
            self._step_pause(edges)
            return

        pause_key = self.binding.get("pause")
        if pause_key is not None and pause_key in edges:
            self.paused = True
            self.pause_cursor = 0
            self.controls_mode = False
            self.awaiting_key = None
            self.audio.play(C.SND_PAUSE)
            return
        if key.ESCAPE in edges:
            self._abandon_level()
            return

        assert self.world is not None
        self.world.tick(self._controls())
        self.audio.play_all(self.world.sounds)
        if self.world.exit:
            self._finish_level()

    # -- pause -----------------------------------------------------------

    def _step_pause(self, edges: set[int]) -> None:
        if self.controls_mode:
            self._step_controls(edges)
            return

        if key.ESCAPE in edges:
            self._abandon_level()
            return
        pause_key = self.binding.get("pause")
        if pause_key is not None and pause_key in edges:
            self.paused = False
            return

        if key.UP in edges:
            self.pause_cursor = (self.pause_cursor - 1) % 6
        elif key.DOWN in edges:
            self.pause_cursor = (self.pause_cursor + 1) % 6
        elif key.LEFT in edges:
            if self.pause_cursor == 3:
                self._cycle_difficulty(-1)
            else:
                self._activate_pause()
        elif key.RIGHT in edges:
            if self.pause_cursor == 3:
                self._cycle_difficulty(1)
            else:
                self._activate_pause()
        elif key.ENTER in edges:
            self._activate_pause()

    def _activate_pause(self) -> None:
        if self.pause_cursor == 0:
            self.paused = False
        elif self.pause_cursor == 1:
            self._toggle_music()
        elif self.pause_cursor == 2:
            self._toggle_sfx()
        elif self.pause_cursor == 3:
            self._cycle_difficulty(1)
        elif self.pause_cursor == 4:
            self.controls_mode = True
            self.controls_cursor = 0
        else:
            self._abandon_level()

    def _cycle_difficulty(self, delta: int) -> None:
        order = list(C.DIFFICULTY_ORDER)
        try:
            i = order.index(self.cfg.difficulty)
        except ValueError:
            i = order.index("normal")
        self.cfg.difficulty = order[(i + delta) % len(order)]
        self.cfg.save()
        if self.world is not None:
            self.world.fire_chance = C.FIRE_CHANCES[self.cfg.difficulty]

    def _step_controls(self, edges: set[int]) -> None:
        actions = list(self.cfg.bindings.keys())
        if self.awaiting_key is not None:
            if key.ESCAPE in edges:
                self.awaiting_key = None
                return
            if edges:
                sym = next(iter(edges))
                self.cfg.bindings[self.awaiting_key] = key.symbol_string(sym)
                self.awaiting_key = None
                self._resolve_bindings()
                self.cfg.save()
            return
        if key.ESCAPE in edges:
            self.controls_mode = False
            self.cfg.save()
            return
        if key.UP in edges:
            self.controls_cursor = (self.controls_cursor - 1) % len(actions)
        elif key.DOWN in edges:
            self.controls_cursor = (self.controls_cursor + 1) % len(actions)
        elif key.ENTER in edges:
            self.awaiting_key = actions[self.controls_cursor]

    # -- toggles ---------------------------------------------------------

    def _toggle_music(self) -> None:
        self.cfg.music_on = not self.cfg.music_on
        self.audio.refresh_music()
        self.cfg.save()

    def _toggle_sfx(self) -> None:
        self.cfg.sfx_on = not self.cfg.sfx_on
        self.cfg.save()

    def _quit(self) -> None:
        persist_save(self.save)
        self.cfg.save()
        self.audio._stop_music()
        self.close()

    # -- pyglet events ---------------------------------------------------

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        self.keys.add(symbol)
        self.press_queue.append(symbol)
        if symbol == key.F11:
            self.cfg.fullscreen = not self.cfg.fullscreen
            self.set_fullscreen(self.cfg.fullscreen)
            self.cfg.save()
            self._layout()
        elif self.awaiting_key is None and symbol == key.M:
            self._toggle_music()
        elif self.awaiting_key is None and symbol == key.N:
            self._toggle_sfx()

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        self.keys.discard(symbol)

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self._layout()

    def _windowed_scale(self) -> int:
        """Integer scale for the initial windowed size (auto or manual)."""
        if (self.cfg.auto_scale and not self.cfg.fullscreen
                and self._primary is not None):
            return compute_windowed_scale(self._primary.width,
                                          self._primary.height)
        return max(1, self.cfg.scale)

    def _center_on_screen(self) -> None:
        if self._primary is None:
            return
        s = self._primary
        self.set_location(s.x + (s.width - self.width) // 2,
                          s.y + (s.height - self.height) // 2)

    def _layout(self) -> None:
        s = min(self.width // C.SCREEN_W, self.height // C.SCREEN_H)
        s = max(1, s)
        vw, vh = C.SCREEN_W * s, C.SCREEN_H * s
        self.renderer.set_viewport(s, (self.width - vw) // 2, (self.height - vh) // 2)

    def on_draw(self) -> None:
        self._layout()
        self.renderer.clear()
        if self.state == MENU:
            self.renderer.draw_menu(self.menuopt, self.mapnumber,
                                    self.save.max_score, self.cursorframe)
        elif self.state == LEVEL and self.world is not None:
            self.renderer.draw_world(self.world, self.alpha)
            if self.paused:
                if self.controls_mode:
                    self.renderer.draw_controls(self.cfg, self.controls_cursor,
                                                self.awaiting_key)
                else:
                    self.renderer.draw_pause(self.cfg, self.pause_cursor)
        elif self.state == CREDITS:
            self.renderer.draw_credits()
        self.renderer.flush()

    def on_close(self) -> None:
        try:
            persist_save(self.save)
            self.cfg.save()
            self.audio._stop_music()
        except Exception:
            pass
        super().on_close()


def main() -> None:
    """Console-script entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Congeneration 2 (port)")
    parser.add_argument("--data", default=None,
                        help="directory containing the game data files")
    parser.add_argument("--scale", type=int, default=None,
                        help="force a fixed integer window scale "
                             "(disables automatic scaling)")
    parser.add_argument("--auto-scale", action="store_true",
                        help="re-enable automatic windowed scaling")
    args, _ = parser.parse_known_args()
    App(data_directory=args.data, scale=args.scale,
        auto_scale=args.auto_scale)
    pyglet.app.run(interval=1.0 / C.MAX_FPS)

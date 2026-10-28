"""Headless simulation tests (no pyglet/display needed)."""

from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from congen2 import constants as C  # noqa: E402
from congen2 import dataformats as df  # noqa: E402
from congen2.world import Controls, Player, World  # noqa: E402

DATA = ROOT / "legacy_app" / "Cg2data"


def make_world(level: int = 1, player: Player | None = None) -> World:
    tm = df.load_cmp(str(DATA / f"MAPA{level}.CMP"))
    ev = df.load_dat(str(DATA / f"Mapa{level}.dat"))
    return World(tm, ev, ev.boss_health, player)


class InitialStateTests(unittest.TestCase):
    def test_player_defaults(self):
        w = make_world()
        p = w.player
        self.assertEqual((p.x, p.y), (C.PLAYER_START_X, C.PLAYER_START_Y))
        self.assertEqual(p.health, 100)
        self.assertEqual(p.ammo, 5)
        self.assertEqual(p.gunlevel, 0)
        self.assertEqual(p.score, 0)

    def test_world_fields(self):
        w = make_world()
        self.assertEqual(w.curframe, 0)
        self.assertFalse(w.exit)
        self.assertFalse(w.level_passed)
        self.assertEqual(w.curframe, 0)


class PlayerActionTests(unittest.TestCase):
    def setUp(self):
        self.w = make_world()

    def test_fire_uses_gun_stats(self):
        self.w.tick(Controls(fire=True))
        shots = [s for s in self.w.pshots if s.x > -32]
        self.assertEqual(len(shots), 1)
        self.assertEqual(shots[0].vel_y, 8)
        self.assertEqual(shots[0].cls, 0)
        self.assertEqual(self.w.player.shotdelay, 10)

    def test_missile_consumes_ammo(self):
        self.w.tick(Controls(missile=True))
        self.assertEqual(self.w.player.ammo, 4)
        self.assertEqual(self.w.missile_delay, 100)
        active = [m for m in self.w.missiles if m.owner > -1]
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].lockon, 1)  # no enemies yet -> lock 1

    def test_bounds(self):
        self.w.player.x = 0
        self.w.tick(Controls(left=True))
        self.assertEqual(self.w.player.x, 0)
        self.w.player.x = C.PLAYER_RIGHT_LIMIT - 1
        self.w.tick(Controls(right=True))
        self.assertLessEqual(self.w.player.x, C.PLAYER_RIGHT_LIMIT + 3)


class EventSpawnTests(unittest.TestCase):
    def test_text_event(self):
        w = make_world()
        for _ in range(51):
            w.tick(Controls())
        self.assertEqual(w.text, "Bienvenido a Congeneration 2!!")
        self.assertGreater(w.text_ticks, 0)

    def test_enemy_spawn_and_ai1(self):
        random.seed(1)
        w = make_world()
        for _ in range(203):      # event at frame 200, then AI ticks
            w.tick(Controls())
        kinds = [e.kind for e in w.enemies]
        self.assertIn(1, kinds)
        e = next(e for e in w.enemies if e.kind == 1)
        # AI1 accelerates downwards by 0.05/tick; spawned at frame 200.
        self.assertGreater(e.vel_y, 0.0)

    def test_enemy_kind2_health(self):
        random.seed(1)
        w = make_world()
        for _ in range(601):      # first kind-2 event is at frame 600
            w.tick(Controls())
        e = next(e for e in w.enemies if e.kind == 2)
        self.assertEqual(e.health, 2)
        self.assertEqual(e.vel_y, 4.0)


class BossTests(unittest.TestCase):
    def test_boss_spawn_and_death(self):
        random.seed(2)
        w = make_world()
        w.player.invencible = 1
        # Advance to the boss patrol altitude.
        for _ in range(4000):
            w.tick(Controls())
            if any(9 < e.kind < 16 for e in w.enemies) and w.enemies[0].y <= 20:
                break
        self.assertEqual([e.kind for e in w.enemies[:6]],
                         [10, 11, 12, 13, 14, 15])
        self.assertGreaterEqual(w.enemies[0].health, 1)
        # Simulate all six sections destroyed.
        for i, e in enumerate(w.enemies[:6]):
            e.kind = 16 + i
            e.health = 1
        w.tick(Controls())
        self.assertEqual(w.enemies[0].boss_death_flag, 1)
        passed = False
        exited = False
        for _ in range(600):
            w.tick(Controls())
            passed = passed or w.level_passed
            if w.exit:
                exited = True
                break
        self.assertTrue(passed)
        self.assertTrue(exited)


class DeathTests(unittest.TestCase):
    def test_player_death_ends_level(self):
        w = make_world()
        w.player.health = 0
        for _ in range(500):
            w.tick(Controls())
        self.assertTrue(w.exit)
        self.assertFalse(w.level_passed)


class CarryOverTests(unittest.TestCase):
    def test_carry_player_stats(self):
        p = Player(health=42, score=9999, gunlevel=2, ammo=7)
        w = make_world(player=p)
        self.assertEqual(w.player.health, 42)
        self.assertEqual(w.player.score, 9999)
        self.assertEqual(w.player.gunlevel, 2)
        self.assertEqual(w.player.ammo, 7)


if __name__ == "__main__":
    unittest.main()

"""Deterministic game simulation, translated from CONGEN2.BAS.

The simulation is pure Python (no pyglet) so it can be tested headlessly.  One
call to :meth:`World.tick` advances exactly one original frame (1/50 s).

Rendering-related drawing is omitted here; the equivalent *state changes*
(sprite frame counters, power-up pulsing, debris animation) are preserved so a
renderer can reconstruct the original pictures.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional

from . import constants as C
from .dataformats import Event, EventFile, TileMap, angle_256


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------


@dataclass
class Controls:
    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False
    fire: bool = False
    missile: bool = False
    f1: bool = False       # invincibility toggle (held state; edge handled inside)
    f2: bool = False
    f3: bool = False
    f4: bool = False
    f5: bool = False


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------


@dataclass
class Player:
    x: float = C.PLAYER_START_X
    y: float = C.PLAYER_START_Y
    vel_x: float = C.PLAYER_VEL_X
    vel_y: float = C.PLAYER_VEL_Y
    turnflag: int = 0
    shotdelay: int = 0
    health: int = C.PLAYER_MAX_HEALTH
    deathflag: int = 0
    score: int = 0
    gunlevel: int = 0
    invencible: int = 0
    ammo: int = C.PLAYER_START_AMMO
    # interpolation
    px: float = C.PLAYER_START_X
    py: float = C.PLAYER_START_Y


@dataclass
class Enemy:
    x: float = -32.0
    y: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    userflag: int = 0
    health: int = 1
    kind: int = 0
    powerup: str = " "
    boss_death_flag: int = 0
    px: float = -32.0
    py: float = 0.0


@dataclass
class PShot:
    x: float = -33.0
    y: float = 100.0
    vel_y: float = 0.0
    cls: int = 0
    px: float = -33.0
    py: float = 100.0


@dataclass
class EShot:
    x: float = -10.0
    y: float = 0.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    ang: int = 0
    px: float = -10.0
    py: float = 0.0


@dataclass
class Missile:
    x: float = -33.0
    y: float = -33.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    owner: int = -1
    ang: int = 0
    lockon: int = 1
    px: float = -33.0
    py: float = -33.0


@dataclass
class Debris:
    x: float = -33.0
    y: float = 100.0
    vel_x: float = 0.0
    vel_y: float = 0.0
    userflag: int = 0
    px: float = -33.0
    py: float = 100.0


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------


class World:
    """One level's worth of simulation state."""

    def __init__(self, tilemap: TileMap, events: EventFile, boss_health: int,
                 player: Optional[Player] = None,
                 fire_chance: int = C.ENEMY_FIRE_CHANCE):
        self.tilemap = tilemap
        self.events = events
        self.boss_health = boss_health
        self.fire_chance = fire_chance

        # Carry-over state is supplied when moving to the next level.
        self.player = player if player is not None else Player()

        self.enemies = [Enemy() for _ in range(C.MAX_ENEMIES)]
        self.pshots = [PShot() for _ in range(C.MAX_PSHOTS)]
        self.eshots = [EShot() for _ in range(C.MAX_ESHOTS)]
        self.missiles = [Missile() for _ in range(C.MAX_MISSILES)]
        self.debris = [Debris() for _ in range(C.MAX_DEBRIS)]

        self.curframe = 0
        self.curevent = 0
        self.curenemy = 0
        self.cureshot = 0
        self.nextpshot = 0
        self.nextmissile = 0
        self.nextdebris = 0

        self.missile_delay = 0
        self.noharm = 0

        # per-level end state
        self.level_passed = False
        self.exit = False
        self.death_sum = 0
        self.fade_counter = 0
        self.fade_active = False

        # overlays
        self.text = ""
        self.text_x = 0
        self.text_y = 0
        self.text_ticks = 0

        # one-frame spark bursts produced by shot impacts
        self.sparks: list[tuple[float, float]] = []

        # sounds requested this tick (drained by the app)
        self.sounds: list[int] = []

    # -- helpers ---------------------------------------------------------

    def _play(self, snd: int) -> None:
        self.sounds.append(snd)

    def _add_debris(self, x: float, y: float, vx: float, vy: float,
                    userflag: int = 0) -> None:
        d = self.debris[self.nextdebris]
        d.x, d.y, d.vel_x, d.vel_y, d.userflag = x, y, vx, vy, userflag
        d.px, d.py = x, y
        self.nextdebris += 1
        if self.nextdebris >= C.MAX_DEBRIS:
            self.nextdebris = 0

    def _reset_missile(self, m: Missile) -> None:
        m.x = m.y = -33.0
        m.vel_x = m.vel_y = 0.0
        m.owner = -1
        m.ang = 0
        m.lockon = 1

    def _reset_pshot(self, s: PShot) -> None:
        s.x, s.y, s.vel_y, s.cls = -33.0, 100.0, 0.0, 0

    def _reset_eshot(self, s: EShot) -> None:
        s.x, s.y, s.vel_x, s.vel_y = -10.0, 0.0, 0.0, 0.0

    def _reset_enemy(self, e: Enemy) -> None:
        e.x, e.y = -32.0, 0.0
        e.vel_x = e.vel_y = 0.0
        e.userflag = 0
        e.health = 1
        e.kind = 0
        e.powerup = " "
        e.boss_death_flag = 0

    def _save_prev(self) -> None:
        p = self.player
        p.px, p.py = p.x, p.y
        for group in (self.enemies, self.pshots, self.eshots,
                      self.missiles, self.debris):
            for e in group:
                e.px, e.py = e.x, e.y

    # -- main tick -------------------------------------------------------

    def tick(self, ctrl: Controls) -> None:
        self.sounds.clear()
        self.sparks.clear()
        self._save_prev()

        self._update_player(ctrl)

        # Death fade (original: rn == 300 * numplayers -> fade, exit after 100)
        self.death_sum = self.player.deathflag
        if self.death_sum >= 300 * C.MAX_PLAYERS:
            self.fade_active = True
            self.fade_counter += 1
            if self.fade_counter >= 100:
                self.exit = True
                return

        self._update_debris()
        self._update_missiles()

        for t in range(C.MAX_ENEMIES):
            self._update_enemy(t)

        self._update_pshots()
        self._update_eshots()

        if self.noharm > 0:
            self.noharm -= 1

        if self.text_ticks > 0:
            self.text_ticks -= 1

        self._process_events()

        self.curframe += 1

    # -- player ----------------------------------------------------------

    def _update_player(self, ctrl: Controls) -> None:
        p = self.player

        # Ship frame animation (original draws first, then toggles; the visual
        # difference is one tick and imperceptible).
        if p.turnflag == 0:
            p.turnflag = 1
        elif p.turnflag == 1:
            p.turnflag = 0
        if p.turnflag > 1:
            p.turnflag = 0

        if p.shotdelay > 0:
            p.shotdelay -= 1

        if ctrl.up and p.y > C.PLAYER_UP_LIMIT:
            p.y -= p.vel_y
        if ctrl.down and p.y < C.PLAYER_DOWN_LIMIT:
            p.y += p.vel_y
        if ctrl.left and p.x > 0:
            p.x -= p.vel_x
            p.turnflag = 2
        if ctrl.right and p.x < C.PLAYER_RIGHT_LIMIT:
            p.x += p.vel_x
            p.turnflag = 3

        # Cheats
        if ctrl.f1 and p.invencible < 2 and p.health > 0:
            p.invencible = 2 if p.invencible == 1 else 3
        if (not ctrl.f1) and p.invencible > 1:
            p.invencible -= 2
        if ctrl.f2:
            p.gunlevel = 0
        if ctrl.f3:
            p.gunlevel = 1
        if ctrl.f4:
            p.gunlevel = 2
        if ctrl.f5:
            p.ammo = 100

        if self.missile_delay > 0:
            self.missile_delay -= 1

        # Launch a homing missile.
        if ctrl.missile and p.ammo > 0 and self.missile_delay == 0 and p.health > 0:
            p.ammo -= 1
            self.missile_delay = C.MISSILE_DELAY
            self._play(C.SND_MISSILE)
            m = self.missiles[self.nextmissile]
            m.x, m.y = p.x, p.y
            m.vel_x, m.vel_y = 0.0, -1.0
            m.owner = 0
            m.ang = 0
            m.lockon = sum(e.kind for e in self.enemies)
            if m.lockon == 0:
                m.lockon = 1
            else:
                while True:
                    cand = random.randrange(1, C.MAX_ENEMIES + 1)
                    if self.enemies[cand - 1].kind != 0:
                        m.lockon = cand
                        break
            m.px, m.py = m.x, m.y
            self.nextmissile += 1
            if self.nextmissile >= C.MAX_MISSILES:
                self.nextmissile = 0

        # Fire the main gun.
        if ctrl.fire and p.shotdelay == 0 and p.health > 0:
            s = self.pshots[self.nextpshot]
            s.x, s.y = p.x, p.y - 10
            s.px, s.py = s.x, s.y
            level = min(p.gunlevel, 2)
            s.vel_y = C.GUN_SPEEDS[level]
            s.cls = level
            self._play(C.GUN_SOUNDS[level])
            self.nextpshot += 1
            if self.nextpshot >= C.MAX_PSHOTS:
                self.nextpshot = 0
            p.shotdelay = C.SHOT_DELAY_BASE - level

        # Death handling.
        if p.health <= 0:
            p.health = 0
            if p.deathflag == 0:
                p.deathflag = 1

        if p.deathflag > 0:
            if p.deathflag < 300:
                self._add_debris(p.x + random.random() * 50 - 25,
                                 p.y + random.random() * 50 - 25,
                                 0.0, 3.0, 0)
            if p.deathflag == 299:
                self._play(C.SND_DEATH)
                for _ in range(20):
                    self._add_debris(p.x + 12, p.y + 12,
                                     random.random() * 10 - 5,
                                     random.random() * 10 - 3,
                                     int(random.random() * 9) + 20)
            p.deathflag += 1
            if p.deathflag > 300:
                p.deathflag = 300

        if p.invencible > 0:
            p.health = 100

    # -- debris ----------------------------------------------------------

    def _update_debris(self) -> None:
        for d in self.debris:
            u = d.userflag
            if u < C.DEBRIS_EXPLOSION_END:
                d.userflag = u + 1
                if d.userflag == 1 and d.x != -33:
                    if self.player.health > 0 and self.enemies[0].boss_death_flag == 0:
                        self._play(C.SND_EXPLODE)
                    elif random.randrange(10) == 0:
                        self._play(C.SND_EXPLODE)
                if d.userflag == C.DEBRIS_EXPLOSION_END:
                    self._reset_debris(d)
            elif C.DEBRIS_SHARD_START <= u < C.DEBRIS_SHARD_END:
                d.userflag = u + 1
                if d.userflag == C.DEBRIS_SHARD_END:
                    d.userflag = C.DEBRIS_SHARD_START
                if d.vel_x + d.vel_y < 0.05:
                    self._reset_debris(d)
                if d.userflag in (22, 27):
                    self._add_debris(d.x, d.y, 0.0, 1.0, C.DEBRIS_TRAIL_START)
            elif C.DEBRIS_TRAIL_START <= u < C.DEBRIS_TRAIL_END:
                d.userflag = u + 1
                if d.userflag == C.DEBRIS_TRAIL_END:
                    self._reset_debris(d)
            elif C.DEBRIS_SPARK_START <= u < C.DEBRIS_SPARK_END:
                d.userflag = u + 1
                if d.userflag == C.DEBRIS_SPARK_END:
                    self._reset_debris(d)
            elif C.DEBRIS_GUNTRAIL_START <= u < C.DEBRIS_GUNTRAIL_END:
                d.userflag = u + 1
                if d.userflag == C.DEBRIS_GUNTRAIL_END:
                    self._reset_debris(d)
            d.x += d.vel_x
            d.y += d.vel_y

    def _reset_debris(self, d: Debris) -> None:
        d.x, d.y = -33.0, 100.0
        # Keep the interpolation anchors in sync: otherwise a just-reset
        # debris is rendered at lerp(old_position, -33) for one tick, which
        # shows a stray explosion frame at a bogus on-screen position.
        d.px, d.py = -33.0, 100.0
        d.vel_x = d.vel_y = 0.0
        d.userflag = 0

    # -- missiles --------------------------------------------------------

    def _update_missiles(self) -> None:
        p = self.player
        for m in self.missiles:
            m.x += m.vel_x
            m.y += m.vel_y
            if m.owner > -1:
                if m.y < -62:
                    self._reset_missile(m)
                    continue
                if m.vel_y > -5:
                    m.vel_y -= 0.1
                target = self.enemies[m.lockon - 1]
                if target.kind != 0:
                    if m.x > target.x:
                        m.vel_x -= C.MISSILE_PRECISION
                        if m.vel_x < -C.MISSILE_MAX_X_SPEED:
                            m.vel_x = -C.MISSILE_MAX_X_SPEED
                    if m.x < target.x:
                        m.vel_x += 0.2
                        if m.vel_x > C.MISSILE_MAX_X_SPEED:
                            m.vel_x = C.MISSILE_MAX_X_SPEED
                m.ang = int(m.vel_x * 8)
                if m.ang < 0:
                    m.ang += 255
                self._add_debris(m.x + 12, m.y + 12, 0.0, 2.0,
                                 C.DEBRIS_TRAIL_START)

    # -- enemies ---------------------------------------------------------

    def _update_enemy(self, t: int) -> None:
        e = self.enemies[t]

        # Power-up pulse animation lives in the original's draw switch.
        if e.kind == 100:
            e.userflag -= 1
            if e.userflag < 25:
                e.userflag = 40
        elif e.kind in (101, 102):
            e.userflag += 1
            if e.userflag > 40:
                e.userflag = 25

        if e.kind < 10:
            self._run_ai(t, e)
        elif 9 < e.kind < 22 and t == 0:
            self._run_boss_ai()

        if e.boss_death_flag > 0:
            e.boss_death_flag += 1
        if e.boss_death_flag == C.BOSS_DEATH_EXIT_TICK:
            self.exit = True
            return

        # All six boss sections destroyed -> start the death sequence.
        if e.kind == 16:
            e2, e3, e4, e5, e6 = self.enemies[1:6]
            if (e2.kind, e3.kind, e4.kind, e5.kind, e6.kind) == (17, 18, 19, 20, 21):
                self._add_debris(e.x + random.random() * 84 - 10,
                                 e.y + random.random() * 52 - 10,
                                 0.0, -1.0, 0)
                e0 = self.enemies[0]
                e0.userflag = 3
                e0.vel_x = 0.0
                e0.vel_y = 0.2
                if e0.boss_death_flag == 0:
                    e0.boss_death_flag = 1
                if e0.boss_death_flag == C.BOSS_DEATH_PASS_TICK:
                    self._play(C.SND_BOSS_DEATH)
                    self.level_passed = True
                    for _ in range(10):
                        self._add_debris(e0.x + 44, e0.y + 28,
                                         random.random() * 10 - 5,
                                         random.random() * 10 - 3,
                                         int(random.random() * 9) + 20)
                    for i in range(6):
                        self.enemies[i].x = -32.0
                        self.enemies[i].y = 0.0
                        self.enemies[i].vel_x = 0.0
                        self.enemies[i].vel_y = 0.0
                        self.enemies[i].userflag = 0
                        self.enemies[i].health = 1
                        self.enemies[t].kind = 0

        e.x += e.vel_x
        e.y += e.vel_y

        if e.x > 321 or e.x < -33 or e.y > 201 or e.y < -33:
            if e.kind < 10 or e.kind > 15:
                self._reset_enemy(e)

        if e.health > 0:
            self._collide_player_shots(t, e)
            self._collide_missiles(t, e)

        if e.health <= 0:
            self._kill_enemy(t, e)

        self._enemy_fire(t, e)
        self._contact_player(t, e)

    def _run_ai(self, t: int, e: Enemy) -> None:
        k = e.kind
        if k == 1:      # AI1
            e.vel_y += 0.05
            e.userflag = 0 if e.userflag == 1 else 1
        elif k == 2:    # AI2
            e.vel_y -= 0.05
            e.userflag += 1
            if e.userflag == 15:
                e.userflag = 0
        elif k == 3:    # AI3
            if e.userflag in (0, 1):
                e.userflag = 1 if e.userflag == 0 else 0
            elif e.userflag in (2, 3):
                e.userflag = 3 if e.userflag == 2 else 2
        elif k == 4:    # AI4
            e.vel_y -= 0.05
            e.userflag = 0 if e.userflag == 1 else 1
        elif k == 5:    # AI5 - drifting mine
            pass
        elif k == 6:    # AI6
            e.vel_y += 0.05
            if self.curframe % 3 == 0:
                if e.vel_x > 0:
                    e.userflag += 1
                else:
                    e.userflag -= 1
        elif k == 7:    # AI7
            e.userflag -= 10
            if e.userflag < 0:
                e.userflag += 256

    def _run_boss_ai(self) -> None:
        e0 = self.enemies[0]
        if e0.y <= C.BOSS_TOP and e0.userflag == 0:
            e0.y = C.BOSS_TOP
            for e in self.enemies[:6]:
                e.vel_y = 0.0
                e.vel_x = -1.0
                e.userflag = 1
        if e0.x <= C.BOSS_LEFT and e0.userflag == 1:
            e0.x = C.BOSS_LEFT
            for e in self.enemies[:6]:
                e.vel_x = 1.0
                e.userflag = 2
        if e0.x >= C.BOSS_RIGHT and e0.userflag == 2:
            e0.x = C.BOSS_RIGHT
            for e in self.enemies[:6]:
                e.vel_x = -1.0
                e.userflag = 1
        for i in range(1, 6):
            ei = self.enemies[i]
            if 9 < ei.kind < 22:
                if i < 3:
                    ei.x = e0.x + i * 32
                    ei.y = e0.y
                else:
                    ei.x = e0.x + (i - 3) * 32
                    ei.y = e0.y + 32

    def _collide_player_shots(self, t: int, e: Enemy) -> None:
        if not (0 < e.kind < 16):
            return
        for s in self.pshots:
            if s.x <= 0:
                continue
            if (e.x - C.PSHOT_HIT_HALF_X < s.x < e.x + C.PSHOT_HIT_HALF_X
                    and e.y - C.PSHOT_HIT_HALF_Y < s.y < e.y + C.PSHOT_HIT_HALF_Y):
                e.health -= (s.cls + 1)
                self.sparks.append((e.x + 16, e.y + 16))
                self._play(C.SND_HIT)
                self._add_debris(s.x, s.y, 0.0, 0.0, C.DEBRIS_SPARK_START)
                self._reset_pshot(s)

    def _collide_missiles(self, t: int, e: Enemy) -> None:
        if not (0 < e.kind < 16):
            return
        for m in self.missiles:
            if (e.x - C.MISSILE_HIT_HALF < m.x < e.x + C.MISSILE_HIT_HALF
                    and e.y - C.MISSILE_HIT_HALF < m.y < e.y + C.MISSILE_HIT_HALF):
                e.health -= C.MISSILE_DAMAGE
                self._play(C.SND_HIT)
                for _ in range(10):
                    self._add_debris(m.x + int(random.random() * 60 - 30),
                                     m.y + int(random.random() * 60 - 30),
                                     0.0, -2.0, 0)
                self._reset_missile(m)

    def _kill_enemy(self, t: int, e: Enemy) -> None:
        self._add_debris(e.x + random.random() * 20 - 10,
                         e.y + random.random() * 20 - 10,
                         0.0, 1.0, 0)
        e.health -= 1
        if e.health > -6:
            return

        for _ in range(5):
            self._add_debris(e.x + 12, e.y + 12,
                             random.random() * 10 - 5,
                             random.random() * 10 - 3,
                             int(random.random() * 9) + 20)

        if 9 < e.kind < 16:
            self.player.score += C.BOSS_SECTION_SCORE
        else:
            self.player.score += C.SCORES.get(e.kind, 0)

        if e.powerup in C.POWERUP_KIND:
            kind = C.POWERUP_KIND[e.powerup]
            slot = self.enemies[self.curenemy]
            slot.x, slot.y = e.x, e.y
            slot.vel_x, slot.vel_y = 0.0, 1.0
            slot.userflag = 32
            slot.health = 100
            slot.kind = kind
            slot.px, slot.py = slot.x, slot.y
            self.curenemy += 1
            if self.curenemy >= C.MAX_ENEMIES:
                self.curenemy = 0

        if 9 < e.kind < 16:
            e.kind += 6
            e.health = 1
        else:
            self._reset_enemy(e)

    def _enemy_fire(self, t: int, e: Enemy) -> None:
        if not (0 < e.kind < 16):
            return
        if random.randrange(self.fire_chance) != 0:
            return
        slot = self.eshots[self.cureshot]
        if slot.x != -10:
            return
        p = self.player
        dx = abs(e.x - p.x)
        dy = abs(e.y - p.y)
        if dx > dy:
            slot.vel_x = C.ENEMY_SHOT_SPEED
            slot.vel_y = dy / (dx / C.ENEMY_SHOT_SPEED) if dx else 0.0
            slot.x = e.x + 12
            slot.y = e.y + 12
        else:
            slot.vel_y = C.ENEMY_SHOT_SPEED
            slot.vel_x = dx / (dy / C.ENEMY_SHOT_SPEED) if dy else 0.0
            slot.x = e.x + 12
            slot.y = e.y + 12
        slot.ang = angle_256(p.x, p.y, e.x, e.y)
        if e.x > p.x:
            slot.vel_x *= -1
        if e.y > p.y:
            slot.vel_y *= -1
        slot.px, slot.py = slot.x, slot.y
        self.cureshot += 1
        if self.cureshot >= C.MAX_ESHOTS:
            self.cureshot = 0

    def _contact_player(self, t: int, e: Enemy) -> None:
        p = self.player
        if not ((e.kind < 16 or e.kind > 99)
                and p.x - 16 < e.x < p.x + 16
                and p.y - 16 < e.y < p.y + 16):
            return
        if self.noharm == 0 and e.kind < 100:
            self.noharm = C.NOHARM_FRAMES
            p.health -= C.ENEMY_CONTACT_DAMAGE
            self._add_debris(p.x + 12, p.y + 12,
                             random.random() * 10 - 5,
                             random.random() * 10 - 3,
                             int(random.random() * 9) + 20)
            e.health -= C.ENEMY_CONTACT_SELF_DAMAGE
        if e.kind == 100:
            p.gunlevel += 1
            if p.gunlevel == 3:
                p.gunlevel = 2
            self._reset_enemy(e)
            self._play(C.SND_POWERUP)
        elif e.kind == 101 and p.health > 0:
            p.health += C.POWERUP_HEALTH_BONUS
            if p.health > C.PLAYER_MAX_HEALTH:
                p.health = C.PLAYER_MAX_HEALTH
            self._reset_enemy(e)
            self._play(C.SND_HEALTH)
        elif e.kind == 102:
            if p.ammo < C.AMMO_MAX:
                p.ammo += 1
            self._reset_enemy(e)
            self._play(C.SND_ROCKET)

    # -- projectiles -----------------------------------------------------

    def _update_pshots(self) -> None:
        for s in self.pshots:
            s.y -= s.vel_y
            if s.y < -33:
                self._reset_pshot(s)
            if s.cls == 2:
                self._add_debris(s.x + random.random() * 24,
                                 s.y + random.random() * 24,
                                 0.0, -1.0, C.DEBRIS_GUNTRAIL_START)

    def _update_eshots(self) -> None:
        p = self.player
        for s in self.eshots:
            s.x += s.vel_x
            s.y += s.vel_y
            if s.x < -11 or s.x > 321 or s.y < -9 or s.y > 201:
                self._reset_eshot(s)
            if (self.noharm == 0
                    and p.x < s.x < p.x + 24
                    and p.y < s.y < p.y + 24):
                self.noharm = C.NOHARM_FRAMES
                self._play(C.SND_HIT)
                p.health -= C.ENEMY_SHOT_DAMAGE
                self._add_debris(s.x, s.y,
                                 random.random() * 10 - 5,
                                 random.random() * 10 - 3,
                                 int(random.random() * 9) + 20)
                self._reset_eshot(s)

    # -- events ----------------------------------------------------------

    def _process_events(self) -> None:
        if self.curevent >= len(self.events.events):
            return
        ev = self.events.events[self.curevent]
        if ev.frame != self.curframe:
            return
        if ev.kind == "T":
            self._play(C.SND_TEXT)
            self.text = ev.buff
            self.text_x, self.text_y = ev.x, ev.y
            self.text_ticks = 100
        elif ev.kind == "F":
            for i in range(6):
                e = self.enemies[i]
                if i < 3:
                    e.x = 116 + i * 32
                    e.y = 200.0
                else:
                    e.x = 116 + (i - 3) * 32
                    e.y = 232.0
                e.kind = 9 + (i + 1)
                e.powerup = " "
                e.vel_x = 0.0
                e.vel_y = -1.0
                e.userflag = 0
                e.health = self.boss_health
                e.px, e.py = e.x, e.y
        elif ev.kind.isdigit() and 1 <= int(ev.kind) <= 9:
            e = self.enemies[self.curenemy]
            e.x, e.y = float(ev.x), float(ev.y)
            e.kind = int(ev.kind)
            e.powerup = ev.buff[:1] if ev.buff else " "
            e.px, e.py = e.x, e.y
            self._init_enemy_velocity(e)
            self.curenemy += 1
            if self.curenemy >= C.MAX_ENEMIES:
                self.curenemy = 0
        self.curevent += 1

    def _init_enemy_velocity(self, e: Enemy) -> None:
        k = e.kind
        if k == 1:
            e.vel_x = e.vel_y = 0.0
            e.userflag = 0
            e.health = 1
        elif k == 2:
            e.vel_x = 1.0 if e.x < 144 else -1.0
            e.vel_y = 4.0
            e.userflag = 0
            e.health = 2
        elif k == 3:
            if e.x < 144:
                e.vel_x = 1.5
                e.userflag = 2
            else:
                e.vel_x = -1.5
                e.userflag = 0
            e.vel_y = 0.0
            e.health = 2
        elif k == 4:
            e.vel_x = e.vel_y = 0.0
            e.userflag = 0
            e.health = 1
        elif k == 5:
            e.vel_x = 0.0
            e.vel_y = 1.0
            e.userflag = 0
            e.health = 3
        elif k == 6:
            if e.x < 144:
                e.vel_x = 3.5
                e.userflag = 192
            else:
                e.vel_x = -3.5
                e.userflag = 64
            e.vel_y = 0.0
            e.health = 1
        elif k == 7:
            if e.x < 144:
                e.vel_x = 4.0
            else:
                e.vel_x = -4.0
            e.vel_y = 4.0
            e.health = 1
            e.userflag = 255

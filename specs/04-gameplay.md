# Gameplay Model

All values are per simulation tick (50 Hz), taken verbatim from
`CONGEN2.BAS`. Coordinates are logical 320×200 pixels, origin top-left.

## 1. Constants

| Name | Value | Meaning |
|---|---|---|
| `PLAYER_START_X/Y` | 144 / 160 | ship start |
| `PLAYER_VEL_X/Y` | 4 / 3 | ship speed |
| `PLAYER_BOUNDS_X` | 0 … 283 | ship x clamp |
| `PLAYER_BOUNDS_Y` | 5 … 162 | ship y clamp |
| `PLAYER_HEALTH` | 100 max | |
| `PLAYER_START_AMMO` | 5 | missiles |
| `AMMO_MAX` | 10 | |
| `SHOT_SLOTS` | 4 | player bullets |
| `MISSILE_SLOTS` | 4 | |
| `ENEMY_SLOTS` | 8 | |
| `ESHOT_SLOTS` | 8 | |
| `DEBRIS_SLOTS` | 50 | particle pool |
| `SHOT_DELAY` | 10 − gun level | frames between shots |
| `MISSILE_DELAY` | 100 | frames between missiles |
| `MISSILE_PRECISION` | 0.4 | homing x correction |
| `MISSILE_MAX_XSPD` | 4 | homing x clamp |
| `NOHARM_FRAMES` | 10 | post-hit invulnerability |

## 2. Player

- Frames: `0` idle, `1` engine animation (alternates 0↔1 each tick),
  `2` banking (or mirrored when turning right).
- Movement: arrows; clamp to bounds above. Move left sets bank-left, right sets
  bank-right. The bank state is cleared next tick by the engine alternation
  (faithful quirk: banking lasts one frame).
- After-image: every 2nd tick, draw the current ship frame as a silhouette in
  palette colour 245, at a position lerped 20 % toward screen centre
  `(160,100)`.
- `Health` clamped at 0. At 0, `Deathflag` starts; ship explodes over 300
  ticks, spawning debris, then the level ends.

### Weapon levels
| Level | Velocity Y | Damage | Sprite | Sound |
|---|---|---|---|---|
| 0 | 8 | 1 | disparo | 1 |
| 1 | 12 | 2 | disparo2 | 7 |
| 2 | 16 | 3 | disparo3 | 8 |

- Fire with Left-Control while `Shotdelay == 0`; then
  `Shotdelay = 10 − Gunlevel`.
- Shots travel up; despawn when `y < -33`.
- Level-2 shots emit a trailing particle (`Userflag 70`) each tick.

### Missiles
- Fire with Space if `Ammo > 0` and `missiledelay == 0`; consumes one ammo,
  sets cooldown 100.
- On launch, lock onto a random living enemy (`Kind != 0`); if none, lock 1.
- Homing: `VelY -= 0.1` clamped to ≥ −5; steer `VelX` by ±0.4 toward target,
  clamped ±4. Rotation angle = `VelX * 8` (0–255 units).
- Damage 20; emits a trail particle each tick; despawn above `y < -62`.

## 3. Enemy types

Spawn initialisation (from event `KIND`, `X`, `Y`, `BUFF`):

| Kind | Health | Initial velocity | Sprite | AI |
|---|---|---|---|---|
| 1 | 1 | (0,0) | malo1 frames 0–1 | **AI1** |
| 2 | 2 | (±1 toward centre, 4) | malo2 frames 0–2 | **AI2** |
| 3 | 2 | (±1.5, 0) | malo3 frames 0–1 (mirror) | **AI3** |
| 4 | 1 | (0,0) | malo1 mirrored vertically | **AI4** |
| 5 | 3 | (0,1) | mina rotated to player | **AI5** |
| 6 | 1 | (±3.5, 0) | malo4 frames 0–1 rotated | **AI6** |
| 7 | 1 | (±4, 4) | malo5 rotated | **AI7** |

Kind 3 initial `Userflag`: 2 if spawned left of centre (moving right), else 0.
Kind 6 initial `Userflag`: 192 if left, else 64.

### AI routines
- **AI1** — `VelY += 0.05`; toggle frame 0↔1.
- **AI2** — `VelY -= 0.05`; frame counter +1, wraps at 15 (3 frames × 5 ticks).
- **AI3** — toggle frame 0↔1 (right-facing) or 2↔3 (left-facing/mirror).
- **AI4** — `VelY -= 0.05`; toggle frame 0↔1 (drawn vertically mirrored).
- **AI5** — no movement change; rendered rotated to face the player.
- **AI6** — `VelY += 0.05`; spin angle ±1 every 3 ticks depending on `VelX`
  sign.
- **AI7** — spin angle `Userflag -= 10` (mod 256).

### Generic enemy fire
Every tick, for each living enemy (`1 ≤ Kind ≤ 15`) with a free shot slot,
1-in-40 chance to fire an `EShot` aimed at the player:
- Designate dominant axis; speed 3 on it, proportional on the other;
- angle = `DQBangle(player, enemy)`; rotation applied at render;
- damage 15 on hit; despawn outside `x∈[-11,321]`, `y∈[-9,201]`.

## 4. Boss

- Event `F` spawns 6 sections (kinds 10–15) in a 3×2 grid:
  - sections 1–3 (top row) at `x = 116 + (i-1)*32`, `y = 200`;
  - sections 4–6 (bottom row) at `x = 116 + (i-4)*32`, `y = 232`;
  - `VelY = -1`, `Health = bosshealth`.
- **AIBoss** (driven by section 1):
  - rises until `y == 20`, then `VelY=0`, `VelX=-1` (patrol);
  - at `x == 5` reverse to `VelX=+1`;
  - at `x == 218` reverse to `VelX=-1`;
  - sections 2–6 rigidly follow section 1's offsets (3×2 grid preserved).
- A destroyed section (`Health ≤ -6`) becomes `Kind + 6` (16–21, "weak" art).
- Boss is defeated when all six sections are destroyed (`16,17,18,19,20,21`).
  Then section 1 sets `VelY = 0.2`, `BossDeathFlag = 1` and emits debris.
- `BossDeathFlag` counts up; at **300** play `finjefe`, set `levelpassed`,
  clear enemies; at **400** exit the level loop.

## 5. Collisions & damage

- Player shot vs enemy (kind 1–15): hit box ±24 x, ±16 y around enemy origin.
  Damage = `Class + 1`. On hit: impact sparks (`Userflag 60`), `golpe` sound,
  shot cleared.
- Missile vs enemy (kind 1–15): hit box ±30 x, ±30 y. Damage 20. Explosion.
- Enemy body vs player (kind <16 or >99): ±16 box. Damage 30 to player, 5 to
  enemy; spawns debris. Rate-limited by `noharm`.
- Enemy shot vs player: ±24 box. Damage 15; `golpe` sound; debris.
- `noharm` gates all contact damage for 10 ticks after any hit.
- Invincibility cheat forces `Health = 100` each tick.

## 6. Power-ups

Dropped on enemy death if the spawn event carried a power-up letter:

| Letter | Kind | Effect | Sound |
|---|---|---|---|
| `P` | 100 | Gunlevel +1 (capped at 2) | 9 |
| `H` | 101 | Health +20 (capped 100) | 10 |
| `M` | 102 | Ammo +1 (capped 10) | 13 |

- Pickups drift down (`VelY = 1`) and pulse in scale
  (`Userflag` oscillates 25↔40).
- Collected on player contact (±16 box).

## 7. Scoring

| Killed | Points |
|---|---|
| kind 1 | 1500 |
| kind 2 | 3000 |
| kind 3 | 3500 |
| kind 4 | 5000 |
| kind 5 | 6000 |
| kind 6 | 2500 |
| kind 7 | 7000 |
| each boss section | 10000 |

`maxscore` updates when a level ends.

## 8. Debris / particle pool

`Userflag` is a state machine over 50 pooled slots:

| Range | Effect | Frames |
|---|---|---|
| 0–17 | explosion anim (`expl 0–5`) | 18 |
| 20–28 | shard, spawns child debris at 22 & 27 | 9 |
| 30–56 | rocket trail (`debris 0–2`) | 27 |
| 60–67 | impact spark (`expl 6–7`, mirrored halves) | 8 |
| 70–79 | gun-level-2 trail (`debris 7`) | 10 |

## 9. HUD

Per player row (y = 10): `Energia P{n} : <hp>%`, `Arma Nivel <gun+1>`,
`Misiles : <ammo>`, and score. `ESCUDO` shown while invulnerable or `noharm`.

## 10. Cheats (preserved)

- `F1` toggle invincibility
- `F2` / `F3` / `F4` set gun level 0 / 1 / 2
- `F5` ammo = 100
- `P` pause

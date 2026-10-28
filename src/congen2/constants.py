"""Named constants derived verbatim from legacy_app/CONGEN2.BAS.

Coordinates are logical 320x200 pixels (origin top-left).  Velocities and
timings are expressed *per simulation tick* (the original ran at a fixed
50 Hz), so they can be carried over unchanged.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
SCREEN_W = 320
SCREEN_H = 200
TICK_RATE = 50          # simulation ticks per second (original DQBsetFrameRate 50)
TICK_DT = 1.0 / TICK_RATE
MAX_FPS = 120           # render cap (QoL)

# ---------------------------------------------------------------------------
# Object pools (original DIM sizes)
# ---------------------------------------------------------------------------
MAX_PLAYERS = 1         # game only ever plays player 1
MAX_PSHOTS = 4
MAX_MISSILES = 4
MAX_ENEMIES = 8
MAX_ESHOTS = 8
MAX_DEBRIS = 50

# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------
PLAYER_START_X = 144
PLAYER_START_Y = 160
PLAYER_VEL_X = 4
PLAYER_VEL_Y = 3
PLAYER_UP_LIMIT = 5
PLAYER_DOWN_LIMIT = 162
PLAYER_RIGHT_LIMIT = 283

PLAYER_MAX_HEALTH = 100
PLAYER_START_AMMO = 5
AMMO_MAX = 10

SHOT_DELAY_BASE = 10            # Shotdelay = 10 - Gunlevel
MISSILE_DELAY = 100
MISSILE_PRECISION = 0.4
MISSILE_MAX_X_SPEED = 4.0
MISSILE_DAMAGE = 20

NOHARM_FRAMES = 10              # post-hit invulnerability window

# Gun levels: velocity, damage, sprite/kind, sound id
GUN_SPEEDS = (8, 12, 16)
GUN_DAMAGE = (1, 2, 3)
GUN_SOUNDS = (1, 7, 8)

# ---------------------------------------------------------------------------
# Enemies
# ---------------------------------------------------------------------------
ENEMY_FIRE_CHANCE = 40          # INT(RND*40)==0 -> 1/40 per tick (HARD)
ENEMY_SHOT_SPEED = 3.0
ENEMY_SHOT_DAMAGE = 15

# Difficulty -> enemy fire chance (higher value == rarer shots).
FIRE_CHANCES = {"hard": 40, "normal": 60, "easy": 100}
DIFFICULTY_ORDER = ("easy", "normal", "hard")
DIFFICULTY_LABELS = {"easy": "FACIL", "normal": "NORMAL", "hard": "DIFICIL"}
ENEMY_CONTACT_DAMAGE = 30
ENEMY_CONTACT_SELF_DAMAGE = 5

# Hit boxes (half-extents relative to enemy origin)
PSHOT_HIT_HALF_X = 24
PSHOT_HIT_HALF_Y = 16
MISSILE_HIT_HALF = 30
PLAYER_CONTACT_HALF = 16

# Score per enemy kind
SCORES = {
    1: 1500,
    2: 3000,
    3: 3500,
    4: 5000,
    5: 6000,
    6: 2500,
    7: 7000,
}
BOSS_SECTION_SCORE = 10000

# Boss
BOSS_SECTION_KINDS = (10, 11, 12, 13, 14, 15)
BOSS_WEAK_KINDS = (16, 17, 18, 19, 20, 21)
BOSS_TOP = 20
BOSS_LEFT = 5
BOSS_RIGHT = 218
BOSS_DEATH_PASS_TICK = 300      # levelpassed set here
BOSS_DEATH_EXIT_TICK = 400      # level loop exits here

# ---------------------------------------------------------------------------
# Power-ups
# ---------------------------------------------------------------------------
POWERUP_KIND = {"P": 100, "H": 101, "M": 102}
POWERUP_HEALTH_BONUS = 20
POWERUP_SCALE_MIN = 25          # original DQBsPut Userflag range
POWERUP_SCALE_MAX = 40

# ---------------------------------------------------------------------------
# Sound ids (original load order)
# ---------------------------------------------------------------------------
SND_SHOT = 1
SND_EXPLODE = 2
SND_HIT = 3
SND_DEATH = 4
SND_PAUSE = 5
SND_TEXT = 6
SND_SHOT2 = 7
SND_SHOT3 = 8
SND_POWERUP = 9
SND_HEALTH = 10
SND_BOSS_DEATH = 11
SND_MISSILE = 12
SND_ROCKET = 13
SND_MENU = 14

# ---------------------------------------------------------------------------
# Colours (palette indices used by the original)
# ---------------------------------------------------------------------------
COL_AFTERIMAGE = 245
COL_WHITE = 255
COL_HUD_MAIN = 255
COL_HUD_HEALTH = 145
COL_HUD_SCORE = 40
COL_HUD_WEAPON = 125
COL_HUD_SHIELD = 160
COL_MENU_TEXT = 255
COL_MENU_LEVEL = 145
COL_MENU_SCORE_LABEL = 40
COL_MENU_SCORE_VALUE = 125
COL_TEXT_EVENT = 50

# ---------------------------------------------------------------------------
# Debris state-machine ranges (Userflag)
# ---------------------------------------------------------------------------
# 0..17   explosion anim, 18 frames
# 20..28  shard, spawns child debris at 22 & 27, 9 frames
# 30..56  rocket trail, 27 frames
# 60..67  impact spark, 8 frames
# 70..79  gun-level-2 trail, 10 frames
DEBRIS_EXPLOSION_END = 18
DEBRIS_SHARD_START = 20
DEBRIS_SHARD_END = 29
DEBRIS_TRAIL_START = 30
DEBRIS_TRAIL_END = 57
DEBRIS_SPARK_START = 60
DEBRIS_SPARK_END = 68
DEBRIS_GUNTRAIL_START = 70
DEBRIS_GUNTRAIL_END = 80

# ---------------------------------------------------------------------------
# Menu / misc
# ---------------------------------------------------------------------------
MAX_KEY_DELAY = 25
MENU_OPTIONS = ("Iniciar juego", "Nivel de inicio:", "Salir")

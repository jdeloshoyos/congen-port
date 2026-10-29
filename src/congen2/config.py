"""Persistent user settings and save-game data.

The original writes ``cg2data/savegame.dat`` next to the game.  The legacy
tree is read-only for this project, so the port stores both the save game and
the user preferences under a per-user application data directory instead.

The save-game *format* is unchanged (max score, max level reached), it simply
lives elsewhere.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

from .dataformats import SaveGame, load_savegame, save_savegame

APP_NAME = "Congen2"


def user_data_dir() -> Path:
    override = os.environ.get("CONGEN2_USER_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / APP_NAME.lower()


# Logical action -> pyglet key symbol name
DEFAULT_BINDINGS = {
    "up": "UP",
    "down": "DOWN",
    "left": "LEFT",
    "right": "RIGHT",
    "fire": "LCTRL",
    "missile": "SPACE",
    "pause": "P",
    "enter": "ENTER",
    "escape": "ESCAPE",
}


@dataclass
class Config:
    music_on: bool = False          # original had no music; opt-in
    sfx_on: bool = True
    music_volume: float = 0.5
    sfx_volume: float = 0.7
    fullscreen: bool = False
    scale: int = 3
    difficulty: str = "normal"
    bindings: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_BINDINGS))

    # ---------------------------------------------------------------
    def path(self) -> Path:
        return user_data_dir() / "config.json"

    def save(self) -> None:
        p = self.path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(asdict(self), fh, indent=2)

    @classmethod
    def load(cls) -> "Config":
        p = cls().path()
        try:
            with open(p, "r", encoding="utf-8") as fh:
                raw = json.load(fh)
        except (OSError, ValueError):
            return cls()
        cfg = cls()
        for key, value in raw.items():
            if key == "bindings" and isinstance(value, dict):
                cfg.bindings = {**DEFAULT_BINDINGS, **value}
            elif hasattr(cfg, key):
                setattr(cfg, key, value)
        return cfg


def save_path() -> Path:
    return user_data_dir() / "savegame.dat"


def load_save() -> SaveGame:
    p = save_path()
    if p.exists():
        return load_savegame(str(p))
    return SaveGame()


def persist_save(save: SaveGame) -> None:
    p = save_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    save_savegame(str(p), save)


# ---------------------------------------------------------------------------
# Data directory discovery (legacy assets, always read-only)
# ---------------------------------------------------------------------------


def data_dir() -> Path:
    override = os.environ.get("CG2_DATA_DIR")
    if override:
        return Path(override)
    here = Path(__file__).resolve()
    candidates: list[Path] = []
    # PyInstaller (onefile/onedir) extracts bundled data under _MEIPASS.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / "data")
    candidates += [
        Path.cwd() / "data",          # running from the repo root
        here.parents[2] / "data",     # repo layout (project root / data)
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]

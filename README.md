# Congeneration 2 — Python/pyglet port

A faithful recreation of **Congeneration 2**, the top-down space shooter written
in QuickBasic 4.5 + DirectQB by Jaime de los Hoyos (art by Vicente de los Hoyos).
The original DOS application is kept untouched under `legacy_app/` and is used
as the behavioural and asset reference.

## Requirements

- [uv](https://docs.astral.sh/uv/) (project/venv/dependency management)
- Python 3.15 (pinned in `.python-version`; uv uses the system interpreter)

Dependencies are declared in `pyproject.toml` and locked in `uv.lock`.

```bash
uv sync
```

This creates `.venv`, installs `pyglet` and the `congen2` package, and keeps
the environment in sync. No global install is required.

## Run

```bash
uv run python run.py
# equivalent console entry point
uv run congen2
# point at a custom data folder, or force a fixed window scale
uv run python run.py --data data --scale 5
```

On launch the window is sized to the largest integer scale of the original
320×200 frame that fits your primary screen (and centred on it); `F11` toggles
fullscreen. Use `--scale N` to force a fixed scale, or `--auto-scale` to return
to automatic sizing.

### Controls

| Action | Key |
|---|---|
| Move | Arrow keys |
| Fire main gun | Left Ctrl |
| Homing missile | Space |
| Pause menu | P |
| Quit to menu | Escape |
| Music on/off | M |
| SFX on/off | N |
| Fullscreen | F11 |
| Cheats | F1 invincible, F2/F3/F4 gun level, F5 +100 missiles |

All gameplay keys are remappable from **Pause → Controles**; bindings persist.

## What is faithful

- **320×200, 256 colours**, colour 0 transparent, the original palette preserved
  in `data/palette.pal`.
- **50 Hz fixed simulation** — every velocity, AI routine, event frame and
  spawn table is carried over verbatim.
- The original art is **losslessly converted to RGBA PNG** under `data/`; WAV
  audio, the `HITECH.FNT` font, `.CMP` maps and `.DAT` event scripts are carried
  over unchanged.
- Menu, level flow, boss sequence, power-ups, scoring, cheats and HUD match the
  original.

## Quality-of-life additions (opt-in)

- **Adaptive rendering up to 120 FPS** with interpolation; simulation stays at
  50 Hz.
- Windowed launch auto-selects the largest integer scale that fits the screen
  (manual `--scale` override); integer-scaled window + optional fullscreen.
- **Optional background music** (`CANCION1.WAV`, unused in the original) with
  an on/off toggle.
- SFX on/off, configurable controls, and a proper pause menu.
- **Difficulty setting** (FACIL / NORMAL / DIFICIL, default NORMAL) in the pause
  menu, controlling how often enemies shoot (HARD = the original rate).
- Original save data (`maxscore`, `maxlevelreached`) is preserved but written to
  a per-user directory — **`legacy_app/` is never modified**.

## Project layout

```
legacy_app/            untouched original game + assets (reference)
data/                  ported runtime assets (RGBA PNG + audio/font/maps)
specs/                 behaviour/format specifications
src/congen2/
  constants.py         all tuning values from CONGEN2.BAS
  dataformats.py       pure decoders: FNT, CMP, DAT, savegame (+ PCX for converter)
  png.py               pure-Python RGBA PNG encode/decode
  world.py             deterministic simulation (player/enemies/AI/boss/…)
  assets.py            pyglet PNG textures, glyph textures, sounds
  render.py            layered rendering, background scroll, HUD, menus
  audio.py             SFX pool + music
  config.py            user settings + save-game persistence
  app.py               window, fixed-timestep loop, state machine, input
entry.py               PyInstaller entry point (frozen app)
icon.ico               application icon (generated from the ship sprite)
run.py                 dev entry point
tools/                 screenshot / smoke / flow / converter / build helpers
tests/                 headless unit tests
```

Regenerate `data/` from `legacy_app/Cg2data/` at any time with:

```bash
uv run python tools/convert_assets.py
```

## Packaging (Windows)

Build a standalone folder distribution with PyInstaller:

```bash
uv sync
uv run python tools/build.py
```

This produces `dist/Congen2/` containing `Congen2.exe` plus an `_internal/`
folder with the Python runtime, pyglet, and the bundled `data/` assets.
Distribute that folder as-is (e.g. zip it) — no installer required. The frozen
app resolves `data/` through `sys._MEIPASS`; saves and settings still go to
`%APPDATA%\Congen2`.

`tools/build.py` generates `icon.ico` from the ship sprite if it is missing;
regenerate it explicitly with `uv run python tools/make_icon.py`.

## Tests

```bash
uv run python -m unittest discover -s tests -v
```

Verification helpers:

```bash
uv run python tools/smoke.py                       # real event loop, closes after 1s
uv run python tools/flowtest.py                    # menu/level/pause/controls flow
uv run python tools/progression.py                 # full 2-level playthrough -> credits
uv run python tools/screenshot.py --state menu --out shots/menu.png
uv run python tools/screenshot.py --state level --ticks 320 --fire --out shots/level.png
```

## Specifications

The reverse-engineered behaviour and formats are documented in `specs/`:

1. `01-overview.md`
2. `02-asset-formats.md`
3. `03-game-states.md`
4. `04-gameplay.md`
5. `05-rendering.md`
6. `06-input.md`
7. `07-enhancements.md`

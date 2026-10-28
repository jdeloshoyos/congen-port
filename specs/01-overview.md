# Congeneration 2 — Port Overview

## 1. Purpose

This project is a faithful port of **Congeneration 2**, a top-down space shooter
written in QuickBasic 4.5 + DirectQB 1.61 by Jaime de los Hoyos (art by Vicente
de los Hoyos). The original DOS application lives untouched in `legacy_app/` and
is the behavioural reference. This port recreates the game on a modern stack
while preserving assets, gameplay, timing and feel, and adds a small set of
opt-in quality-of-life improvements.

## 2. Source of truth

- `legacy_app/CONGEN2.BAS` — the complete original source (1571 lines, CRLF).
- `legacy_app/Cg2data/` — original art, sound, maps, events and save data.
- `legacy_app/Readme.txt` — controls and background.
- `legacy_app/Shot1.jpg` … `Shot4.jpg` — visual reference screenshots.

**The `legacy_app/` tree must never be modified.** All derived assets are read
from it at runtime (or converted into an in-memory form); nothing is written
back.

## 3. Target stack

| Concern | Choice |
|---|---|
| Language | Python 3.15 |
| Windowing / GPU | pyglet 2.1 (OpenGL) |
| Audio | pyglet.media (WAV) |
| Asset decode | Built-in pure-Python PCX + FNT decoders |
| Tests | Python `unittest` (headless; no display required) |

## 4. Resolution & timing

- **Logical resolution: 320 × 200**, 256-colour palette, colour index 0 is
  transparent (chroma key), exactly like VGA mode 13h.
- **Simulation: fixed 50 Hz tick.** One tick equals one frame of the original;
  every constant, velocity and event frame number carries over verbatim.
- **Rendering: decoupled, adaptive, capped at 120 FPS**, with interpolation
  between simulation ticks for smooth motion.
- The logical frame is scaled to the window with **integer scaling**
  (default 3× = 960×600) and optional fullscreen; letterboxed as needed.

## 5. High-level architecture

```
src/congen2/
  constants.py     All tuning values (named, documented).
  dataformats.py   Pure decoders: PCX, FNT, CMP, DAT, savegame. No pyglet.
  world.py         Deterministic simulation: player, enemies, shots,
                   missiles, debris pool, map scroll, events, collisions.
  events.py        Event scheduling model (parsed from .DAT).
  ai.py            Enemy AI routines (AI1–AI7, boss).
  assets.py        pyglet texture / sound / font-atlas construction.
  config.py        Persistent user settings (music, controls, etc.).
  app.py           Window, fixed-timestep loop, state machine, rendering,
                   menu, HUD, pause overlay.
  states/          Menu, Level, Credits screens (driven by app).
run.py             Entry point.
tools/             Asset inspection / verification utilities.
tests/             Headless unit tests.
```

The simulation (`world.py`, `events.py`, `ai.py`, `dataformats.py`) is pure
Python and fully testable without a display. Rendering and input live only in
`assets.py` / `app.py`.

## 6. Fidelity policy

1. **Behaviour first.** Gameplay logic, AI, spawn tables, collisions, scoring
   and state transitions mirror the original.
2. **Assets unchanged.** Original PCX/WAV/FNT/CMP/DAT files are consumed as-is.
3. **Palette-faithful.** One shared 256-colour palette is extracted from the
   original art and applied to every image.
4. **Timing-faithful.** 50 Hz simulation; no speed rescaling.
5. **Additive QoL only.** Enhancements are opt-in and never alter core
   behaviour (see `07-enhancements.md`).

## 7. Non-goals

- Remaking or upscaling the art/audio (originals are used as-is).
- Networked, multi-player or persistent-campaign features beyond the original
  single-player flow.
- Recreating DirectQB internals; only its observable behaviour matters.

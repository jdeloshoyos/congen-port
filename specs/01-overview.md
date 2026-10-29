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

**The `legacy_app/` tree must never be modified.** It is the reference; the
ported app reads its own assets from the top-level **`data/`** folder, which is
generated losslessly from `legacy_app/Cg2data/` by `tools/convert_assets.py`
(PCX → RGBA PNG; audio/font/maps/events copied). Nothing is written back to
`legacy_app/`.

## 3. Target stack

| Concern | Choice |
|---|---|
| Language | Python 3.15 |
| Windowing / GPU | pyglet 2.1 (OpenGL) |
| Audio | pyglet.media (WAV) |
| Asset decode | pyglet (PNG) + pure-Python FNT/CMP/DAT decoders |
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
  dataformats.py   Pure decoders: FNT, CMP, DAT, savegame (+ PCX for the
                   converter). No pyglet.
  png.py           Pure-Python RGBA PNG encode/decode (converter + tests).
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
2. **Assets losslessly converted.** The original PCX art is converted to
   true-colour RGBA PNG (byte-identical pixels; WAV/FNT/CMP/DAT copied as-is).
3. **Palette-faithful.** The original 256-colour palette is preserved in
   `palette.pal` (colours are baked into the PNGs, and the palette still drives
   text/after-image tinting).
4. **Timing-faithful.** 50 Hz simulation; no speed rescaling.
5. **Additive QoL only.** Enhancements are opt-in and never alter core
   behaviour (see `07-enhancements.md`).

## 7. Non-goals

- Remaking or upscaling the art/audio (originals are used as-is).
- Networked, multi-player or persistent-campaign features beyond the original
  single-player flow.
- Recreating DirectQB internals; only its observable behaviour matters.

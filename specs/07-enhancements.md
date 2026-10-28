# Quality-of-Life Enhancements

All enhancements are **additive and opt-in**. Disabling them restores the
original behaviour exactly.

## 1. Adaptive frame rate

- Simulation remains fixed at **50 Hz**, preserving original behaviour.
- Rendering is decoupled and runs as fast as the display allows, **capped at
  120 FPS**, with interpolation between ticks.
- Result: smoother motion on modern displays without changing game logic.

## 2. Window & display

- Default window 960×600 (3× integer scale of 320×200).
- Integer scaling with letterboxing; no blurry non-integer stretch.
- `F11` toggles fullscreen, using the largest integer scale that fits.
- Optional: nearest-neighbour filtering to keep pixel art crisp.

## 3. Music

- The original contains an unused track, `CANCION1.WAV`; the port uses it as an
  optional looping background theme.
- **Music can be turned on or off** (default off to remain faithful) via:
  - `M` key, and
  - a toggle in the pause menu.
- The choice is persisted in the user config file and restored on launch.
- Music volume and SFX on/off are likewise configurable.

## 4. Configurable controls

- The pause menu offers a controls screen to remap gameplay keys.
- Defaults match the original.
- Bindings persist in the user config file.

## 5. Pause menu

Replaces the original tight key-wait pause with a proper overlay that freezes
the simulation and offers:

- Resume
- Music on/off
- SFX on/off
- Difficulty (FACIL / NORMAL / DIFICIL)
- Controls remap
- Quit to menu

## 6. Difficulty

- Three settings, selected in the pause menu (←/→) and persisted:
  - **HARD** — enemy fire chance 1/40 per tick (the original, faithful rate).
  - **NORMAL** (default) — 1/60 per tick.
  - **EASY** — 1/100 per tick.
- Only the enemies' shooting frequency changes; movement, health, damage,
  spawns and scoring are untouched.
- Changing it mid-level takes effect immediately.

## 7. Persistence

- Original save semantics (`maxscore`, `maxlevelreached`) are preserved in
  `savegame.dat` for compatibility.
- User preferences (music, SFX, difficulty, controls, window mode) live in a
  separate config file (`config.json` under a user-config directory) so the
  original save file format is untouched.

## 8. Explicit non-enhancements

To keep the port faithful, the following are *not* changed:

- 320×200 logical resolution and all asset pixel dimensions.
- Enemy AI, spawn tables, velocities, damage, scoring.
- Fixed 50 Hz gameplay logic.
- Level flow and menu semantics.

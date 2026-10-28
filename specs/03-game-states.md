# Game States & Flow

The original uses `GOTO` labels rather than structured states. The port models
the same flow as an explicit state machine.

## 1. States

| State | Responsibility |
|---|---|
| `MENU` | Title screen, option cursor, level selection, hi-score display. |
| `LEVEL` | Active gameplay: map scroll, entities, events, HUD, pause. |
| `CREDITS` | End-of-game credits screen after the final level. |

## 2. Transitions

```
                 ENTER on "Iniciar juego"
   MENU ─────────────────────────────────▶ LEVEL (start level = selected)
     ▲                                        │
     │  ESC  (abandon, levelpassed = 0)        │
     │  player death (levelpassed = 0)         │
     │                                        ▼
     └──────────────  save & return  ◀── LEVEL ends ──┐
                                                      │ level passed
                                                      ▼
                                          level+1 exists ?
                                            │            │
                                         yes│            │no
                                            ▼            ▼
                                         LEVEL      CREDITS ──ENTER──▶ MENU
```

### Menu behaviour
- Options: 1 `Iniciar juego`, 2 `Nivel de inicio`, 3 `Salir`.
- Up/Down move the cursor (wrapping 1↔3); Left/Right on option 2 change the
  selected start level, clamped to `[1, maxlevelreached]`.
- Enter on option 1 → start `LEVEL` with the selected level.
- Enter on option 3 → persist save, quit the application.
- The animated cursor is enemy `malo2` frames 0–2 (faithful to original) drawn
  at `(140, (opt-1)*40 + 48)`.

### Level entry
1. Load `mapa{n}.cmp` and `mapa{n}.dat`.
2. Load boss image pair (`<boss>.pcx`, `<boss>wk.pcx`) and tileset.
3. Draw initial background (map rows 393–400).
4. Initialise counters; carry player Health/Score/Gunlevel/Ammo across levels,
   reset position to `(144,160)`.

### Level exit
- `EXIT` conditions inside the loop:
  - ESC pressed,
  - player death finished (`Deathflag == 300` for every player),
  - boss defeated and `BossDeathFlag == 400`.
- After exit: fade to black; update `maxscore`.
- If **not** level-passed (died or ESC): save and return to `MENU`.
- If level-passed: increment level; if the next `.dat` does not exist (or is
  empty), show `CREDITS`; otherwise save progress and enter next `LEVEL`.

### Credits
Full-screen `final.pcx` with the author credits and “Presione ENTER para
seguir.”; ENTER fades out, saves, and returns to `MENU`.

## 3. Pause

- Pressing `P` during `LEVEL` toggles a pause overlay.
- The original's pause is a tight key-wait loop; the port uses a proper paused
  state that freezes simulation and shows an overlay with the new QoL toggles
  (music/SFX, resume, quit-to-menu). Input is not consumed by gameplay while
  paused.

## 4. Persistence

- `maxscore`, `maxlevelreached` are saved exactly as the original does
  (on quit, on death/game-over, on level completion, on credits exit).
- User settings (music on/off, volume, key bindings) are stored separately so
  the original save file format remains compatible.

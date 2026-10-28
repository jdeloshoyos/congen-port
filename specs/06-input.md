# Input

## 1. Original controls (must remain available)

| Action | Key |
|---|---|
| Move | Arrow Up / Down / Left / Right |
| Fire main gun | Left Control |
| Fire homing missile | Space |
| Menu up/down | Arrow Up / Down |
| Level select | Arrow Left / Right (on “Nivel de inicio”) |
| Confirm | Enter |
| Quit to menu (in game) | Escape |
| Pause | P |
| Invincibility (cheat) | F1 |
| Gun level 0/1/2 (cheat) | F2 / F3 / F4 |
| +100 missiles (cheat) | F5 |

The original reads DOS scan-codes. The port reads physical key presses from
pyglet and maps them to the same logical actions, so behaviour is preserved on
modern keyboards.

## 2. Additional controls (QoL)

These are additive and optional:

| Action | Key |
|---|---|
| Pause / resume | P (and Escape opens pause when enabled) |
| Music toggle | M |
| SFX toggle | N |
| Fullscreen toggle | F11 |
| Quit-to-menu from pause | Escape (in pause overlay) |

## 3. Configurable bindings

- Menu navigation and gameplay bindings can be remapped in the pause menu’s
  controls sub-screen (QoL, see `07-enhancements.md`).
- Bindings are persisted in the user config file and applied at startup.
- Defaults are exactly the original controls.

## 4. Input model

- A logical action is `pressed` if any bound key is down; `just_pressed` is
  derived from a key-release edge, used for menu navigation and toggles.
- Menu key repeat uses a 25-tick delay to match the original’s `maxkeydelay`.
- Cheat keys use edge detection so a held key does not repeat every tick.

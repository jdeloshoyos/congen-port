# Rendering Model

## 1. Coordinate system & scaling

- Simulation and draw commands use the native **320×200** logical space,
  top-left origin, +x right, +y down (matching DirectQB).
- The logical frame is presented into a window using **integer scaling**
  (auto-selected to the largest fit for the primary screen; `--scale N`
  overrides). Non-integer window sizes letterbox with black bars.
- Textures are sampled with **nearest-neighbour (point) filtering**, so scaled
  pixels are crisp squares rather than bilinear-blurred.
- Optional fullscreen uses the largest integer scale that fits.

## 2. Frame composition

The original composites four layers each tick:

```
layer 0  visible framebuffer
layer 1  work layer (sprites, HUD, text)
layer 2  scrolling background / map
layer 3  menu overlay art
```

Modern equivalent per rendered frame:

1. **Background** — draw the visible map rows directly at their scrolled
   positions (closed form, see §4).
2. **Entities** — debris → missiles → enemies → player → player shots →
   enemy shots, in the original draw order.
3. **HUD / text** — drawn last, on top.
4. **Overlays** — menu art / pause overlay composite with colour-0
   transparency.

## 3. Sprite operations

| Original | Meaning | Port |
|---|---|---|
| `DQBput` | masked blit (colour 0 clear) | alpha texture quad |
| `DQBmPut(…,1)` | horizontal mirror | negative x-scale |
| `DQBmPut(…,2)` | vertical mirror | negative y-scale |
| `DQBrPut(…,ang)` | rotate about sprite centre | rotation = +ang·(360/256)° (clockwise) |
| `DQBsPut(…,s,s)` | uniform scale | scale s/32 (≈0.78…1.25) |
| `DQBhPut(…,col)` | solid silhouette | white mask tinted by `palette[col]` |
| `DQBtri` | filled triangle | triangle primitive |
| `DQBscroll` | layer scroll | derived scroll offset |

Angles are 0–255 units clockwise from “up”; `DQBangle(p1,p2) =
atan2(dx, −dy)` normalised to 0–255.

Scaling note: the original passes `Userflag` (25…40) to `DQBsPut`; the port
maps the pulsing power-up to `Userflag / 32` (≈ 0.78…1.25) for a similar
breathing effect.

## 4. Background scrolling

Equivalent to the original `scrollpos`/`mappos` scroller. For tick `t`:

```
scrollpos = (t % 32) - 31
mappos    = ((392 - (t // 32) - 1) % 392) + 1
```

Draw rows `mappos + k` (k = 0, 1, …) at `y = scrollpos + 32·k`, while `y < 200`.
Row 393–400 are only used for the initial background (`t = 0`). Each row is ten
32×32 tiles.

## 5. Interpolation

Because simulation runs at 50 Hz and rendering can run faster, each entity keeps
a previous and current position; the renderer lerps by the fraction of the
current tick elapsed. Rotation/scale interpolate for boss patrol, missiles and
pulsing pickups.

## 6. Palette & transparency

- Textures are built from 8-bit index images + the shared palette, converted to
  RGBA with index 0 → alpha 0.
- The font atlas is white glyphs on transparent, tinted per draw call.
- The after-image silhouette uses a generated alpha mask tinted with
  `palette[245]`.

## 7. Text

- Custom 8×8 bitmap font (`HITECH.FNT`), rendered from a 16×16 glyph atlas.
- Draw calls take `(text, x, y, colour_index)`; colour is palette-looked-up.
- Line height 10 px, matching the original HUD.

## 8. Effects fidelity notes

- Motion after-image: every other tick, silhouette lerped 20 % toward (160,100).
- Enemy rotation (kinds 5/6/7, boss none, missiles, enemy shots) uses the
  DirectQB angle convention above.
- Impact sparks are the two 32×32 frames from `hit.pcx`, mirrored in halves.

# Asset & Data Formats

Runtime assets live in the top-level **`data/`** folder; **`legacy_app/Cg2data/`**
remains the untouched reference. This document specifies the runtime formats
and the derived in-memory models.

## 1. Palette & colour model

- 256-colour VGA palette, **768 bytes = 256 × (R,G,B)**, stored as
  **`data/palette.pal`** (extracted verbatim from `nave.pcx`).
- Graphics are **true-colour RGBA PNG**; their colours are baked in at
  conversion time from this palette. The palette itself is now used only for
  tinting the HUD/menu text and the ship's after-image.
- **Colour index 0 is transparent** in the original; in the PNG art this becomes
  **alpha 0** (fully transparent) at conversion time.
- Colour 245 is the after-image/silhouette tint (`#0E0E0E`), applied to the
  white mask `nave_sil.png`.

## 2. PNG images (RGBA)

- True-colour + alpha, 8-bit, colour type 6 (no palette chunk).
- Converted from the original 8-bit PCX art: each pixel's palette entry is
  written as RGB, and index 0 → alpha 0. No re-quantization; pixels are
  byte-identical to the original palette.
- Loaded at runtime with `pyglet.image.load`, sliced with `get_region`
  (note: pyglet's `get_region` uses a bottom-up `y` origin, so sheet rows are
  inverted when cropping).
- The original PCX format is retained only for the one-time converter
  (`tools/convert_assets.py`) and read by `dataformats.decode_pcx`.

## 3. Sprite atlas layout

Frame counts and roles are unchanged from the original; files are simply
`.png`:

| Source | Frame size | Frames | Role |
|---|---|---|---|
| `nave.png` | 32×32 | 1 | ship idle |
| `nave2.png` | 32×32 | 1 | ship engine |
| `nave3.png` | 32×32 | 1 | ship banking |
| `nave_sil.png` | 32×32 | 1 | ship silhouette (white mask) |
| `disparo.png` | 32×32 | 1 | gun level 1 |
| `disparo2.png` | 32×32 | 1 | gun level 2 |
| `disparo3.png` | 32×32 | 1 | gun level 3 |
| `powerup.png` | 32×32 | 1 | "P" upgrade |
| `salud.png` | 32×32 | 1 | "H" health |
| `Misil.png` | 32×32 | 1 | missile |
| `Misilbox.png` | 32×32 | 1 | "M" missile box |
| `explo.png` | 32×32 | 6 | explosion frames 0–5 |
| `hit.png` | 32×32 | 2 | impact frames 6–7 |
| `debris.png` | 8×8 | 8 | debris/particle + enemy bullet |
| `malo1.png` | 32×32 | 2 | enemy kind 1 |
| `malo2.png` | 32×32 | 3 | enemy kind 2 |
| `malo3.png` | 32×32 | 2 | enemy kind 3 |
| `mina.png` | 32×32 | 1 | enemy kind 5 |
| `malo4.png` | 32×32 | 2 | enemy kind 6 |
| `malo5.png` | 32×32 | 1 | enemy kind 7 |
| `boss{1,2}.png` | 32×32 | 6 (3×2) | boss alive sections |
| `boss{1,2}wk.png` | 32×32 | 6 (3×2) | boss destroyed sections |

Enemy kind 4 reuses `malo1` mirrored vertically. Kind 100/101/102 reuse the
powerup/salud/misilbox images with a pulsing scale.

## 4. Map files (`.CMP`)

```
offset 0   : 12-byte ASCII tileset filename, e.g. "tileset1.png" (padded)
offset 12  : 4000 bytes of tile indices, stored x-fastest:
             for y in 1..400: for x in 1..10: byte = tile_index + 35
```

- Grid = **10 wide (x) × 400 tall (y)**, each cell one tile.
- `tile_index = byte - 35`, range 0–19.
- Tileset = **320×64 PNG = 2 rows × 10 columns of 32×32 tiles** (20 tiles).
- Map 1 uses `tileset1.png`, map 2 uses `tileset2.png` (the converter rewrites
  the name embedded in the copied `.cmp`).

## 5. Event files (`.DAT`)

Plain text. Line 1 = boss image base name (`boss1`/`boss2`), line 2 = boss
health (integer). Remaining lines, one event each:

```
FRAME_KINDBUFF_X_Y
```

- `FRAME` — simulation tick at which the event fires.
- `KIND` — one character:
  - `1`–`9` spawn an enemy of that kind,
  - `T` show text,
  - `F` spawn the boss.
- `BUFF` — for enemies: optional power-up letter `P`/`H`/`M`, else empty;
  for `T`: the message text (may contain spaces).
- `X`, `Y` — spawn position, or text x/y. Off-screen spawns use negative
  coordinates (e.g. `-31`).

Parsing is delimiter-based (underscores), not fixed-column. The event stream
ends after the `F` (boss) event but the file may not contain it in malformed
data.

## 6. Font (`HITECH.FNT`)

- 256 glyphs × 8 bytes = 2048 bytes, then 257 bytes of `0x08` padding.
- Each glyph is **8×8 monochrome, MSB = leftmost pixel**, 8 rows per glyph.
- Glyph index equals the character code (ASCII/CP437). All text used by the
  game is ASCII 32–126.
- Rendered as white-on-transparent glyph textures, tinted per text colour
  (via `palette.pal`) at draw time.

## 7. Sounds (`.WAV`)

- Standard RIFF/WAVE, 8-bit unsigned PCM, mono, 22050 Hz.
- Loaded directly by `pyglet.media`.
- Original 14 indexed sounds: disparo(1), explo(2), golpe(3), muerte(4),
  pausa(5), texto(6), disparo2(7), disparo3(8), powerup(9), salud(10),
  finjefe(11), misil(12), rocketl(13), menu(14).
- `CANCION1.WAV` (8-bit mono 22050 Hz, ~2.75 s) is **not** referenced by the
  original; the port uses it as an optional looping music track.

## 8. Save game (`savegame.dat`)

Two ASCII lines: `maxscore`, `maxlevelreached`. Not shipped in `data/`; the
port writes it to a per-user directory (see `07-enhancements.md`), keeping the
original save semantics.

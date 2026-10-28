# Asset & Data Formats

All files live in `legacy_app/Cg2data/` and are read-only. This document
specifies the exact byte formats and the derived in-memory models.

## 1. Palette & colour model

- 256-colour VGA palette, **768 bytes = 256 × (R,G,B)**.
- The palette is embedded in every PCX (trailing 768 bytes). The original loads
  `nave.pcx` first and keeps that palette; all art in the pack shares the same
  palette. **We extract the palette from `nave.pcx` and apply it globally.**
- **Colour index 0 is transparent** for all sprite blits (`DQBput`, mirrored,
  rotated, scaled, and transparent layer copies).
- Colour 245 is the after-image/silhouette tint used by `DQBhPut`.

## 2. PCX images (8-bit, single plane)

Header (128 bytes), little-endian fields we use:

| Offset | Field |
|---|---|
| 0 | manufacturer `0x0A` |
| 2 | encoding: `1` = RLE |
| 3 | bits per pixel (`8`) |
| 4,6,8,10 | xmin, ymin, xmax, ymax (words) |
| 65 | number of planes (`1`) |
| 66 | bytes per line (word, per plane) |

- Width = `xmax - xmin + 1`; Height = `ymax - ymin + 1`.
- Pixel stream is **RLE**: a byte `b` with `(b & 0xC0) == 0xC0` introduces a run
  of `b & 0x3F` copies of the next byte; otherwise `b` is a literal pixel.
- Each scanline occupies `bytes_per_line` bytes (may include padding beyond
  `width`); padding is discarded.
- If the last 769 bytes begin with `0x0C`, the following 768 bytes are the
  palette.

## 3. Sprite atlas layout (original)

The original loads all PCX images onto one 320-wide layer at fixed offsets and
slices 32 × 32 (or 8 × 8) regions with `DQBget`. We instead slice each source
PCX directly into frames. Frame counts:

| Source | Frame size | Frames | Role |
|---|---|---|---|
| `nave.pcx` | 32×32 | 1 | ship idle |
| `nave2.pcx` | 32×32 | 1 | ship engine |
| `nave3.pcx` | 32×32 | 1 | ship banking |
| `disparo.pcx` | 32×32 | 1 | gun level 1 |
| `disparo2.pcx` | 32×32 | 1 | gun level 2 |
| `disparo3.pcx` | 32×32 | 1 | gun level 3 |
| `powerup.pcx` | 32×32 | 1 | "P" upgrade |
| `salud.pcx` | 32×32 | 1 | "H" health |
| `misil.pcx` | 32×32 | 1 | missile |
| `Misilbox.pcx` | 32×32 | 1 | "M" missile box |
| `explo.pcx` | 32×32 | 6 | explosion frames 0–5 |
| `hit.pcx` | 32×32 | 2 | impact frames 6–7 |
| `debris.pcx` | 8×8 | 8 | debris/particle + enemy bullet |
| `malo1.pcx` | 32×32 | 2 | enemy kind 1 |
| `malo2.pcx` | 32×32 | 3 | enemy kind 2 |
| `malo3.pcx` | 32×32 | 2 | enemy kind 3 |
| `mina.pcx` | 32×32 | 1 | enemy kind 5 |
| `malo4.pcx` | 32×32 | 2 | enemy kind 6 |
| `malo5.pcx` | 32×32 | 1 | enemy kind 7 |
| `boss{1,2}.pcx` | 32×32 | 6 (3×2) | boss alive sections |
| `boss{1,2}wk.pcx` | 32×32 | 6 (3×2) | boss destroyed sections |

Enemy kind 4 reuses `malo1` mirrored vertically. Kind 100/101/102 reuse the
powerup/salud/misilbox images with a pulsing scale.

## 4. Map files (`.CMP`)

```
offset 0   : 12-byte ASCII tileset filename, e.g. "tileset1.pcx" (padded)
offset 12  : 4000 bytes of tile indices, stored x-fastest:
             for y in 1..400: for x in 1..10: byte = tile_index + 35
```

- Grid = **10 wide (x) × 400 tall (y)**, each cell one tile.
- `tile_index = byte - 35`, range 0–19.
- Tileset = **320×64 PCX = 2 rows × 10 columns of 32×32 tiles** (20 tiles).
- Map 1 uses `tileset1.pcx`, map 2 uses `tileset2.pcx`.

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
- Rendered as white-on-transparent glyphs in a 16×16 atlas, tinted per text
  colour at draw time.

## 7. Sounds (`.WAV`)

- Standard RIFF/WAVE, 8-bit unsigned PCM, mono, 22050 Hz.
- Loaded directly by `pyglet.media`.
- Original 14 indexed sounds: disparo(1), explo(2), golpe(3), muerte(4),
  pausa(5), texto(6), disparo2(7), disparo3(8), powerup(9), salud(10),
  finjefe(11), misil(12), rocketl(13), menu(14).
- `CANCION1.WAV` (8-bit mono 22050 Hz, ~2.75 s) is **not** referenced by the
  original; the port uses it as an optional looping music track.

## 8. Save game (`savegame.dat`)

Two ASCII lines: `maxscore`, `maxlevelreached`. Read at boot, rewritten on
quit / level completion. The port stores this plus user settings separately
(see `07-enhancements.md`), while keeping the original save semantics.

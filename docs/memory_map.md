# Memory map (Stage 4)

All addresses are 28-bit physical addresses. The constants are defined once in `tools/make_assets.py`
(written to `build/gen/layout.inc`); `src/layout.asm` checks that the regions do not overlap.
As in ShooterMega65, the program keeps BASIC's SYS memory map (RAM below `$C000`, I/O at `$D000`, KERNAL
above) and returns to BASIC with X or RUN/STOP. BASIC's screen RAM, colour RAM `$0000–$0FFF` and RAM below
`$2000` are never written. `$20000–$3FFFF` is ROM and never a data target.

## Bank 0

| Address | Use |
|---|---|
| `$0002–$0037` | game zero page (`$1E` tmp2 since Stage 4b) (BASIC's `$02–$FF` is saved to `SAVED_ZP` and restored on exit) |
| `$2001–$2010` | BASIC stub `BANK 0:SYS 8224` |
| `$2020–$6915` | code, tables, load buffer, palette buffer, HUD, font and spark glyph sources (guard: below `$C000`) |

## Chip RAM, banks 4/5

| Address | Size | Use |
|---|---|---|
| `$40000–$4F9FF` | ≤ 62.5 KB | arena FCM glyphs (file `A-RIO-GFX`), char `$1000`+, max. 1,000 glyphs (Rio: 996 since the generator picture of Stage 4b, 63,744 bytes) |
| `$50000–$51BFF` | 7 KB | fighter 1, frame slot A (char `$1400`+) |
| `$51C00–$537FF` | 7 KB | fighter 1, frame slot B (char `$1470`+) |
| `$53800–$5383F` | 64 B | blank NCM glyph that ends every row (char `$14E0`) |
| `$53840–$53C7F` | 17×64 B | energy bar glyphs (char `$14E1`+) |
| `$54000–$5503F` | 26×160 | RRB screen buffer A |
| `$55200–$5623F` | 26×160 | RRB screen buffer B |
| `$56400–$57FFF` | 7 KB | fighter 2, frame slot C (char `$1590`+) |
| `$58800–$5AA8F` | 8848 B | arena map (file `A-RIO-MAP`): palette 0–175 (528 B), clean screen rows, clean colour rows |
| `$5AC00–$5C7FF` | 7 KB | fighter 2, frame slot D (char `$16B0`+) |
| `$5DB00–$5DDFF` | 768 B | BASIC's palette 0 until exit |
| `$5DE00–$5DEFF` | 256 B | BASIC's zero page until exit |
| `$5E000–$5F3FF` | 80×64 B | 16×16 font, 40 characters (char `$1780`+) |
| `$5F400–$5FF3F` | 45×64 B | hit and block sparks, 5 frames of 2×3 NCM glyphs (char `$17D0`+) |

Planned (not used yet): effect glyphs, music and samples.

## Colour RAM (`$FF80000`)

| Offset | Use |
|---|---|
| `$0000–$0FFF` | BASIC's colour RAM, never written |
| `$1000–$203F` | colour buffer A (26×160) |
| `$2400–$343F` | colour buffer B (26×160) |

## Attic RAM

| Address | Use |
|---|---|
| `$8000000–$803FFFF` | fighter package 1, Tiago (file `F-TIAGO`, Stage 4: 55 frames, 164,800 bytes); the first byte is also the attic-RAM test cell |
| `$8040000–$807FFFF` | fighter package 2, Konrad (file `F-KONRAD`, Stage 4: 55 frames, 167,488 bytes) |

## VIC-IV configuration

| Register | Value | Meaning |
|---|---|---|
| `$D031` | `$40` | FAST, H320, V200 |
| `$D054` | `$45` (+ PALEMU kept) | CHR16, FCLRHI (chars > $FF are full colour), VFAST |
| `$D058/9` | 160 | LINESTEP |
| `$D05E`/`$D063` | 80 | CHRCOUNT |
| `$D05A` | 120 | CHRXSCL |
| `$D04C/D` | 48 | TEXTXPOS (16 logical px under the left border) |
| `$D04E/F` | 104 | TEXTYPOS (row 0 at the top border) |
| `$D048/9`, `$D04A/B` | 104, 504 | top and bottom border |
| `$D07B` | 25 | display rows (26 rows fetched, the last one under the border) |
| `$D051` | `$00` | RRB double buffering |
| `$D070` | `$00` | palette 0 for editing, text and sprites |

## Palette 0

| Entries | Use |
|---|---|
| 0–175 | arena (0 = black, the background colour) |
| 176–191 | bank 11, hit and block sparks |
| 192–207 | bank 12, fighter 1 |
| 208–223 | bank 13, fighter 2 |
| 224–239 | bank 14, planned: mirror-match palette |
| 240–255 | bank 15, HUD (energy bars) and font |

## RRB row (80 tokens, 160 bytes)

| Tokens | Content |
|---|---|
| 0–41 | background: 2 blank + 40 arena FCM chars (colour `$00,$00`) |
| 42–78 | overlay: fragments (GOTOX + glyph columns; rows 1–4: energy bars, timer, names, round stars; rows 8–11: banners), the rest null GOTOX tokens to x 320 (`$90,$00`) |
| 79 | blank NCM glyph, ends the row at x 336 |

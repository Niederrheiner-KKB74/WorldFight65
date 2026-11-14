# Memory map (Stage 0)

All addresses are 28-bit physical addresses. As in ShooterMega65, the program keeps BASIC's SYS memory map
(RAM below `$C000`, I/O at `$D000`, KERNAL above) and returns to BASIC with X or RUN/STOP.
BASIC's screen RAM, colour RAM `$0000–$0FFF` and RAM below `$2000` are never written.
`$20000–$3FFFF` is ROM and never a data target.

## Used in Stage 0

| Address | Use |
|---|---|
| `$2001–$2010` | BASIC stub `BANK 0:SYS 8224` |
| `$2020–…` | test program (224 bytes); guard: program ends below `$C000` |

## Plan from Stage 1 on (not used yet; every entry is checked and updated when it is built)

### Bank 0

| Address | Use |
|---|---|
| `$2020–$BFFF` | code and tables (state machines, move tables, box tables, input buffers, HUD) |

### Banks 4/5 (chip RAM)

| Address | Size | Use |
|---|---|---|
| `$40000–$4F9FF` | 62.5 KB | arena background, FCM glyphs (≤ 1,000 × 64 bytes), char `$1000`+ |
| `$4FA00–$4FFFF` | 1.5 KB | spare |
| `$50000–$50FFF` | 4 KB | fighter 1, frame slot A |
| `$51000–$51FFF` | 4 KB | fighter 1, frame slot B |
| `$52000–$52FFF` | 4 KB | fighter 2, frame slot A |
| `$53000–$53FFF` | 4 KB | fighter 2, frame slot B |
| `$54000–$55FFF` | 8 KB | effects, projectiles, HUD glyphs (NCM) |
| `$56000–$56F9F` | 25×160 | RRB screen buffer A |
| `$57000–$57F9F` | 25×160 | RRB screen buffer B |
| `$58000–$58F9F` | 25×160 | background part of every row (fixed per arena, copied into the back buffer) |
| `$59000–$5FFFF` | 28 KB | music, sound effects, samples in use; saved BASIC state (as ShooterMega65) |

Colour RAM: the game's colour rows lie above `$0FFF` (exact offsets fixed in Stage 1).

### Attic RAM (`$8000000`+)

| Use |
|---|
| fighter frames (both fighters, all frames, trimmed), arena pictures, title and selection screens, music pieces, samples |

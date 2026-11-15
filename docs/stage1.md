# Stage 1 – Arena and first fighter

Release files are in `releases/stage1/`.

## What it does
- Video set-up for the game: H320/V200, RRB double buffering, settings from ShooterMega65.
- **Arena 1, the beach promenade in Rio de Janeiro** at sunset, drawn by Claude
  (`assets/source/arena_rio.py`): evening sky, the Sugarloaf with its cable car, the sea, the beach with
  umbrellas and a volleyball net, a kiosk, palm trees and the black-and-white wave pavement on which the fight
  takes place. 175 colours, 593 full-colour glyphs.
- **Tiago** (Brazil, capoeira) as the first fighter, drawn with the new skeleton renderer
  (`tools/fighter_art.py`, `assets/source/fighter_tiago.py`): idle (4 frames, ginga-like sway) and walking
  (6 frames, played backwards when walking back). Placeholder quality; the final artwork follows in Stage 4.
- The frames live in **attic RAM** and are copied by DMA into one of two chip-RAM slots whenever the frame
  changes (the slot the shown screen uses is never overwritten).
- **Facing left uses the VIC-IV horizontal flip** (glyph colour byte `$48`, columns in reverse order); only
  right-facing frames are stored.
- Loading: `A-RIO-GFX`, `A-RIO-MAP` and `F-TIAGO` are SEQ files on the disk. Without attic RAM the program
  prints a message and stops.

## Controls
| Input | Action |
|---|---|
| Joystick port 2 left/right | walk (forward = towards the facing direction, 2 px per frame; back 1 px) |
| Fire / key F | turn round (test function for this stage) |
| X or RUN/STOP | back to BASIC |

## Build
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
`--define AUTOTEST` makes a test build with a scripted joystick (walk right, turn, stand facing left), used
for the emulator test.

## Verification so far
| Check | Result |
|---|---|
| Assembly, asset checks (`tools/check_assets.py`), D81 read-back | ✔ |
| XEMU (owner's ROM, headless): normal build | ✔ arena complete, Tiago stands on the pavement at x 96, facing right |
| XEMU: `AUTOTEST` build | ✔ walks right to the edge, turns round, shown mirrored |
| **Real MEGA65** | **open – please test** |

XEMU is not authoritative for RRB rendering and glyph flipping (CLAUDE.md rule 2), so the hardware test
decides.

## Hardware test checklist
1. `LOAD "WORLDFIGHT",8` and `RUN`: after a few seconds of loading the arena appears without stray characters,
   no flickering, correct colours (sunset sky, grey-purple Sugarloaf, white/black pavement).
2. Tiago stands on the pavement left of centre, facing right, and sways gently.
3. Joystick right/left: he walks smoothly; walking backwards plays the steps backwards; he stops at both edges.
4. Fire (or F): he turns round. **Facing left he must look exactly like a mirror image** – no scrambled
   columns, no stripes, no gaps between the 16-pixel columns. This tests the horizontal flip bit.
5. Walk while facing left, also across the palms and the kiosk: no flicker, no holes in the background.
6. X or RUN/STOP: back to `READY.` with the normal BASIC screen and colours; `RUN` works again.

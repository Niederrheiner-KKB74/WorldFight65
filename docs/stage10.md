# Stage 10 – Compression, third fighter Malee

Test builds go to the owner as D81; the release goes to `releases/stage10/` when the stage is confirmed.

## Part 1: compression (test build 10a)
- Format "WZ" (`tools/lzpack.py`, LZ4-like: literal runs and matches with a 16-bit offset); the build packs
  the files and checks the round trip; `src/unpack.asm` unpacks them after loading (32-bit flat pointers,
  attic RAM → attic RAM).

  | File | Before | Packed |
  |---|---|---|
  | F-TIAGO | 181,440 | 64,081 (35 %) |
  | F-KONRAD | 169,920 | 56,879 (33 %) |
  | A-RIO-GFX | 63,744 | 48,002 (75 %) |
  | A-ZOLL-GFX | 64,000 | 45,711 (71 %) |
  | T-TITLE-GFX | 50,560 | 29,111 (58 %) |

  The D81 now holds about 300 KB instead of 600 KB. Maps and music stay unpacked (small).
- Loading: packed files go to `ATTIC_PACK` (`$8700000`) and are unpacked into place; the title is unpacked
  right after the BASIC state is saved (the unpacker uses zero page `$60–$6B`).
- Self-test build `--define AUTOTEST --define AUTOTEST_UNPACK` (with `AUTOTEST_MENU`): sums every unpacked
  region against the original files and shows "READY" (all correct) or "DRAW".

## Part 2: Malee (test build 10b)
- Part 1 (compression) confirmed on hardware by the owner (2026-11-22): loading noticeably shorter.
- Master image (`assets/art/malee/master.png`, normalised from the owner's 1254 px picture; raw in
  `assets/art/source/`) and the arena **Wat Arun, Bangkok** (`assets/art/arena/watarun_source.png`,
  1000 glyphs after merging similar tiles, 41 KB packed).
- `assets/source/fighter_malee.py`: name MALEE, country THAILAND, home arena Wat Arun; health 120 (the
  lightest fighter), walk 4/3; Muay Thai moves (jab, elbow, low kick, roundhouse, flying knee in the air).
  **Until her sprite sheets exist the skeleton renderer draws her** (poses borrowed from Tiago).
- Special move **Khao Loi** (flying knee): quarter circle back (down, down-back, back) + kick - new motion
  "qcb" in the recogniser (lenient like QCF: the diagonal may be skipped); the CPU knows it too.
- Roster of three on the selection screen; mirror matches go through the three arenas in turn.
- Attic RAM: Malee's package at `$8080000`; the pictures moved up to `$8200000+` (frame offsets of the
  fighter packages have 20 bits, so all packages stay in the first MB).

## Status
- Assembled: yes.
- Emulator smoke test (XEMU): self-test "READY" (all five regions identical to the originals); title,
  selection, versus, fight as before; in XEMU "PRESS FIRE" appears about 4 s earlier.
- Part 2 (10b) in XEMU: self-test "READY" for all seven packed regions; Malee (skeleton placeholder) fights
  against the CPU and wins rounds.
- Owner-confirmed on hardware: part 1 yes (2026-11-22); part 2 pending.

## Hardware checklist (part 1, confirmed)
1. Loading: title with "LOADING", then "PRESS FIRE" - how long does it take now (before: ? s)?
2. Both fighters look exactly as before in all animations (no stray pixels, no wrong frames).
3. Both arenas and the title picture look as before.
4. A whole match and the way back to the selection; exit with X.

## Hardware checklist (part 2)
1. Selection: left/right goes through Tiago, Konrad, Malee (name THAILAND); the CPU can be Malee too.
2. Tiago or Konrad against Malee (player 2): versus screen and fight at Wat Arun.
3. Malee (placeholder figure) walks, jumps, attacks; down, down-back, back + button 2 = Khao Loi (dashes
   in, knockdown); key M shows the recogniser (white border when the motion is complete).
4. Mirror matches: Rio, Zollverein, Wat Arun in turn.
5. Loading time and everything else as in part 1.

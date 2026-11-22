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

## Part 2: Malee (follows)
Master image and arena picture from the owner; then the sheets with pose guides and prompts; special move
Khao Loi (flying knee), quarter circle back + kick.

## Status (part 1)
- Assembled: yes.
- Emulator smoke test (XEMU): self-test "READY" (all five regions identical to the originals); title,
  selection, versus, fight as before; in XEMU "PRESS FIRE" appears about 4 s earlier.
- Owner-confirmed on hardware: pending.

## Hardware checklist (part 1)
1. Loading: title with "LOADING", then "PRESS FIRE" - how long does it take now (before: ? s)?
2. Both fighters look exactly as before in all animations (no stray pixels, no wrong frames).
3. Both arenas and the title picture look as before.
4. A whole match and the way back to the selection; exit with X.

# Working rules for WorldFight65

These rules are taken from ShooterMega65 (Stage 19) and adapted. They apply to every change.

1. **Toolchain.** Use KickAssembler 65CE02 5.25 (`KickAss65CE02-5.25.jar`, SHA-256
   `5d8544280dae2d018c79151d8c7b877eca1fb994096e54ca380b26d0cd79f847`) with `.cpu _45gs02`.
   Build only through `python3 tools/build.py`. The jar and the MEGA65 ROM are never committed
   (`tools/bin/` is git-ignored).
2. **Hardware before XEMU.** XEMU is not authoritative for RRB/GOTOX scaling, RRB timing, glyph flipping or
   audio DMA. Graphics and sound changes count as confirmed only after the owner has tested them on real
   MEGA65 hardware. Rules inherited from Vyper and ShooterMega65 (confirmed there on hardware):
   - H320 with `CHRXSCL $D05A = 120`, GOTOX in logical 320-px coordinates.
   - RRB double buffering: `$D051` bit 7 = 0.
   - GOTOX token: screen `X lo, (X hi & 3) | $10 | yoffset<<5`, colour `$90,$00`; NCM glyph colour `$08, pal`.
   - Audio DMA: write `$D72A/$D72B` before `$D72C`; test `$D711` bit 7 only.
   - KERNAL I/O: `SETBNK ($FF6B)` before `SETNAM`.
   - `$20000–$3FFFF` is ROM, never a data target.
   Confirmed in WorldFight65 (Stage 1): FCM background chars (> $FF, colour `$00,$00`) under NCM RRB
   fragments; horizontal glyph flip with colour byte 0 `$48` and reversed column order; frame DMA from attic RAM.
   Stage 2: joystick port 1 via `$DC01` with both CIA1 ports as inputs; button 2 via POT X (`$D620` port 1,
   `$D622` port 2, pressed < `$80`) with 8BitDo pads; files > 64 KB loaded into attic RAM.
   Stage 3: fighters, HUD text and banners sharing rows without glitches; vertically trimmed
   frames with a changing top offset; 256 KB fighter packages in attic RAM.
3. **Memory.** Check `docs/memory_map.md` before using any address and update it in the same change.
   Guard regions with assembler checks (`.errorif` / `.if … .error`).
4. **Stages.** Every test stage ships PRG, D81 and reproducible build instructions in `releases/stageN/`
   and a `docs/stageN.md` with a hardware checklist. When the owner confirms a stage on hardware, it is
   tagged `stageN-stable` and its release folder is not changed again.
5. **Reports.** Keep these separate: assembled, emulator smoke test, owner-confirmed on hardware.
   Never claim hardware success without the owner's confirmation.
6. **Diagnosis first.** Find the cause before making large changes; prefer small, traceable commits.
7. **Reuse.** Port proven modules from `Niederrheiner-KKB74/ShooterMega65` (RRB pixie emitter, system
   save/restore and exit, audio DMA, sound engine, loader, D81/high-score code) and, where they came from,
   `Niederrheiner-KKB74/Vyper_for_Mega65`, into clean modules here. Note the source repository and stage in
   a comment.
8. **Artwork.** Claude draws arenas and screens with scripts in `assets/source/`. Fighters come from sprite
   sheets the owner creates with an image generator (since Stage 4b, owner decision 2026-11-16); Claude checks
   them against `docs/art_import.md` and imports them with `tools/import_fighter.py`. Animations without a
   sheet are drawn by the skeleton renderer. Generated images are checked by `tools/check_*.py` scripts.
9. **Scope.** Two fighters on screen, chosen from loadable fighter packages (Tiago and Konrad first). The engine
   has no fighter-specific code; fighters are data (`docs/design.md` §3.2). Two-player mode comes first; the CPU
   opponent reads the same virtual joystick as a human player and is added later without changing the fighter code.
10. **Docs.** Keep `docs/design.md` (architecture and decisions) and `docs/memory_map.md` current.

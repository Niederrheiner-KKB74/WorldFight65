# Stage 6 – Title, fighter selection, versus screen, music

Test builds go to the owner as D81; the release goes to `releases/stage6/` when the stage is complete.

## What it does (6a/6b, test build 2026-11-19)
- **Game flow** (`src/menu.asm`): title → fighter selection → versus screen → match (best of three) →
  "<NAME> WINS" → back to the selection.
  - **Title:** "WORLDFIGHT 65", blinking "PRESS FIRE" (button 1 or 2, either joystick).
  - **Selection:** each player chooses with left/right and confirms with a button ("READY", win pose).
    Once player 1 is ready, his joystick also chooses for player 2 (solo tests until the CPU opponent).
  - **Same fighter twice:** player 2 gets other colours (made automatically: costume colours turned, white
    and black tinted blue; skin and hair stay).
  - **Versus screen:** names and countries of both fighters, "VS", about 3 seconds.
- All fighter packages are loaded at start (no disk access between the screens).
- **Music** (composed by Claude, `assets/source/compose_music.py`):
  - "Campeonato" – title, selection and versus screen; festive, C major, samba-like bass, loops after ~36 s.
  - "Samba da Briga" – the fight; a samba in D minor (flute-like lead, cavaquinho strums in the partido-alto
    rhythm, surdo, tamborim, samba bass), 125 BPM, loops after ~50 s; stops when the match is won. It
    replaced "Copacabana Clash" after the owner's review (too close to the shooter, should fit Brazil,
    quieter). Both pieces are quieter now (volume 10 title, 9 fight, was 12).
- **Title picture** from the owner's generator picture (`assets/art/title/title_source.png`): 320 × 200,
  175 colours (octree quantiser, keeps Tiago's green belt), 790 glyphs. It lives in attic RAM together with
  the arena picture; switching screens copies the picture into the chip-RAM picture area by DMA.
  Selection and versus screen keep the arena as backdrop.
- **Loading under the title** (owner's wish 2026-11-20, as in Vyper Stage 5d-1): the title picture is loaded
  first and shown with "LOADING" while the KERNAL loads the arena, both fighters and the music (interrupts on,
  no KERNAL output while the title is visible). A load error first switches back to the BASIC screen, then
  prints `CANNOT LOAD <file>` (test build `--define AUTOTEST_LOADFAIL`).
- Fixed after the second hardware test (title skipped at once): every screen starts with all buttons counted
  as held - only a new press after a release counts - and the title ignores the joysticks for its first second.
- Fixed after the first hardware test: no music on the title and the first selection (the sound engine was
  initialised after the title music had been started).

## Build
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
Emulator test builds: `--define AUTOTEST --define AUTOTEST_MENU` (with `AUTOTEST_MENU_T`, `_S`, `_V` for the
title, selection and versus screen), `AUTOTEST_KO` + `AUTOTEST_LONG` (a whole match, then the selection).

## Status
- Assembled: yes.
- Emulator smoke test (XEMU): title, selection (incl. mirror match), versus, fight, match end → selection →
  next match; no crash with both music pieces playing. XEMU audio not judged.
- Owner-confirmed on hardware: pending.

## Hardware checklist
0. Right after RUN the title picture appears with "LOADING" and stays while the rest loads.
1. Title screen: the title picture with "WORLDFIGHT 65" above the globe, "PRESS FIRE" blinks; title music
   plays right from the first start.
2. The title stays until you press fire (button 1 or 2, either port) → selection screen.
3. Left/right changes the fighter (name, country, figure, sound); a button confirms ("READY", win pose).
4. Player 2 chooses with joystick 2; after player 1 is ready, joystick 1 also works for player 2.
5. Both choose the same fighter: player 2 in other colours, in the selection and in the fight.
6. Versus screen with both names and countries, then the fight; the fight music starts.
7. Match won → "<NAME> WINS", music stops → selection with the title music again → next match works.
8. Music: does it fit (title festive, fight a samba)? Volume next to the sound effects? Loops without a jump?
9. X / RUN/STOP leaves the game from every screen, sound off, BASIC fine; RUN again works.

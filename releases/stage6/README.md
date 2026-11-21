# WorldFight65 – Stage 6

Title, fighter selection, versus screen and music. The title picture (owner's generator art) appears right
after RUN with "LOADING" while the rest loads. Title → selection (same fighter twice: player 2 in other
colours) → versus → match (best of three) → selection. Music by Claude: "Campeonato" (title) and
"Samba da Briga" (fight). Sound effects and special moves as in Stage 5.

Mount `WORLDFIGHT65.D81`, then `LOAD "WORLDFIGHT",8` and `RUN`. Needs attic RAM (MEGA65 R3+).
Notes and checklist: `docs/stage6.md`.

Status: assembled, XEMU smoke test, confirmed on real hardware by the owner (2026-11-21).

Build (reproducible from the tagged sources):
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```

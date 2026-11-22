# WorldFight65 – Stage 8

Second arena: Zeche Zollverein in Essen, Konrad's home (owner's generator picture). A match takes place in
the home arena of player 2's fighter; mirror matches alternate. Balancing check with the CPU on both sides
(results in `docs/stage8.md`; values unchanged). Everything from Stage 7 unchanged.

Mount `WORLDFIGHT65.D81`, then `LOAD "WORLDFIGHT",8` and `RUN`. Needs attic RAM (MEGA65 R3+).

Status: assembled, XEMU smoke test, confirmed on real hardware by the owner (2026-11-22).

Build (reproducible from the tagged sources):
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```

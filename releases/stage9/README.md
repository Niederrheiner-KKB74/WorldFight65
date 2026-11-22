# WorldFight65 – Stage 9

Polish: a quiet moment before the round banner, "FINAL ROUND" for round 3, and a winner screen
("CHAMPION", name, country, win pose, fanfare) before the selection. Everything from Stage 8 unchanged.

Mount `WORLDFIGHT65.D81`, then `LOAD "WORLDFIGHT",8` and `RUN`. Needs attic RAM (MEGA65 R3+).
Notes and checklist: `docs/stage9.md`.

Status: assembled, XEMU smoke test, confirmed on real hardware by the owner (2026-11-22).

Build (reproducible from the tagged sources):
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```

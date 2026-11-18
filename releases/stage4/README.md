# WorldFight65 – Stage 4

Final artwork: Tiago (port 1) and Konrad (port 2) with all 55 frames each from the owner's generator
sprite sheets (Stage 4b, imported by `tools/import_fighter.py`), the Rio arena from the owner's generator
picture, hit and block sparks. Blocking by holding back while the opponent attacks nearby (proximity guard),
sparring partner on key T, walk animation driven by the distance walked, hit boxes measured on the art,
fighters clipped at the screen edges.

Mount `WORLDFIGHT65.D81`, then `LOAD "WORLDFIGHT",8` and `RUN`. Needs attic RAM (MEGA65 R3+).
Notes and checklist: `docs/stage4.md`.

Status: confirmed on real MEGA65 hardware by the owner on 2026-11-18 (all animations, moves, blocking,
K.O. at the screen edges, new arena).

Build (reproducible from the tagged sources):
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```

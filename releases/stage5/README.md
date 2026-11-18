# WorldFight65 – Stage 5

Sound effects (sound engine from ShooterMega65 Stage 19) and one special move per fighter:
Tiago's meia-lua de compasso (quarter circle forward + kick) and Konrad's Rammbock shoulder charge
(charge back, then forward + punch), with an input buffer. The specials still use placeholder frames
until the owner's sprite sheets arrive.

Mount `WORLDFIGHT65.D81`, then `LOAD "WORLDFIGHT",8` and `RUN`. Needs attic RAM (MEGA65 R3+).
Notes and checklist: `docs/stage5.md`.

Status: assembled and smoke-tested in XEMU; hardware confirmation by the owner pending.

Build (reproducible from the tagged sources):
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```

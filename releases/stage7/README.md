# WorldFight65 – Stage 7

CPU opponent for player 2 with three levels (easy / normal / hard, chosen with up/down on the selection
screen). It writes only player 2's virtual joystick; joystick 2 takes over the side at any time on the
title or selection screen. Everything from Stage 6 (title, selection, versus, music) is unchanged.

Mount `WORLDFIGHT65.D81`, then `LOAD "WORLDFIGHT",8` and `RUN`. Needs attic RAM (MEGA65 R3+).
Notes and checklist: `docs/stage7.md`.

Status: assembled, XEMU smoke test, confirmed on real hardware by the owner (2026-11-21).

Build (reproducible from the tagged sources):
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```

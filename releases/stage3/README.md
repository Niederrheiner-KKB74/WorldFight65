# WorldFight65 – Stage 3

A complete match: Tiago (port 1) against Konrad (port 2), best of three rounds. Mount `WORLDFIGHT65.D81`,
then `LOAD "WORLDFIGHT",8` and `RUN`. Button 1 = punch, button 2 = kick, forward + button = heavy,
up = jump, down = crouch, back = block. X or RUN/STOP = back to BASIC. Needs attic RAM (MEGA65 R3+).
Notes and checklist: `docs/stage3.md`.

Build (reproducible from the tagged sources):
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```

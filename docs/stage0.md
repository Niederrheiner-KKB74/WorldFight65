# Stage 0 – Toolchain and disk test

Release files are in `releases/stage0/`.

## What it does
- The repository, working rules (`CLAUDE.md`), design (`docs/design.md`) and memory map are in place.
- `tools/build.py` assembles `src/main.asm` with KickAssembler 65CE02 5.25 (SHA-256 checked), writes
  `WORLDFIGHT.PRG` and the disk image `WORLDFIGHT65.D81` and reads the file back from the image.
- The program only prints a short message through the KERNAL, waits for a key and returns to BASIC.
  It does not touch the VIC-IV yet.

## Build
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```

## Start
Mount `WORLDFIGHT65.D81`, then `LOAD "WORLDFIGHT",8` and `RUN` (or `DLOAD "WORLDFIGHT"` / `RUN`).

## Verification so far
| Check | Result |
|---|---|
| Assembly (KickAss65CE02 5.25), PRG < `$C000`, D81 read-back | ✔ |
| Emulator smoke test | not done (no XEMU in the build environment) |
| **Real MEGA65** | **open – please test** |

## Hardware test checklist
1. The disk mounts, and the directory shows the disk name `WORLDFIGHT65` and the file `WORLDFIGHT`.
2. `LOAD "WORLDFIGHT",8` and `RUN` show the message in upper and lower case on a cleared screen.
3. Any key returns to `READY.`; `RUN` works again.

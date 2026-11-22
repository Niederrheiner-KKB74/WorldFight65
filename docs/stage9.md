# Stage 9 – Polish

Release files are in `releases/stage9/` (identical to the test build `WORLDFIGHT65-stage9a.d81`).

## What it does (test build 9a)
- **Pause before the round banner:** each round starts with a moment of quiet (0.7 s), then "ROUND n",
  then "FIGHT!" (the fight starts 0.7 s later than before).
- **"FINAL ROUND"** instead of "ROUND 3" (also for further rounds after draws), with its own sound.
- **Winner screen:** after "<NAME> WINS" in the arena (now 3.4 s instead of 6 s) the winner stands alone in
  the middle of the arena in his win pose with "CHAMPION", name and country; a short fanfare ("Vitória",
  ~8 s, does not loop). After 1.5 s a button leads on ("PRESS FIRE" blinks), otherwise after about 5 s;
  then the selection with the title music.
- Emulator test scripts keep the old intro timing; `AUTOTEST_INTRO` and `AUTOTEST_ROUND3` use the new one.

## Status
- Assembled: yes.
- Emulator smoke test (XEMU): "FINAL ROUND" banner (round 3), winner screen after a match, then the
  selection.
- Owner-confirmed on hardware: **yes** (2026-11-22), pause, fanfare and timing stay as they are.

## Hardware checklist
1. Round start: short pause, then "ROUND 1" / "ROUND 2", then "FIGHT!".
2. Round 3: "FINAL ROUND" with its own sound.
3. After the match: "<NAME> WINS", then the winner screen (winner alone, "CHAMPION", name, country), fanfare.
4. Fire after "PRESS FIRE" appears → selection; without a button the selection comes by itself.
5. Selection with the title music; the next match works. Also when the CPU wins.

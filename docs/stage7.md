# Stage 7 – CPU opponent

Test builds go to the owner as D81; the release goes to `releases/stage7/` when the stage is confirmed.

## What it does
- **Player 2 is the CPU** unless joystick 2 is used: fire on joystick 2 on the title, or any move or button
  on joystick 2 on the selection screen, makes player 2 a human again (header "2P").
- **Selection:** the CPU's header shows its level, "CPU EASY" / "CPU NORMAL" / "CPU HARD". After player 1
  is ready, joystick 1 chooses the CPU's fighter (left/right) and level (up/down) and confirms with a button.
  Default: normal. The choice stays for the next match.
- **How it plays** (`src/cpu.asm`): it only writes player 2's virtual joystick, like a human on joystick 2;
  the fighter code is unchanged. It reads what a player sees: distance, the other fighter's state and move,
  its own state. Move reaches come from the fighter data (`mv_reach`, measured on the artwork), so every
  fighter package works without CPU code of its own.
  - Far away: walks in, sometimes jumps in (jump kick when falling and close), sometimes waits.
  - In reach: attacks with a move that reaches (punches, kicks, crouching attacks, sweep, its special
    move: Tiago's quarter circle, Konrad's charge from a distance), otherwise guards, steps back or walks in.
  - Sees an attack nearby: after a reaction time it blocks with a level-dependent chance, crouching for
    low moves.
  - Other fighter jumps in: anti-air heavy punch or guard. Other fighter on the floor: comes closer and waits.

  | Level | Block chance | Reaction | Pause between actions | Attack chance in reach |
  |---|---|---|---|---|
  | easy | 27 % | 14-29 frames | up to 16 frames | 35 % |
  | normal | 55 % | 8-15 frames | often short | 59 % |
  | hard | 82 % | 3-6 frames | rare | 78 % |

## Build
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
Emulator test builds: `--define AUTOTEST --define AUTOTEST_CPU` (CPU against a mostly passive player 1),
`--define AUTOTEST --define AUTOTEST_MENU_CPU` (selection with "CPU HARD").

## Status
- Assembled: yes.
- Emulator smoke test (XEMU): the CPU walks in, jumps over, attacks, knocks down and wins a round against a
  passive player 1; selection shows and changes the level. Not yet judged: how it feels to play against.
- Owner-confirmed on hardware: pending.

## Hardware checklist
1. Without touching joystick 2: header "CPU NORMAL"; up/down (after player 1 is ready) changes the level.
2. Joystick 2 moved or pressed on the selection screen (or fire on the title): header "2P", two-player game
   as before.
3. Against the CPU: it walks in, attacks, blocks (also low attacks crouching), jumps in, uses its special move.
4. Levels: easy beatable for a beginner, normal a fair fight, hard clearly harder - but not unbeatable?
5. CPU as Tiago and as Konrad; also the mirror match.
6. After the match back to the selection with the CPU still set; the next match works.
7. Key T (sparring) and key M still work; X / RUN/STOP leaves the game.

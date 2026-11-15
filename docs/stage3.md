# Stage 3 – A complete match

Release files are in `releases/stage3/`.

## What it does
- **Crouching** (down): smaller hurt box; crouching punch (button 1), low kick (button 2) and
  **sweep** (down-forward + button 2: Tiago's rasteira, Konrad's leg sweep).
- **Jumping** (up, up-forward, up-back): 40 frames in the air, 60 px high; one **jump attack** per jump
  (button 1: Tiago's jump punch / Konrad's double axe-handle blow; button 2: Tiago's flying kick /
  Konrad's flying knee). Fighters can jump over each other and turn round on landing.
- **Blocking** (hold back): standing or crouching block poses. Attack heights: mid (blockable both ways),
  low (crouching kicks, sweeps and Konrad's stomp kick: block crouching), overhead (jump attacks: block
  standing). A blocked attack does no damage, causes half the hitstun and pushes back.
- **Knockdown:** sweeps and every hit on a fighter in the air knock him down; he falls (also from the air),
  lies on the floor, gets up and is invulnerable meanwhile.
- **KO:** the loser falls and stays down ("K.O."); the winner strikes his **win pose** (Tiago raises both
  arms, Konrad flexes).
- **Rounds:** "ROUND n", "FIGHT!", 99-second timer, "TIME" (more energy wins, equal = "DRAW"), best of three
  rounds with a star per won round, "<NAME> WINS", then a new match.
- **HUD:** energy bars, timer, the fighters' names; the new 16×16 arcade font (40 characters) is drawn by
  Claude in `tools/make_assets.py`.
- 19 animations per fighter (55 frames each); frames are now also trimmed at the top.

## Controls (both pads)
| Input | Standing | Crouching | In the air |
|---|---|---|---|
| Button 1 | light punch (forward: heavy punch) | crouching punch | jump punch |
| Button 2 | light kick (forward: heavy kick) | low kick (forward: sweep) | jump kick |
| Up / up-forward / up-back | jump | – | – |
| Back | walk back, block | crouching block (down-back) | – |

X or RUN/STOP: back to BASIC. P: POT X diagnosis in the border (from Stage 2).

## Build
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
Emulator test builds: `--define AUTOTEST` (sweep and knockdown) plus optionally `--define AUTOTEST_INTRO`
("ROUND 1"), `AUTOTEST_JUMP` (flying kick), `AUTOTEST_BLOCK` (Konrad blocks a heavy punch) or `AUTOTEST_KO`
(Tiago kicks until KO).

## Verification so far
| Check | Result |
|---|---|
| Assembly, asset checks, D81 read-back | ✔ |
| XEMU `AUTOTEST_INTRO` | ✔ "ROUND 1", timer 99, names, full bars |
| XEMU `AUTOTEST` | ✔ sweep hits, Konrad lies on the floor, his bar is down by 12 |
| XEMU `AUTOTEST_JUMP` | ✔ flying kick in the air hits Konrad's head |
| XEMU `AUTOTEST_BLOCK` | ✔ Konrad blocks Tiago's heavy punch, no damage |
| XEMU `AUTOTEST_KO` | ✔ "K.O.", Konrad down at the edge, Tiago in his win pose |
| XEMU: rounds 2/3, "WINS", time up, getting up, crouching block of a low attack | not tested (needs real input or longer runs) |
| **Real MEGA65** | **open – please test** |

## Hardware test checklist
1. Start: "ROUND 1", then "FIGHT!"; timer 99 between the bars, names TIAGO and KONRAD below. No flicker,
   no stray characters; the font is readable (yellow to orange with a dark outline).
2. The timer counts down once per second.
3. Crouch (down) and the three crouching attacks of both fighters; the sweep knocks down.
4. Jump straight up, forwards and backwards; jump over the opponent: both turn round after landing.
   Jump punch and jump kick, one per jump; a hit in the air knocks the opponent down.
5. Knocked down: the fighter falls, lies about a second, gets up; hits during this time do nothing.
6. Block: hold back while the opponent attacks – standing against punches and jump attacks, crouching
   (down-back) against the sweep, the low kicks and Konrad's stomp kick. Blocked: no energy lost.
   Blocking low against a jump attack, or standing against a sweep, must fail.
7. KO: "K.O.", the loser falls and stays down, the winner shows his win pose; a star appears for the
   winner; "ROUND 2" starts with full bars.
8. Let the timer run out: "TIME" (or "DRAW" at equal energy), the fighter with more energy wins the round.
9. After two won rounds: "<NAME>" / "WINS" for about 6 seconds, then a new match with "ROUND 1" and no stars.
10. X or RUN/STOP: back to BASIC as before.

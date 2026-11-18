# Stage 5 – Sound effects and special moves

Release files are in `releases/stage5/`.

## What it does
- **Sound engine** from ShooterMega65 Stage 19 (`src/sound.asm`, `tools/build_music.py`), file `MUSIC` at
  `$A000`. Effects on SID 2 (mirrored to SID 4), defined in `music/sfx.json`:
  swing light / heavy when an attack starts, jump, landing, hit light / heavy (heavy from 10 damage), block,
  thud when a knocked-down fighter hits the floor, K.O., "FIGHT!" and the special-move sound.
- **Special moves**, one per fighter (data in the fighter module, no fighter-specific code):

  | Fighter | Special | Input (facing right) | Damage | Effect |
  |---|---|---|---|---|
  | Tiago | Meia-lua de compasso | down, down-right, right + **button 2** (kick) | 16 | dashes in, knockdown |
  | Konrad | Rammbock (shoulder charge) | hold **left** (or down-left) ~1 s, then right + **button 1** (punch) | 18 | charges in, knockdown |

  Facing left the directions are mirrored. The motion may be entered while another attack or a hitstun is
  still running (input buffer). Both specials can be blocked standing (they hit mid).
- **Placeholder art:** the specials still show frames of Tiago's high kick and Konrad's forearm smash. Pose
  guides `assets/art/guides/*_sp1_guide.png` and prompts `docs/art_prompts_special.md` are ready for the
  owner's sheets (4 cells each).
- **Sparring partner** (key T): his sequence now ends with his special move (Konrad's charge crouches
  down-back for ~1 s first).

## Build
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
Emulator test builds: `--define AUTOTEST --define AUTOTEST_QCF` (Tiago's special) or `AUTOTEST_CHARGE`
(Konrad's), each with `--define AUTOTEST_LATE` for the moment after the knockdown.

## Status
- Assembled: yes.
- Emulator smoke test (XEMU): both specials start, dash in, hit and knock down; no crash with the sound
  engine. XEMU audio was not judged (not authoritative).
- Owner-confirmed on hardware: **pending**.

## Hardware checklist
1. "FIGHT!" sound at the start of each round.
2. Swing sounds: light attacks a short hiss, heavy attacks a longer one.
3. Jump and landing sounds.
4. Hit sounds: light hits a short knock, heavy hits (hp, hk, jump kick, sweep, specials) a deeper one.
5. Block sound (hold back while being attacked).
6. Thud when a knocked-down fighter lands; K.O. sound at the end of a round.
7. Sound stops when leaving the game (RUN/STOP + RESTORE path as before) and BASIC is fine afterwards.
8. Tiago: down, down-forward, forward + button 2 → meia-lua de compasso (placeholder: high kick frames),
   dashes in, knocks Konrad down; special sound on start.
9. Konrad: hold back ~1 s, then forward + button 1 → Rammbock (placeholder: forearm smash frames), charges
   in, knocks Tiago down. Also from down-back (crouching charge).
10. Both specials are blocked by holding back; the attacker stops dashing when blocked.
11. Normal heavy punch / heavy kick (forward + button) still come out when no motion was entered.
12. Sparring partner (T): the special appears at the end of his sequence for both players.
13. Are the motions easy enough to enter with the 8BitDo pad? (QCF windows 12 frames, charge 40 frames.)

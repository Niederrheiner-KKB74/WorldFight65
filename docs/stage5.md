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
- **Lenient input** (after the owner's hardware report 2026-11-19 that no special came out): the QCF may skip
  the diagonal (down, then forward within 12 frames); the charge window (14 frames) opens as soon as back is
  released, so passing through neutral on the pad no longer loses the charge; the button is buffered for
  6 frames; a button pressed a moment too early (e.g. kick at down-forward, which starts the sweep) is turned
  into the special when the motion is finished in the attack's first frame.
- **Key M** (test aid): the border shows the recogniser of both fighters - yellow = charged (Konrad has held
  back long enough), cyan = QCF down-forward reached, white = motion complete, press the button now.
- **Artwork:** both specials come from the owner's generator sheets (`assets/art/<f>/sp1.png`, 4 cells,
  2026-11-19; raw files in `assets/art/source/`). Tiago's cells are shown as 1, 2, 3, 3, 4 (the heel in
  front is the active frame), Konrad's as 1, 2, 2, 3, 4. Hit boxes are measured on the art: Tiago's heel
  at 56-65 px, Konrad's fists/shoulder at 46-74 px above the floor.
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
- Emulator smoke test (XEMU): both specials start (also with an early kick at down-forward and with the
  charge released through neutral), dash in, hit and knock down; no crash with the sound
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
8. Tiago: down, down-forward, forward + button 2 → meia-lua de compasso ,
   dashes in, knocks Konrad down; special sound on start.
9. Konrad: hold back ~1 s, then forward + button 1 → Rammbock , charges
   in, knocks Tiago down. Also from down-back (crouching charge).
10. Both specials are blocked by holding back; the attacker stops dashing when blocked.
11. Normal heavy punch / heavy kick (forward + button) still come out when no motion was entered.
12. Sparring partner (T): the special appears at the end of his sequence for both players.
13. Key M: does the border turn yellow / cyan / white while entering the motions?
14. Are the motions easy enough to enter with the 8BitDo pad? (QCF steps 12 frames, button 14 frames after forward; charge 40 frames, then 14 frames.)

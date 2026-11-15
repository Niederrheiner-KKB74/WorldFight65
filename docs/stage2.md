# Stage 2 – Tiago against Konrad

Release files are in `releases/stage2/`.

## What it does
- **Konrad** (Germany, wrestling) joins Tiago: heavy build, black singlet with a red stripe, red wrestling
  shoes, blond hair and beard (`assets/source/fighter_konrad.py`). The skeleton renderer now draws any
  costume (zones for skin, torso, pelvis, thighs, shins, feet; belt, singlet neckline, stripe, beard).
- **Two players:** Tiago on joystick port 1, Konrad on port 2. Both fighters always face each other.
- **Attacks** (two-button scheme): button 1 = light punch, forward + button 1 = heavy punch,
  button 2 = light kick, forward + button 2 = heavy kick.
  - Tiago: open-hand jab, rear-hand strike, ponteira (snap kick), martelo (high roundhouse kick).
  - Konrad: jab, forearm smash, stomp kick, knee strike. Konrad walks slower but hits harder.
- **Hits:** hit boxes on the active frames of every attack (taken from the striking hand, foot or knee of
  the pose), hurt box per fighter, damage, 6 frames of hitstop, hitstun with a hit animation, pushback
  (at the screen edge the attacker is pushed back instead). An attacking fighter is drawn in front.
- **Push boxes:** the fighters cannot walk through each other (36 px between their anchors).
- **Energy bars** at the top (RRB fragments with 17 bar glyphs); player 2's bar is the mirrored version
  and empties towards the centre as well.
- **KO:** at 0 energy the loser slides back and stays frozen in the last frame of his hit animation
  (there is no knockdown animation yet); after 3 seconds a new round starts with full energy. Falling to the
  floor, getting up, rounds, timer and win poses follow in Stage 3.
- Each fighter package (`F-TIAGO`, `F-KONRAD`) is loaded into its own 128 KB area of attic RAM; the loader
  can now load files larger than 64 KB.
- Key **P**: shows the POT X reading of joystick port 2 as the border colour (diagnosis for button 2).

## Build
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
`--define AUTOTEST` makes the emulator test build: scripted joysticks (Tiago walks in, light punch;
Konrad knee strike; Tiago martelo), frozen during Tiago's kick.

## Verification so far
| Check | Result |
|---|---|
| Assembly, asset checks, D81 read-back | ✔ |
| XEMU, normal build | ✔ arena, both fighters facing each other, both energy bars full |
| XEMU, `AUTOTEST` build | ✔ all three attacks hit; energy bars down by 18 (Tiago) and 22 (Konrad = jab 6 + martelo 16); attacker drawn in front |
| XEMU: KO and next round, pushback at the edge, button 2 via POT | not tested (needs real input) |
| **Real MEGA65** | **✔ confirmed by the owner (2026-11-15) with 8BitDo pads: works as described, including button 2 via POT X. Noted: at a KO the loser does not fall to the floor (no knockdown animation yet, planned for Stage 3).** |

## Hardware test checklist
1. Start: arena, Tiago left facing right, Konrad right facing left, two full yellow energy bars at the top.
   No flicker, no stray characters, correct colours (Konrad: black singlet, red stripe and shoes).
2. Joystick 1 moves Tiago, joystick 2 moves Konrad. Walking towards each other, they stop when they meet
   and cannot pass through each other; they always face each other.
3. **Button 1** (both pads): light punch; with the stick held towards the opponent: heavy punch.
4. **Button 2** (both pads): light kick; with forward: heavy kick. If button 2 does nothing (or kicks
   all the time): press P and watch the border colour while pressing button 2 on the pad in **port 2**;
   please tell me whether the colour changes and in which direction (dark/light). Press P again to stop.
5. Hits: a short freeze, the hit fighter recoils and slides back, the energy bar shrinks from the centre.
   Missed attacks (too far away) do nothing.
6. Push a fighter into the screen edge with hits: he stops at the edge, the attacker is pushed back.
7. KO: when a bar is empty, the loser slides back and freezes (no fall yet); after 3 seconds both start again
   with full bars.
8. Overlapping fighters (during attacks): no holes, no flicker, the attacker in front.
9. X or RUN/STOP: back to `READY.`, BASIC screen and colours normal, both joysticks still work in BASIC
   (e.g. with a game started afterwards).

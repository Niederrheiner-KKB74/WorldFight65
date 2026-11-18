# Stage 4 – Final artwork

Release files are in `releases/stage4/`. Game mechanics, controls and hit boxes are unchanged from Stage 3.

## What it does
- **New fighter renderer** (`tools/fighter_art.py`): tapered limbs with muscle bulges instead of capsules,
  shaped torso, faces in profile (nose, ear, eye, brow, mouth), light from the front and the top, a warm rim
  of sunset light on the skin, dark outline. After the owner's review: parts of the same material are merged
  and shaded as one area (an arm, a trouser leg with the pelvis, the singlet with torso, pelvis and thighs),
  and no edges are drawn where a limb grows out of the body, so arms and legs no longer look stuck on.
  Feet and shoes have a real shape in profile (flat sole on the floor, heel, rounded toes, instep), and wide
  trouser legs end above the ankle instead of reaching under the foot. The head turns with the neck: a
  falling or lying fighter looks up and backwards instead of having an upright head on a lying body.
  Heads are real profiles instead of balls: a cranium with a flat back of the head (no deeper than the
  face is long), flat forehead, brow, nose, lips, a protruding chin and an angular jaw, with a hairline
  running from the forehead down to the nape; curls add volume on top only.
- **Tiago:** bare, muscular torso with chest and belly lines, curly black hair, wide white capoeira trousers
  with folds, green-and-yellow cord belt (cordão) with knot and tassels, bare feet. Livelier ginga in the
  idle animation; the rear-hand strike now crosses in front of the body; new win pose **seen from the
  front** (fist raised, other hand on the hip, cheering).
- **Konrad:** broad build (after the owner's first look: flatter back and shoulders closer together in
  profile, so his bent-forward stance no longer looks like a hump or a rucksack; slimmer lower legs; hip joints
  closer together and slimmer thighs, so his seat no longer sticks out), black singlet with black-red-gold side-seam stripes on torso and thighs, bare
  shoulders, red wrestling shoes with laces and sole, a military buzz cut (very short on top, sides shaved with
  stubble) and a blond beard; new win pose **seen from the front** (double biceps).
- **Facial expressions:** eyes shut and mouth open when hit or falling, open mouth in the win pose.
- **Sparks:** yellow-white star burst at the point where a hit lands, blue shield arc on a block
  (palette bank 11); they keep playing while the fighters freeze in the hitstop.

## Build
```
python3 tools/build.py --kickass /path/to/KickAss65CE02-5.25.jar
```
Emulator test builds as in Stage 3 (`--define AUTOTEST` plus `AUTOTEST_INTRO`, `AUTOTEST_JUMP`,
`AUTOTEST_BLOCK` or `AUTOTEST_KO`). Preview sheets of all frames: `build/preview/tiago.png`,
`build/preview/konrad.png`, `build/preview/effects.png`.

## Verification so far
| Check | Result |
|---|---|
| Assembly, asset checks, D81 read-back | ✔ |
| XEMU `AUTOTEST` (sweep) | ✔ new artwork, Konrad on the floor |
| XEMU `AUTOTEST_JUMP` | ✔ flying kick with the hit spark at Konrad's head |
| XEMU `AUTOTEST_BLOCK` | ✔ blue block spark at Konrad's guard, no damage |
| XEMU `AUTOTEST_KO` | ✔ "K.O.", Tiago's new win pose |
| **Real MEGA65** | **open – please test** |

## Hardware test checklist
1. Both fighters look as in the preview: Tiago with curly hair, folds in the white trousers, cord belt;
   Konrad with the black-red-gold stripes, red shoes and beard. No stray pixels, no wrong colours,
   no gaps between the 16-pixel columns (also facing left).
2. All moves from Stage 3 still work the same way (the hit boxes are unchanged).
3. A hit shows a yellow star burst at the point of impact, a block a blue arc; both disappear after a
   fraction of a second. Also check a hit in the air and a sweep (spark near the floor).
4. Hit and falling fighters close their eyes; the winner turns to the front for his win pose (Tiago:
   fist up, Konrad: double biceps).
5. Everything else as in Stage 3 (rounds, timer, KO, exit to BASIC).

## Stage 4b test builds (generator artwork, not a release yet)

- Fighters partly from the owner's generator sheets (`docs/art_import.md`, `docs/art_prompts.md`).
- Blocking: hold back while the opponent attacks nearby -> block pose (down-back: crouching block).
- Key **T**: sparring partner - player 2 (border red), then player 1 (border blue) attacks by himself; once
  more T = off. Test on hardware: hold back / down-back against his attacks; low attacks (crouching kick,
  sweep) must be blocked crouching, jump attacks standing.
- Emulator check: `--define AUTOTEST --define AUTOTEST_SPAR` (standing guard) and
  `... --define AUTOTEST_SPAR_LOW` (crouching guard) freeze in the guard pose.

## Result (2026-11-18)

Confirmed by the owner on real MEGA65 hardware: all fighter animations and moves of Tiago and Konrad
from the generator art (idle, walk, block, crouch, standing and crouching attacks, sweep with fall and
get-up, jump and jump attacks, hit, K.O., win), blocking with back / down-back, the sparring partner,
the K.O. at the left and right screen edge (fighter stays visible), the generator arena.
Release: `releases/stage4/` (SHA-256 in `SHA256SUMS.txt`); tag `stage4-stable` is set by the owner.

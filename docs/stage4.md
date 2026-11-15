# Stage 4 – Final artwork

Release files are in `releases/stage4/`. Game mechanics, controls and hit boxes are unchanged from Stage 3.

## What it does
- **New fighter renderer** (`tools/fighter_art.py`): tapered limbs with muscle bulges instead of capsules,
  shaped torso, faces in profile (nose, ear, eye, brow, mouth), light from the front and the top, a warm rim
  of sunset light on the skin, dark outline.
- **Tiago:** bare, muscular torso with chest and belly lines, curly black hair, wide white capoeira trousers
  with folds, green-and-yellow cord belt (cordão) with knot and tassels, bare feet. Livelier ginga in the
  idle animation; the rear-hand strike now crosses in front of the body; new win pose (fist raised, other
  hand on the hip).
- **Konrad:** broad build (after the owner's first look: flatter back and shoulders closer together in
  profile, so his bent-forward stance no longer looks like a hump or a rucksack; slimmer lower legs), black singlet with black-red-gold side-seam stripes on torso and thighs, bare
  shoulders, red wrestling shoes with laces and sole, blond crew cut and beard; new win pose (double biceps).
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
4. Hit and falling fighters close their eyes; the winner shows his new win pose.
5. Everything else as in Stage 3 (rounds, timer, KO, exit to BASIC).

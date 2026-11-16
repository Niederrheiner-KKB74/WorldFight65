# Generator prompts for the fighter sprite sheets

Lessons from Stage 4b (idle, walk, block): the generator keeps colours and scale best when it **edits the
attached idle image** instead of drawing from scratch; it enlarges small figures (crouching) to fill the cell
unless told not to; it ignores exact pixel distances but keeps relative rules ("as wide as …", "the back foot
stays where it is"). Sizes and foot lines that are slightly off are corrected by `tools/normalize_sheet.py`;
wrong colours and wrong scale cannot be corrected. Hit boxes are fitted to the delivered art afterwards.

How to use:

1. One animation per request. Attach the fighter's idle sheet (or only its first cell) and, where named
   below, an already approved sheet as a second reference.
2. Prompt = **base prompt** + **character block** + **animation block**, all in one message.
3. Check before sending it on: right number of figures, figure the same size as in the idle sheet,
   colours unchanged, no pink on the figure.

## Base prompt

```
Edit the attached idle sprite: keep the character exactly as he is - the same face, hair, body, costume,
the same colours, the same pixel-art style and the same scale. Only the pose changes, as described below.

Output: one sprite sheet, a single row of {N} square cells of exactly 256 x 256 px (image {N*256} x 256 px).
Solid flat magenta background #FF00FF, no gradient, no shadow, no ground line, no text, no frame numbers.
No magenta, pink or purple anywhere on the character.
The character faces right in every cell. Soles on one common line: the lowest pixel of a foot on the
ground is at y = 239 (16 px above the bottom of the cell). The character is exactly as big as in the
idle sprite (standing: 224 px from soles to top of head) - never enlarge or shrink him to fit the cell.
In standing poses the back foot stays where it is in the idle sprite; the cell is wide enough for
punches and kicks to the right. Nothing may be cut off at the cell edges.
```

## Character blocks

Konrad:
```
Character: Konrad, a muscular German Greco-Roman wrestler with a very short blond buzz cut and a short
beard; black singlet with a black-red-gold side stripe, white socks, red wrestling shoes with white stripes.
Heavy, powerful, grounded movements.
```

Tiago:
```
Character: Tiago, an athletic Brazilian capoeira fighter with dark braided hair, bare-chested, white
capoeira trousers, a green and yellow cord belt with tassels, barefoot.
Light, springy, flowing movements.
```

## Animation blocks

Frame counts are fixed by the game (`assets/source/fighter_<name>.py`). In attacks, frame 2 is the moment of
the hit: arm or leg fully extended.

| Sheet | Frames | Second reference |
|---|---|---|
| `crouch` | 1 | `c_block` |
| `lp`, `hp`, `lk`, `hk` | 3, 4, 3, 4 | – |
| `c_lp`, `c_lk`, `sweep` | 3, 3, 4 | `crouch` |
| `hit` | 2 | – |
| `jump`, `j_p`, `j_k` | 3, 3, 3 | for `j_p`, `j_k`: `jump` |
| `fall`, `getup` | 3, 2 | – |
| `win` | 2 | – |

**crouch** (1)
```
Animation: crouch, 1 frame. Deep crouch with the guard up (fists in front of the chin), as in the attached
crouching-block sprite but with the forearms lowered. Same scale as standing: crouching he is only about
150 px from soles to top of head; the upper part of the cell stays empty magenta.
```

**lp** – Konrad: jab, Tiago: open-hand jab (3)
```
Animation: light punch, 3 frames. 1: the front fist starts forward. 2: front arm fully extended at head
height, the fist reaches about 80 px in front of the chest (near x = 205). 3: the arm comes back halfway
to the guard.
```

**hp** – Konrad: forearm smash, Tiago: rear-hand strike (4)
```
Animation: heavy punch, 4 frames. 1: wind-up, the rear arm drawn back, body turned. 2: rear arm fully
extended at chest height with the whole body behind it, reaching about 85 px in front of the chest
(Konrad: a horizontal forearm smash). 3: follow-through. 4: back towards the guard.
```

**lk** – Konrad: stomp kick (low), Tiago: ponteira (front kick, middle) (3)
```
Animation: light kick, 3 frames. 1: the front knee comes up. 2: [Konrad: a short stomp kick forward
and down, the sole at shin height of the opponent, about 80 px in front of the body]
[Tiago: a straight front kick, the ball of the foot at stomach height, about 110 px in front of the body].
3: the leg comes back, foot towards the floor.
```

**hk** – Konrad: knee strike, Tiago: martelo (roundhouse kick, head height) (4)
```
Animation: heavy kick, 4 frames. 1: wind-up. 2: [Konrad: a powerful knee strike forward at stomach height,
hands pulling the imaginary opponent's head down] [Tiago: martelo, a roundhouse kick with the instep at
head height, the leg fully extended about 120 px in front of the body, the supporting foot turned].
3: the leg comes back. 4: returning to the guard.
```

**c_lp** (3), **c_lk** (3), **sweep** (4)
```
Animation: crouching light punch, 3 frames, from the attached crouch pose and at its scale (about 150 px
high). 1: start. 2: front arm fully extended forward at stomach height of a standing opponent. 3: back.
```
```
Animation: crouching light kick, 3 frames, from the attached crouch pose and at its scale. 1: start.
2: the front leg kicks forward low along the floor, the foot at ankle height, about 110 px in front
of the body. 3: back.
```
```
Animation: sweep, 4 frames, from the attached crouch pose and at its scale. [Tiago: rasteira - he drops
low, one hand on the floor, the extended front leg sweeps along the floor.] [Konrad: a low leg sweep with
the extended front leg along the floor.] 1: drop down. 2: leg fully extended along the floor, about
110 px in front of the body. 3: the leg sweeps back. 4: back into the crouch.
```

**hit** (2)
```
Animation: getting hit, 2 frames. 1: head snapped back, upper body bent backwards, face in pain, guard
broken, feet still on the floor. 2: recovering halfway towards the guard.
```

**jump** (3), **j_p** (3), **j_k** (3)
```
Animation: jump, 3 frames. 1: take-off, knees bent, both feet on the floor line. 2: in the air, knees
tucked, fists up; draw him at the height of a standing figure (top of the head near y = 16) - the legs
are tucked, so the feet end far above the floor line (around y = 190). The game moves the sprite up and
down. 3: landing, knees bent, both feet on the floor line.
```
```
Animation: jumping punch, 3 frames, all in the air at the height of frame 2 of the attached jump sprite.
1: the tucked pose of the jump. 2: front arm punching forward and down, fully extended. 3: tucked again.
```
```
Animation: jumping kick, 3 frames, all in the air at the height of frame 2 of the attached jump sprite.
1: the tucked pose of the jump. 2: one leg kicking forward and down, fully extended, about 110 px in front
of the body. 3: tucked again.
```

**fall** (3), **getup** (2)
```
Animation: knocked down, 3 frames. 1: hit hard, thrown backwards, feet leaving the floor. 2: falling on his
back in mid-air, body almost horizontal, lowest pixel around y = 230. 3: lying flat on his back on the
floor (lowest pixel at y = 239), head to the left, about 70 px high and up to 250 px long.
Same scale as standing - do not enlarge.
```
```
Animation: getting up, 2 frames. 1: sitting up / on one knee, a hand on the floor. 2: almost standing,
knees bent, guard coming up.
```

**win** (2)
```
Animation: victory pose, 2 frames, facing the viewer or three-quarter view. [Konrad: double-biceps pose,
fists at head height.] [Tiago: a proud capoeira pose, one fist raised.] Raised fists may reach the top edge
of the cell but must not be cut off: keep the top of the head at y = 16 as in the idle sprite.
1 and 2 differ slightly (breathing, smile).
```

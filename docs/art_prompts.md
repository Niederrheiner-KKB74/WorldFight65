# Generator prompts for the fighter sprite sheets

Lessons from Stage 4b (idle, walk, block): the generator keeps colours and scale best when it **edits the
attached idle image** instead of drawing from scratch; it enlarges small figures (crouching) to fill the cell
unless told not to; it ignores exact pixel distances but keeps relative rules ("as wide as …", "the back foot
stays where it is"). Sizes and foot lines that are slightly off are corrected by `tools/normalize_sheet.py`;
wrong colours and wrong scale cannot be corrected. Hit boxes are fitted to the delivered art afterwards.

Lessons from the first round (owner, 2026-11-16): sheets made from *different* starting images drift apart
(Tiago's walk narrower and brighter, Konrad's singlet grey instead of black, frame 2 of the idle sheets
bigger than the others - visible as "pulsing"). Therefore every sheet starts from one master image.

How to use:

1. **Master first.** Generate a single standing pose per fighter (one 256 x 256 cell, guard up, the
   character exactly as he should look in the game) with the master prompt below. When it is approved it is
   stored as `assets/art/<fighter>/master.png`; nothing else defines the character.
2. **Every sheet is an edit of the master** - also idle and walk. Attach `master.png` (and, where named
   below, an already approved sheet for the pose), never an older sheet alone.
3. One animation per request. Prompt = **base prompt** + **character block** + **animation block**.
4. Before a sheet goes into the game, `python3 tools/check_sheets.py <fighter> <sheet.png>` compares it with
   the master: format, frame count, foot line, height, torso width, colours, brightness, magenta, and for idle
   the jitter between the frames. It also writes an overview `build/preview/check_<fighter>.png`.

## Master prompt

```
Pixel-art character for a 2D fighting game in the style of Street Fighter II: one single sprite in a
256 x 256 px cell, solid flat magenta background #FF00FF, no shadow, no ground line, no text.
{character block}
Standing fighting stance in side view facing right (body turned sideways, the left shoulder towards the
viewer is the rear one, the front shoulder points to the right - not turned towards the viewer), guard up
(both fists in front of the chest), knees slightly bent in a springy stance, feet about shoulder-width apart
one behind the other, compact: the figure is at most 135 px wide.
Proportions like classic Street Fighter II sprites: slightly larger head, hands and feet than realistic,
broad shoulders, so the face and fists stay readable when the sprite is shown only about 100 px tall. Soles at y = 239 (16 px above the bottom of the cell),
top of the head at y = 16, so the figure is 224 px tall. Clean pixel art with dark outlines, at most about
24 colours, no anti-aliasing against the background, no magenta, pink or purple on the character.
```

## Base prompt

```
Edit the attached master sprite: keep the character exactly as he is - the same face, hair, body, costume,
the same colours, the same pixel-art style and the same scale. Only the pose changes, as described below.

Output: one sprite sheet, a single row of {N} square cells of exactly 256 x 256 px (image {N*256} x 256 px).
Solid flat magenta background #FF00FF, no gradient, no shadow, no ground line, no text, no frame numbers.
No magenta, pink or purple anywhere on the character.
The character faces right in every cell. Soles on one common line: the lowest pixel of a foot on the
ground is at y = 239 (16 px above the bottom of the cell). The character is exactly as big as in the
master sprite (standing: 224 px from soles to top of head) - never enlarge or shrink him to fit the cell.
In standing poses the back foot stays where it is in the master sprite; the cell is wide enough for
punches and kicks to the right. Nothing may be cut off at the cell edges.
```

## Character blocks

Konrad:
```
Character: Konrad, a muscular German Greco-Roman wrestler with a very short blond buzz cut and a short
beard; black singlet with a black-red-gold side stripe, white socks, red wrestling shoes with white stripes.
He is clearly the heavier and more massive of the two fighters: very broad chest and shoulders, thick neck,
thick arms and thighs, wide stable stance - a heavyweight wrestler, noticeably bulkier than a slim martial
artist, but exactly as tall as the other fighters. Heavy, powerful, grounded movements.
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
| `idle` | 4 | – |
| `walk` | 6 | – |
| `block`, `c_block` | 1, 1 | for `c_block`: `crouch` |
| `crouch` | 1 | – |
| `lp`, `hp`, `lk`, `hk` | 3, 4, 3, 4 | – |
| `c_lp`, `c_lk`, `sweep` | 3, 3, 4 | `crouch` |
| `hit` | 2 | – |
| `jump`, `j_p`, `j_k` | 3, 3, 3 | for `j_p`, `j_k`: `jump` |
| `fall`, `getup` | 3, 2 | – |
| `win` | 2 | – |

**idle** (4) - generated (owner's choice, 2026-11-17: the generator idle looks better than the breathing
drawn by `tools/make_idle.py`, which stays available as a fallback). Konrad's approved idle sheet is in
`assets/art/source/konrad_idle_raw.png`; it moves very little (head 1 px), which the owner accepts.

**walk** (6)
```
Animation: forward walk cycle, 6 frames, looping (frame 6 leads back into frame 1), walking in place like a
game sprite. Head and torso stay at the same position in all frames (at most 2 px variation); same torso
width as in the master in every frame. Only the legs move: frames 1 and 4 are the contact poses (one foot
forward, the other back, feet about one and a half foot lengths apart), frames 2-3 and 5-6 the passing
poses. The guard stays as in the master. [Konrad: short, heavy steps.] [Tiago: light, springy steps.]
```

**block** (1), **c_block** (1)
```
Animation: standing block, 1 frame. Same stance as the master, forearms raised in front of the face, chin
down.
```
```
Animation: crouching block, 1 frame, from the attached crouch sprite and at its scale (about 150 px from
soles to top of head; the upper part of the cell stays empty magenta). Forearms raised in front of the face.
```

**crouch** (1)
```
Animation: crouch, 1 frame. Deep crouch with the guard up (fists in front of the chin). Same scale as
standing: crouching he is only about 150 px from soles to top of head; the upper part of the cell stays
empty magenta. Do not enlarge him to fill the cell.
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
of the cell but must not be cut off: keep the top of the head at y = 16 as in the master sprite.
1 and 2 differ slightly (breathing, smile).
```

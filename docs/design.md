# WorldFight65 – Technical Design

Status: Stage 4. This document is the plan. Everything below that has not been built and tested on hardware is
marked **(planned)** or **(to verify)**. Decisions are logged in §12.

## 1. Game summary
- One-on-one fighting game, static arena backgrounds (no scrolling). Two fighters are on screen; they are
  chosen from a roster of loadable fighters (§3.2), starting with **Tiago** (Brazil, capoeira) and
  **Konrad** (Germany, wrestling).
- Mode 1: two players, joysticks in port 1 and port 2. Mode 2 (later): one player against the CPU.
- Best of three rounds, 99-second round timer (counted in game seconds), KO or time-over decides a round.
- Each fighter: walking, jumping (up, forward, back), crouching, blocking (hold away from the opponent),
  light and heavy attacks standing, crouching and in the air, throws (optional, late), two to three special
  moves each, one of them a projectile.
- Both players may choose the same fighter (mirror match); the second one then uses an alternative palette.
- Stage 3 controls: up = jump (up-forward / up-back: jump in that direction), down = crouch, holding back =
  block. Standing: button 1 punch, button 2 kick, with forward heavy. Crouching: button 1 crouching punch,
  button 2 low kick, down-forward + button 2 sweep. In the air: one jump punch or jump kick per jump.
- Attack heights: mid (blockable standing or crouching), low (crouching kicks, sweep: must be blocked
  crouching; Konrad's stomp kick is low as well), overhead (jump attacks: must be blocked standing).
  Blocked attacks do no damage, cause half the hitstun and full pushback.
- Knockdown: sweeps and every hit on a fighter in the air knock down; the fighter lies for 1 s, gets up
  (0.4 s) and is invulnerable meanwhile. A KO knocks down for good.

## 2. Display (planned)
- H320/V200 PAL, 50 Hz, CPU at 40.5 MHz, settings inherited from ShooterMega65 (`CHRXSCL = 120`, RRB double
  buffering, GOTOX in logical 320-px coordinates).
- 25 visible character rows. Every row of the screen buffer has three parts:
  1. **Background:** 40 full-colour (FCM) characters, 8×8 px, 256 colours. The arena is one picture of
     up to 1,000 unique glyphs (64 bytes each, 64,000 bytes). Because nothing scrolls, the background
     part of the buffer is written once per arena and never rebuilt.
  2. **Overlay:** RRB fragments for the two fighters, projectiles, hit sparks and dust.
  3. **HUD:** energy bars, timer and round markers in rows 0–2, also as overlay fragments (or fixed
     background characters if that proves cheaper).
- Row budget: 40 background tokens + 2 fighters × (1 GOTOX + up to 5 glyph columns) + effects
  (about 3 × 3 tokens) + closing GOTOX ≈ 64 tokens. The row is laid out for **80 tokens (160 bytes)**,
  which leaves room for a projectile and sparks on the same line. **(to verify: raster time per line)**
- Only the overlay part is rebuilt each frame: the frame loop copies the fixed background part of each
  row into the back buffer by DMA and appends the fragments, as ShooterMega65 does with its ring rows.

### 2.1 Palette
- The arena uses palette entries up to 175 (FCM pixels index the palette directly).
- Fighters, effects and HUD use NCM glyphs (16×8 px, 16 colours, 64 bytes) with palette banks 11–15:
  bank 12 = fighter 1, bank 13 = fighter 2, bank 14 = mirror-match alternative, bank 15 = effects and HUD,
  bank 11 = spare (for example a flash colour when hit). The art pipeline checks that an arena stays
  below entry 176.

## 3. Fighters as RRB objects (planned)
- A fighter frame is up to **4–5 NCM columns (64–80 px) × 12–13 glyph rows (96–104 px)**.
- The emitter is ShooterMega65's pixie emitter (`pixie.asm`): one fragment per touched row, a GOTOX token
  with Y offset for sub-row positioning, blank guard glyphs above and below every column.
- **Facing:** only right-facing frames are stored. A left-facing fighter is drawn with the column order
  reversed and the VIC-IV horizontal flip bit set in the glyph colour byte (colour RAM byte 0, bit 6:
  `$48` instead of `$08`). This halves the frame memory. **(confirmed on hardware, Stage 1)**
- Each frame stores an x anchor (the fighter's foot point) so that flipping mirrors around the body and
  not around the bounding box.

### 3.1 Frame streaming from attic RAM
Animation frames need a lot of memory: a 4×12 frame is 48 glyphs of 64 bytes = 3 KB before trimming
empty glyphs. A fighter with about 40 frames needs 60–120 KB. All frames therefore live in **attic RAM**
(every MEGA65 from R3 on, as for ShooterMega65). Each fighter has two glyph slots of 4 KB in chip RAM;
when the frame changes, the new frame is copied by DMA into the slot that is not being shown, and the
slot is switched with the next screen buffer flip. At most two 4 KB copies per frame. **(to verify:
attic RAM DMA time)**

### 3.2 Loadable fighters (planned)
- The engine contains **no fighter-specific code**. Everything that makes a fighter is data in a
  **fighter package**, one file per fighter on the disk (`F-TIAGO`, `F-KONRAD`, …):
  header (name, flag/country, health, walk and jump speeds, two palettes), frame directory and trimmed
  frame glyphs, animation tables, move tables (normals and specials with their input motion), boxes,
  sound-effect ids and the id of the fighter's home arena.
- Special moves are built from a fixed set of **move types** that the engine implements once:
  strike, multi-hit, lunge/dash attack, rising attack, jump attack, projectile, command throw. A new
  fighter combines and parameterises these; a new move type is an engine change and gets its own stage.
- At fighter selection the two chosen packages are loaded from disk into two attic-RAM slots
  (loader from ShooterMega65). A mirror match loads one package and uses its second palette.
- **Size budget per package: 64 KB on disk** (frames compressed), checked by the build. Stage 2
  measurement: 26 uncompressed frames are already 81 KB (Tiago) and 91 KB (Konrad); Stage 3 (55 frames):
  162 KB and 173 KB. A package may take up to 256 KB of attic RAM (8 MB are available), but on the disk the
  files must be **compressed by Stage 6**. Plan: a glyph dictionary per fighter (every unique glyph stored
  once, frames as lists of glyph numbers, blank glyphs as 0) expanded by DMA when a frame is uploaded. Estimate for the
  D81 (about 790 KB): program ~40 KB, music and samples ~60 KB, arenas ~40–60 KB each (compressed),
  fighters 64 KB each. Seven fighters and their arenas do not fit on one D81; the plan is therefore:
  disk 1 = game with Tiago, Konrad and their arenas; further fighters on disk 1 as long as space
  allows, then an add-on disk. **(to decide when the sizes are measured, at the latest in Stage 6)**
- Roster: Tiago and Konrad are built first (Stages 1–8). The other proposed fighters (Moussa/Senegal,
  Kanya/Thailand, Élodie/France, El Cóndor/Mexico, Batu/Mongolia) follow as packages, one per stage, after
  Stage 8. Each fighter brings a home arena, so the world championship travels from country to country.

## 4. Game logic (planned)
- Fixed 50 updates per second, one per video frame.
- Each fighter is a state machine: `idle, walk_fwd, walk_back, crouch, jump_up/fwd/back, attack (with
  move id), block_high, block_low, hitstun, blockstun, knockdown, getup, win, lose`.
- **Moves** are data tables: animation frames with duration, plus startup, active and recovery phases,
  damage, hitstun, blockstun, pushback and whether the move hits high, low or overhead.
- **Boxes:** each frame has one push box (fighters may not overlap), up to two hurt boxes and during
  active frames one hit box. Stage 2: one push distance (36 px between the anchors), one hurt box per
  fighter (half width and height from the fighter's stats), and a hit box of 14×12 px around the striking
  joint (hand, foot, knee) on active frames, taken from the pose by the art tools. Instead of an on-screen
  overlay, the preview sheets in `build/preview` are used to check the boxes.
- **Hit pause:** 4–6 frames in which both fighters freeze, followed by pushback. Corner rule: if the
  defender is at the screen edge, the attacker is pushed back instead.
- **Arena width** = screen width (320 px), fighters cannot leave it.

## 5. Input (planned)
- Each fighter reads a **virtual joystick byte** (up, down, left, right, button 1, button 2).
  For humans it is filled from port 1 / port 2; for the CPU opponent by the AI. The fighter code never
  reads the hardware directly.
- Directions are converted to "forward/back" relative to the facing direction.
- An **input buffer** keeps the last 32 frames per player; special moves are recognised from it
  (quarter circle forward + button, charge back then forward + button, and so on).
- Port 1 shares lines with the keyboard matrix. The keyboard is only scanned while the game is paused.
- **Two buttons** (owner, 2026-11-15: 8BitDo gamepads with several buttons): button 1 = punch, button 2 = kick.
  The direction held at the moment of the press chooses the strength:
  neutral or back = light, forward = heavy; down / down-back = crouching light, down-forward = crouching heavy;
  in the air: forward held = heavy. Both buttons together close to the opponent = throw (late stage).
  Special moves use motions plus one button. The mapping is a table and may be tuned after hardware tests.
- Button 2 is read through the joystick port's POT X line, as two-button adapters (C64GS convention) wire
  it: pressed reads a low value. Stage 2 reads `$D620` (port 1) and `$D622` (port 2) and counts values
  below `$80` as pressed; key P shows port 2's reading in the border colour for diagnosis.
  **(confirmed on hardware with the owner's 8BitDo pads, Stage 2)**

## 6. HUD and round flow (Stage 3)
- Energy bars for both players (row 1), the round timer between them, the names below the bars, a star
  for every won round next to the timer; all text in a 16×16 font (two NCM glyphs per character, drawn
  by Claude in `tools/make_assets.py`).
- Round flow (`src/game.asm`): "ROUND n" (1.8 s), "FIGHT!" (1 s), fight with a 99-second timer
  (50 frames per second); KO ("K.O.") or time up ("TIME", the fighter with more energy wins, equal =
  "DRAW"); the winner strikes his win pose; after 4.4 s the next round. Whoever wins two rounds wins the
  match ("<NAME> WINS", 6 s), then a new match starts. After a draw in round 3 round 3 is repeated.
  (Planned later: slow motion on KO, a separate winner screen.)

## 7. Sound (planned)
- Music and sound engine from ShooterMega65 (`sound.asm`, `build_music.py`): music on two SIDs, effects on
  the others.
- Hit and block sounds, voice-like shouts for special moves as samples played by audio DMA.

## 8. Artwork
- **Since Stage 4b the fighters come from sprite sheets** made by the owner with an image generator and
  imported during the build (`tools/import_fighter.py`, format and rules in `docs/art_import.md`). Walk
  animations are driven by the distance walked, walk speeds are in half pixels. The skeleton renderer
  described below draws the animations that have no sheet yet.
- Claude draws both fighters, the arenas, the title and the character screens with Python scripts in
  `assets/source/` (as in ShooterMega65), with check scripts for size, palette and frame limits.
- The fighters are original characters (no likeness of existing games).
- **Fighter renderer (Stage 4, `tools/fighter_art.py`):** a pose is a set of joint positions; the renderer
  draws tapered limbs with muscle bulges, a torso with chest and belly lines (bare torso) or a singlet with
  side-seam stripes, wide trousers with folds, a cord belt with knot and tassels, shoes with sole and laces,
  a head in profile (cranium with a flat back of the head, forehead, brow, nose, lips, chin, jaw, hairline from the forehead to
  the nape) with ear, eye, brow and mouth, curly hair or a military buzz cut with a beard, and three
  facial expressions (normal, hit: eyes shut and mouth open, win). Parts of the same material are merged
  and shaded as one area, and the edges are left out around the joints where limbs grow out of the body.
  The head is drawn upright and turned with the neck when it is tilted by more than 25° (falling, lying). Light falls from the front and the top,
  a warm rim of sunset light lies on the back edge of the skin, and a dark outline surrounds the figure.
  A far arm that strikes across the body (rear-hand punch) is drawn in front of the torso.
  The win poses are drawn **from the front** (`front()` poses, `render_front()`): both arms and legs lit,
  torso with the costume's front details, a frontal head with two eyes, ears, hair and beard.
- Palette per fighter: 16 colours (transparent, outline, 4 skin tones, hair, 4 clothing tones, 2 accent
  colours, rim light, eye white, mouth).
- **Sparks (Stage 4):** a three-frame hit spark (yellow-white star burst) and a two-frame block spark (blue
  shield arc) at the centre of the hit box, palette bank 11; they keep playing during the hitstop.

## 9. Loading and memory
See `docs/memory_map.md`. Everything is loaded from the D81 at start: arenas, fighter frames, music and
samples into attic RAM, the current arena and the shared glyphs into chip RAM.

## 10. Leaving the game (planned)
As ShooterMega65: X or RUN/STOP returns to BASIC; VIC-IV registers, palettes, zero page and base page are
saved at start and restored on exit (`system.asm` from ShooterMega65).

## 11. Roadmap
| Stage | Content |
|---|---|
| 0 | repository, rules, design, build pipeline, D81 test program |
| 1 | video set-up, the Rio arena (FCM), Tiago (placeholder art) standing and walking with joystick 2, frame streaming from attic RAM, horizontal flip test, exit to BASIC |
| 2 | Konrad, both fighters, both joysticks, light/heavy attacks, hits, hitstop, pushback, push boxes, energy bars, KO and next round |
| 3 | jumping, crouching, blocking, attack heights, knockdown and getting up; rounds, timer, KO, win poses, font, names |
| 4 | final artwork for both fighters (new renderer), facial expressions, new win poses, hit and block sparks |
| 5 | special moves and projectiles, input buffer; sound effects |
| 6 | title, fighter selection with package loading, versus screen, music, winner screen |
| 7 | CPU opponent |
| 8 | second arena, balancing, polish |
| 9+ | one further fighter per stage as a loadable package, with its home arena |

## 12. Decisions log
- **Versus fighter, not a scrolling beat 'em up** (owner, 2026-11-14): static backgrounds keep the engine
  simple; the effort goes into animation and fighting mechanics.
- ~~Exactly two fighters~~ (owner, 2026-11-14) → **two fighters on screen, chosen from a roster of
  loadable fighter packages** (owner, 2026-11-15); first fighters: Tiago (Brazil, capoeira) and Konrad
  (Germany, wrestling).
- **Two players first, CPU opponent later** (owner, 2026-11-14), hence the virtual joystick (§5).
- **Artwork by Claude** (owner, 2026-11-14), drawn with scripts as in ShooterMega65 (fighters: replaced in Stage 4b, see below).
- **Toolchain and working rules from ShooterMega65** (2026-11-14).
- **FCM background, NCM fighters** (Stage 0 plan): a static picture does not need to be built from
  reusable tiles, so full-colour characters give the best arenas; fighters stay in the 16-colour format
  whose RRB handling is proven in ShooterMega65.
- **Horizontal flip instead of mirrored frames** (confirmed on hardware in Stage 1).
- **Frames in attic RAM, streamed by DMA** (confirmed on hardware in Stage 1).
- **Two-button control scheme** (owner, 2026-11-15), see §5.
- **First arena: the Rio beach promenade** (owner, 2026-11-15).
- **Skeleton renderer for the fighters** (Stage 1): poses are joint positions, `tools/fighter_art.py`
  draws limbs, outline and shading; every fighter is a costume plus poses.
- **Layout constants in one place** (Stage 1): `tools/make_assets.py` writes `build/gen/layout.inc`.
- **Stage 2 move set:** button 1 = light punch, forward + button 1 = heavy punch, button 2 = light kick,
  forward + button 2 = heavy kick. Tiago: open-hand jab, rear-hand strike, ponteira, martelo.
  Konrad: jab, forearm smash, stomp kick, knee strike. Health 128 (= bar width in pixels).
- **Stage 3:** vertical trimming of frames (only glyph rows with pixels are stored); fighter packages
  256 KB in attic RAM; 19 animations and 9 moves per fighter (tables indexed fighter * 32 + animation and
  fighter * 16 + move).
- **Fighter tables are still built into the program** in Stage 2 (both fighters are known at build time);
  moving the headers into the packages follows with the fighter selection in Stage 6.
- **Fighter art from an image generator** (owner, 2026-11-16): the owner supplies sprite sheets (256 px
  cells, magenta background), Claude imports them; replaces "artwork by Claude" for the fighters. Figures in
  calm poses at most 0.6 x their height wide (about 55 px in the game) to leave room to move.
- **Walk speed in half pixels, walk animation driven by distance** (Stage 4b): Tiago 2 px, Konrad 1.5 px
  forward, both 1 px back; the feet of the sheets stay on the ground in both directions.
- **Theme: a "world championship"** (owner, 2026-11-15): the fighters show typical traits of different
  continents and countries.

## 13. Open questions for the owner
1. One D81 with an add-on disk, or a different medium, once the roster no longer fits (§3.2).

# WorldFight65 – Technical Design

Status: Stage 0. This document is the plan. Everything below that has not been built and tested on hardware is
marked **(planned)** or **(to verify)**. Decisions are logged in §12.

## 1. Game summary
- One-on-one fighting game, two fighters, static arena backgrounds (no scrolling).
- Mode 1: two players, joysticks in port 1 and port 2. Mode 2 (later): one player against the CPU.
- Best of three rounds, 99-second round timer (counted in game seconds), KO or time-over decides a round.
- Each fighter: walking, jumping (up, forward, back), crouching, blocking (hold away from the opponent),
  light and heavy attacks standing, crouching and in the air, throws (optional, late), two to three special
  moves each, one of them a projectile.
- Both players may choose the same fighter (mirror match); the second one then uses an alternative palette.

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
  `$48` instead of `$08`). This halves the frame memory. **(to verify on hardware in Stage 1)**
- Each frame stores an x anchor (the fighter's foot point) so that flipping mirrors around the body and
  not around the bounding box.

### 3.1 Frame streaming from attic RAM
Animation frames need a lot of memory: a 4×12 frame is 48 glyphs of 64 bytes = 3 KB before trimming
empty glyphs. A fighter with about 40 frames needs 60–120 KB. All frames therefore live in **attic RAM**
(every MEGA65 from R3 on, as for ShooterMega65). Each fighter has two glyph slots of 4 KB in chip RAM;
when the frame changes, the new frame is copied by DMA into the slot that is not being shown, and the
slot is switched with the next screen buffer flip. At most two 4 KB copies per frame. **(to verify:
attic RAM DMA time)**

## 4. Game logic (planned)
- Fixed 50 updates per second, one per video frame.
- Each fighter is a state machine: `idle, walk_fwd, walk_back, crouch, jump_up/fwd/back, attack (with
  move id), block_high, block_low, hitstun, blockstun, knockdown, getup, win, lose`.
- **Moves** are data tables: animation frames with duration, plus startup, active and recovery phases,
  damage, hitstun, blockstun, pushback and whether the move hits high, low or overhead.
- **Boxes:** each frame has one push box (fighters may not overlap), up to two hurt boxes and during
  active frames one hit box. The art tools export them with the frames; a debug key shows them on screen.
- **Hit pause:** 4–6 frames in which both fighters freeze, followed by pushback. Corner rule: if the
  defender is at the screen edge, the attacker is pushed back instead.
- **Arena width** = screen width (320 px), fighters cannot leave it.

## 5. Input (planned)
- Each fighter reads a **virtual joystick byte** (up, down, left, right, button 1, button 2, button 3).
  For humans it is filled from port 1 / port 2; for the CPU opponent by the AI. The fighter code never
  reads the hardware directly.
- Directions are converted to "forward/back" relative to the facing direction.
- An **input buffer** keeps the last 32 frames per player; special moves are recognised from it
  (quarter circle forward + button, charge back then forward + button, and so on).
- Port 1 shares lines with the keyboard matrix. The keyboard is only scanned while the game is paused.
- **Buttons:** the basic scheme works with any one-button joystick (button alone = punch, button with
  down-forward/down-back = kicks, button held = heavy). If the owner has 2- or 3-button pads, buttons 2 and
  3 are read through the POT lines. **(open question, §13)**

## 6. HUD and round flow (planned)
- Energy bars for both players, a two-digit timer, round markers, player names.
- Round flow: "ROUND 1" / "FIGHT!" banner, play, KO or time over, slow-down on KO, win pose, next round;
  after two won rounds the winner screen.

## 7. Sound (planned)
- Music and sound engine from ShooterMega65 (`sound.asm`, `build_music.py`): music on two SIDs, effects on
  the others.
- Hit and block sounds, voice-like shouts for special moves as samples played by audio DMA.

## 8. Artwork (planned)
- Claude draws both fighters, the arenas, the title and the character screens with Python scripts in
  `assets/source/` (as in ShooterMega65), with check scripts for size, palette and frame limits.
- The fighters are original characters (no likeness of existing games).

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
| 1 | video set-up, one placeholder arena (FCM), one fighter (placeholder art) standing and walking with joystick 2, horizontal flip test, hit-box debug overlay, exit to BASIC |
| 2 | both fighters, both joysticks, light/heavy attacks, hits, push boxes, energy bars |
| 3 | jumping, crouching, blocking, hitstun, knockdown; rounds, timer, KO, win poses |
| 4 | first real artwork for both fighters and the first arena |
| 5 | special moves and projectiles, input buffer; sound effects |
| 6 | title, fighter selection, versus screen, music, winner screen |
| 7 | CPU opponent |
| 8 | second arena, balancing, polish |

## 12. Decisions log
- **Versus fighter, not a scrolling beat 'em up** (owner, 2026-11-14): static backgrounds keep the engine
  simple; the effort goes into animation and fighting mechanics.
- **Exactly two fighters** (owner, 2026-11-14), also in the final game.
- **Two players first, CPU opponent later** (owner, 2026-11-14), hence the virtual joystick (§5).
- **Artwork by Claude** (owner, 2026-11-14), drawn with scripts as in ShooterMega65.
- **Toolchain and working rules from ShooterMega65** (2026-11-14).
- **FCM background, NCM fighters** (Stage 0 plan): a static picture does not need to be built from
  reusable tiles, so full-colour characters give the best arenas; fighters stay in the 16-colour format
  whose RRB handling is proven in ShooterMega65.
- **Horizontal flip instead of mirrored frames** (Stage 0 plan, to verify).
- **Frames in attic RAM, streamed by DMA** (Stage 0 plan).

## 13. Open questions for the owner
1. Which controllers do you use: one-button joysticks only, or pads with 2 or 3 buttons?
2. Names, look and fighting styles of the two fighters, and the first arena (Claude can propose them).

# Fighter artwork from sprite sheets (Stage 4b)

Since Stage 4b the fighters are drawn by an image generator (the owner creates the sheets) and imported by
`tools/import_fighter.py` during the build. Animations without a sheet are still drawn by the skeleton
renderer `tools/fighter_art.py` until every sheet exists.

## Master and check

`assets/art/<fighter>/master.png` (one 256 x 256 cell, the approved standing pose) defines the character;
every sheet is generated as an edit of it (`docs/art_prompts.md`). `tools/check_sheets.py <fighter> [sheet]`
compares sheets with the master before they are imported (without a master: frame 1 of idle).

## Sheet format

- One PNG per animation: `assets/art/<fighter>/<animation>.png`, animation names as in `ANIMS` of
  `tools/make_assets.py` (`idle`, `walk`, `lp`, `hp`, `lk`, `hk`, `hit`, `crouch`, `c_lp`, `c_lk`, `sweep`,
  `block`, `c_block`, `jump`, `j_p`, `j_k`, `fall`, `getup`, `win`).
- One row of square cells, 256 x 256 px each; exactly as many cells as the animation has frames in the
  fighter module (`assets/source/fighter_<name>.py`), otherwise the build stops.
- Solid flat magenta background `#FF00FF`. The character contains no magenta, pink or purple: small
  key-coloured specks inside the figure are filled from the surrounding colours, larger enclosed areas are
  treated as holes (transparent).
- The figure faces right. Soles on a common line, lowest pixel at y = 239 (16 px above the cell bottom);
  figure height from soles to top of head 224 px in every sheet of a fighter. Head and torso centred in the
  cell and at the same x in all frames (walk cycles are drawn in place).
- Crouching figures (`crouch`, `c_lp`, `c_lk`, `c_block`) are drawn at the same scale: about 150 px from the
  soles to the top of the head (the crouching hurt box). A sheet drawn to fill the cell can be fixed with
  `normalize_sheet.py … --height 150`.
- Colours exactly as in the idle sheet of the fighter (skin, hair, costume, belt, shoes): a fighter has only
  15 colours for all of his frames, so every deviating shade takes palette entries from the others.
- Width of the figure at most 135 px (0.6 x height) in idle, walk, block and hit poses; attacks and
  knockdowns up to about 250 px.
- Sheets in another size (e.g. 2172 x 724) are brought into this format with
  `python3 tools/normalize_sheet.py IN.png FRAMES OUT.png` (keeps the slot positions and the common foot line,
  scales the tallest figure to 224 px).

## Conversion

1. Key out the magenta background and its tinted fringe; fill small enclosed specks.
2. Scale: once per fighter, from frame 1 of the idle sheet (the master, once the idle sheet is made from it), so that the figure has the height of the
   skeleton-drawn idle frame (about 97 px in the game, scale about 0.41). Head and torso are placed at the
   same position relative to the anchor as in the skeleton frame, so the hit and push boxes of the fighter
   module keep fitting.
3. Place every frame in the 144 x 112 px canvas with the foot line on the anchor `(64, 109)`.
4. Quantise all frames of the fighter together to 15 colours + transparent (palette bank of the fighter).
   While imported and skeleton-drawn frames are mixed, only the imported frames choose the palette; the
   skeleton-drawn frames are mapped onto it.

## Walk cycles and speed

A walk sheet is played according to the distance walked (`walk_step` in `src/fighter.asm`): one walk frame
lasts `ticks x walk_fwd` half pixels. The distance of one cycle in the game is therefore
`6 frames x ticks x walk_fwd / 2` px and should match two steps of the sheet in game pixels; then the feet
stay on the ground, also when walking back at a lower speed.

| Fighter | walk_fwd / walk_back (half px per frame) | ticks per walk frame | cycle in the game | two steps in the sheet |
|---|---|---|---|---|
| Tiago | 4 / 2 (2 px / 1 px) | 6 | 72 px | about 75 px |
| Konrad | 3 / 2 (1.5 px / 1 px) | 8 | 72 px | about 69 px |

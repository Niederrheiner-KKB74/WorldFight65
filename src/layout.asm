// ----------------------------------------------------------------------------
// Memory layout (see docs/memory_map.md). The constants come from
// tools/make_assets.py (build/gen/layout.inc); this file only adds the
// assembler checks that keep the regions apart.
// ----------------------------------------------------------------------------
#import "../build/gen/layout.inc"

.errorif ARENA_GFX + 1000 * 64 > SLOT_A, "arena glyphs overlap the frame slots"
.errorif SLOT_A + SLOT_SIZE > SLOT_B, "frame slot A overlaps slot B"
.errorif SLOT_B + SLOT_SIZE > BLANK_NCM, "frame slot B overlaps the blank glyph"
.errorif BLANK_NCM + 64 > SCREEN_A, "blank glyph overlaps screen buffer A"
.errorif SCREEN_A + BUF_BYTES > SCREEN_B, "screen buffer A overlaps B"
.errorif SCREEN_B + BUF_BYTES > ARENA_MAP, "screen buffer B overlaps the arena map"
.errorif CLEAN_COL + BUF_BYTES > SAVED_SCR, "arena map overlaps the saved-state area"
.errorif SAVED_PAL0 + 768 > SAVED_ZP || SAVED_ZP + 256 > $5e000, "saved palette / zero page overlap"
.errorif COLOUR_A < $1000 || COLOUR_A + BUF_BYTES > COLOUR_B || COLOUR_B + BUF_BYTES > $8000, "colour buffers"
.errorif (SCREEN_A >> 16) != (SCREEN_B >> 16), "both screen buffers must lie in the same bank"

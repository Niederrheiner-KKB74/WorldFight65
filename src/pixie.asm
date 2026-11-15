// ----------------------------------------------------------------------------
// RRB pixie emitter (ported from ShooterMega65 Stage 19, src/pixie.asm),
// extended by horizontal flipping for fighters that face left.
//
// A frame is w NCM chars wide (16 px each) and h glyph rows high. Glyph layout
// (tools/make_assets.py): column c, row i is character base + c*(h+1) + i, and
// the glyph directly before every column and the glyph after it are blank.
// Vertical sub-row positioning uses the GOTOX Y offset (screen byte 1: bit 4 +
// offset in bits 5-7), the hardware-verified Vyper format ($10 + k<<5, colour
// $90/$00). One fragment per touched row: GOTOX token + w glyph tokens.
//
// Flipped (px_flip != 0): the columns are emitted from the last to the first and
// every glyph has the VIC-IV horizontal flip bit (colour RAM byte 0 bit 6:
// $48 instead of $08). (To verify on hardware: Stage 1 checklist.)
// ----------------------------------------------------------------------------

// in: px_x (16 bit signed, logical screen x of the frame's left edge), px_y (16 bit signed, top edge),
//     px_pal (colour byte 1), px_flip, px_base/px_bhi (absolute character number of glyph 0 of
//     column 0), px_w, px_h
pixie_draw:
    lda px_w
    asl
    clc
    adc #2
    sta px_need
    lda #$08
    ldx px_flip
    beq !+
    lda #$48
!:  sta px_c0
    // GOTOX = x + bias; visible if 0 <= GOTOX < 336
    clc
    lda px_x
    adc #GOTOX_BIAS
    sta px_gx
    lda px_x+1
    adc #0
    sta px_gx+1
    bmi !skip+
    beq !xok+
    cmp #1
    bne !skip+
    lda px_gx
    cmp #<336
    bcs !skip+
!xok:
    lda px_y+1
    bmi !neg+
    bne !skip+                  // >= 256: below the screen
    lda px_y
    cmp #VIS_ROWS*8
    bcs !skip+
    bcc !rows+
!neg:
    cmp #$ff                    // more than 256 px above: skip
    bne !skip+
!rows:
    lda px_y
    and #7
    tax
    lda ybits_tab,x
    sta px_yb
    cpx #1                      // carry = (k != 0)
    lda px_h
    adc #0
    sta px_n
    lda px_y+1                  // r0 = y >> 3 (arithmetic)
    sta px_row
    lda px_y
    lsr px_row
    ror
    lsr px_row
    ror
    lsr px_row
    ror
    sta px_r0
    // column step: +(h+1), or -(h+1) when flipped (the first emitted column is then the last one)
    ldx px_h
    inx
    stx px_step
    lda px_flip
    beq px_noflip
    lda px_w                    // base += (w-1)*(h+1)
    sta px_i
px_adv:
    dec px_i
    beq px_noflip
    clc
    lda px_base
    adc px_step
    sta px_base
    bcc px_adv
    inc px_bhi
    jmp px_adv
px_noflip:
    lda #0
    sta px_i
!loop:
    lda px_r0
    clc
    adc px_i
    bmi !next+                  // row above the screen
    cmp #VIS_ROWS
    bcs !done+                  // further rows are below as well
    sta px_row
    jsr emit_fragment
!next:
    inc px_i
    lda px_i
    cmp px_n
    bne !loop-
!done:
!skip:
    rts

// emit row px_i of the current frame into display row px_row
emit_fragment:
    jsr frag_begin
    bcc !+
    rts
!:
    // glyph = base + i (with a Y offset the hardware shows the bottom lines of glyph i-1 above it)
    clc
    lda px_base
    adc px_i
    sta px_gl
    lda px_bhi
    adc #0
    sta px_gl+1

    ldx px_w
!col:
    lda px_gl
    sta ((scr_ptr)),z
    lda px_c0                   // NCM glyph, flipped or not
    sta ((col_ptr)),z
    inz
    lda px_gl+1
    sta ((scr_ptr)),z
    lda px_pal
    sta ((col_ptr)),z
    inz
    dex
    beq !end+
    lda px_flip
    bne !back+
    clc                         // next column: + h + 1 glyphs
    lda px_gl
    adc px_step
    sta px_gl
    bcc !col-
    inc px_gl+1
    bne !col-
!back:
    sec                         // flipped: previous column
    lda px_gl
    sbc px_step
    sta px_gl
    bcs !col-
    dec px_gl+1
    bne !col-
!end:
    ldz #0
    rts

// Start a fragment of px_need bytes in display row px_row of the back buffer: set scr_ptr / col_ptr,
// write the GOTOX token (x = px_gx, Y-offset bits px_yb) and return with Z = 2, carry clear.
// Carry set (nothing written, overflow counted) if the row has no room left.
frag_begin:
    ldx px_row
    lda rowfill,x
    clc
    adc px_need
    cmp #OVL_END+1
    bcc !fits+
    inc overflow
    sec
    rts
!fits:
    pha                         // new fill level
    lda rowfill,x               // offset = row_ofs[row] + rowfill[row]
    clc
    adc row_ofs_lo,x
    sta tmp
    lda row_ofs_hi,x
    adc #0
    sta tmp+1
    clc
    lda tmp
    adc backscr
    sta scr_ptr
    lda tmp+1
    adc backscr+1
    sta scr_ptr+1
    lda #(SCREEN_A >> 16)
    sta scr_ptr+2
    lda #0
    sta scr_ptr+3
    clc
    lda tmp
    adc backcol
    sta col_ptr
    lda tmp+1
    adc backcol+1
    sta col_ptr+1
    lda #(COLRAM >> 16) & $ff
    sta col_ptr+2
    lda #(COLRAM >> 24)
    sta col_ptr+3
    pla
    sta rowfill,x
    ldz #0
    lda px_gx                   // GOTOX token
    sta ((scr_ptr)),z
    lda #$90                    // GOTOX, no background paint (transparent)
    sta ((col_ptr)),z
    inz
    lda px_gx+1
    and #3
    ora px_yb
    sta ((scr_ptr)),z
    lda #$00
    sta ((col_ptr)),z
    inz
    clc
    rts

ybits_tab:  .fill 8, $10 + (i << 5)
row_ofs_lo: .fill VIS_ROWS, <(i * ROW_BYTES)
row_ofs_hi: .fill VIS_ROWS, >(i * ROW_BYTES)
rowfill:    .fill VIS_ROWS, 0

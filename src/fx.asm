// ----------------------------------------------------------------------------
// Hit and block sparks (Stage 4): a short RRB animation at the point where an
// attack lands (centre of the overlap of hit box and hurt box). One spark at a
// time; frames 0-2 = hit, 3-4 = block (tools/make_assets.py, FX.bin).
// ----------------------------------------------------------------------------

.const FX_W = 2                 // NCM columns
.const FX_H = 3                 // glyph rows
.const FX_GLYPHS = 1 + FX_W * (FX_H + 1)
.const FX_TICKS = 3             // video frames per spark frame

// A = 0 hit / 1 block; the position comes from the hit test (hb_l, hb_r, hv_lo, hv_hi)
fx_spawn:
    tay
    lda fx_first,y
    sta fx_frame
    lda fx_last,y
    sta fx_end
    lda #0
    sta fx_tick
    lda #1
    sta fx_on
    clc                         // x = (hb_l + hb_r) / 2 - 16
    lda hb_l
    adc hb_r
    sta fx_x
    lda hb_l+1
    adc hb_r+1
    lsr
    ror fx_x
    sta fx_x+1
    sec
    lda fx_x
    sbc #16
    sta fx_x
    lda fx_x+1
    sbc #0
    sta fx_x+1
    clc                         // y = FLOOR_Y - (hv_lo + hv_hi) / 2 - 12 (hit box heights include the jump)
    lda hv_lo
    adc hv_hi
    ror
    sta tmp
    lda #FLOOR_Y - 12
    sec
    sbc tmp
    bcs !+
    lda #0
!:  sta fx_y
    rts
fx_first: .byte 0, 3
fx_last:  .byte 2, 4

// once per frame (also during hitstop, so the spark plays while the fighters freeze)
fx_update:
    lda fx_on
    beq !+
    inc fx_tick
    lda fx_tick
    cmp #FX_TICKS
    bcc !+
    lda #0
    sta fx_tick
    lda fx_frame
    cmp fx_end
    bcs !off+
    inc fx_frame
    rts
!off:
    lda #0
    sta fx_on
!:  rts

fx_draw:
    lda fx_on
    bne !+
    rts
!:  lda fx_x
    sta px_x
    lda fx_x+1
    sta px_x+1
    lda fx_y
    sta px_y
    lda #0
    sta px_y+1
    sta px_flip
    lda #FX_W
    sta px_w
    lda #FX_H
    sta px_h
    ldx fx_frame                // glyph 0 of column 0 = FX_CHAR + frame * FX_GLYPHS + 1
    lda fx_char_lo,x
    sta px_base
    lda fx_char_hi,x
    sta px_bhi
    lda #(FX_BANK << 4) | $0f
    sta px_pal
    jmp pixie_draw
fx_char_lo: .fill 5, <(FX_CHAR + i * FX_GLYPHS + 1)
fx_char_hi: .fill 5, >(FX_CHAR + i * FX_GLYPHS + 1)

fx_on:    .byte 0
fx_frame: .byte 0
fx_end:   .byte 0
fx_tick:  .byte 0
fx_x:     .word 0
fx_y:     .byte 0

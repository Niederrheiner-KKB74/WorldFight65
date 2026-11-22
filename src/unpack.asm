// ----------------------------------------------------------------------------
// Stage 10: unpacker for the "WZ" format of tools/lzpack.py (LZ4-like: literal runs and matches with a
// 16-bit offset). Packed files are loaded into attic RAM at ATTIC_PACK and unpacked once to their place
// in attic RAM (fighter packages, picture glyphs) while the title is shown. 32-bit flat pointers
// (((zp)),z with Z = 0) reach all of attic RAM. Needs the base page B = 0 (after system_save): it uses the
// game zero page $60-$6B.
// ----------------------------------------------------------------------------
.label up_src = $60             // 32 bit: packed data
.label up_dst = $64             // 32 bit: output
.label up_ref = $68             // 32 bit: match source in the output

.macro UnpackTo(dst) {
    lda #<(ATTIC_PACK & $ffff)
    sta up_src
    lda #>(ATTIC_PACK & $ffff)
    sta up_src+1
    lda #((ATTIC_PACK >> 16) & $ff)
    sta up_src+2
    lda #((ATTIC_PACK >> 24) & $ff)
    sta up_src+3
    lda #<(dst & $ffff)
    sta up_dst
    lda #>(dst & $ffff)
    sta up_dst+1
    lda #((dst >> 16) & $ff)
    sta up_dst+2
    lda #((dst >> 24) & $ff)
    sta up_dst+3
    jsr unpack
}

// C = 1 when the data does not start with "WZ" (file not packed)
unpack:
    ldz #0
    jsr up_get
    cmp #'W'
    beq !+
    sec
    rts
!:  jsr up_get
    cmp #'Z'
    beq !+
    sec
    rts
!:
    jsr up_get                  // the unpacked size is not needed (the data ends with offset 0)
    jsr up_get
    jsr up_get
!seq:
    jsr up_get                  // token
    sta up_tok
    lsr
    lsr
    lsr
    lsr
    jsr up_len                  // literal count -> up_n
!lit:
    lda up_n                    // copy the literals
    ora up_n+1
    beq !off+
    jsr up_get
    sta ((up_dst)),z
    inc up_dst                    // 32-bit increment
    bne !+
    inc up_dst+1
    bne !+
    inc up_dst+2
!:  lda up_n
    bne !+
    dec up_n+1
!:  dec up_n
    jmp !lit-
!off:
    jsr up_get                  // offset
    sta up_off
    jsr up_get
    sta up_off+1
    ora up_off
    bne !+
    clc                         // offset 0: the end
    rts
!:  sec                         // up_ref = up_dst - offset
    lda up_dst
    sbc up_off
    sta up_ref
    lda up_dst+1
    sbc up_off+1
    sta up_ref+1
    lda up_dst+2
    sbc #0
    sta up_ref+2
    lda up_dst+3
    sbc #0
    sta up_ref+3
    lda up_tok                  // match length - 4
    and #15
    jsr up_len
    clc
    lda up_n
    adc #4
    sta up_n
    bcc !copy+
    inc up_n+1
!copy:
    lda ((up_ref)),z              // forward byte by byte (overlapping matches repeat the pattern)
    sta ((up_dst)),z
    inc up_ref                    // 32-bit increment
    bne !+
    inc up_ref+1
    bne !+
    inc up_ref+2
!:  inc up_dst
    bne !+
    inc up_dst+1
    bne !+
    inc up_dst+2
!:  lda up_n
    bne !+
    dec up_n+1
!:  dec up_n
    lda up_n
    ora up_n+1
    bne !copy-
    jmp !seq-

// A = 4-bit length; 15 adds extension bytes (255 = continue) -> up_n (16 bit)
up_len:
    sta up_n
    lda #0
    sta up_n+1
    lda up_n
    cmp #15
    bne !done+
up_ext:
    jsr up_get
    pha
    clc
    adc up_n
    sta up_n
    bcc !+
    inc up_n+1
!:  pla
    cmp #255
    beq up_ext
!done:
    rts

up_get:
    lda ((up_src)),z
    inc up_src                    // 32-bit increment
    bne !+
    inc up_src+1
    bne !+
    inc up_src+2
!:  rts

up_tok: .byte 0
up_off: .word 0
up_n:   .word 0

#if AUTOTEST_UNPACK
// Test build: after loading, every unpacked region is summed and compared with the sums of the original
// files (build/gen/pack_check.inc). The screen shows "READY" when all match, "DRAW" on a mismatch.
#import "../build/gen/pack_check.inc"
.macro CheckRegion(addr, size, sum) {
    lda #<(addr & $ffff)
    sta up_src
    lda #>(addr & $ffff)
    sta up_src+1
    lda #((addr >> 16) & $ff)
    sta up_src+2
    lda #((addr >> 24) & $ff)
    sta up_src+3
    lda #<size
    sta ck_n
    lda #>size
    sta ck_n+1
    lda #[size >> 16]
    sta ck_n+2
    jsr ck_sum
    lda ck_s
    cmp #<sum
    bne !bad+
    lda ck_s+1
    cmp #>sum
    beq !ok+
!bad:
    inc ck_fail
!ok:
}
unpack_selftest:
    lda #0
    sta ck_fail
    CheckRegion(ATTIC_TGFX, CK_T_TITLE_GFX_SIZE, CK_T_TITLE_GFX_SUM)
    CheckRegion(ATTIC_AGFX, CK_A_RIO_GFX_SIZE, CK_A_RIO_GFX_SUM)
    CheckRegion(ATTIC_ZGFX, CK_A_ZOLL_GFX_SIZE, CK_A_ZOLL_GFX_SUM)
    CheckRegion(ATTIC_F1, CK_F_TIAGO_SIZE, CK_F_TIAGO_SUM)
    CheckRegion(ATTIC_F2, CK_F_KONRAD_SIZE, CK_F_KONRAD_SUM)
    lda #5                      // green
    ldx ck_fail
    beq !+
    lda #2                      // red
!:  sta ck_col
    rts
ck_sum:                         // 16-bit sum of ck_n (24 bit) bytes at up_src
    ldz #0
    lda #0
    sta ck_s
    sta ck_s+1
!l: lda ((up_src)),z
    clc
    adc ck_s
    sta ck_s
    bcc !+
    inc ck_s+1
!:  inc up_src
    bne !+
    inc up_src+1
    bne !+
    inc up_src+2
!:  lda ck_n                    // count down 24 bit
    bne !d+
    lda ck_n+1
    bne !c+
    dec ck_n+2
!c: dec ck_n+1
!d: dec ck_n
    lda ck_n
    ora ck_n+1
    ora ck_n+2
    bne !l-
    rts
ck_n:    .fill 3, 0
ck_s:    .word 0
ck_fail: .byte 0
ck_col:  .byte 0
#endif

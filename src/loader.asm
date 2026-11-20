// ----------------------------------------------------------------------------
// Loading SEQ files with the KERNAL into chip or attic RAM.
// Taken from ShooterMega65 Stage 19 (src/level.asm: load_device, load_seq_to,
// ld_flush, print), which follows the hardware-verified Vyper rules:
// SETBNK before SETNAM, CHRIN/READST loop, CLRCHN/CLOSE.
// Called only before the game takes over the machine.
// ----------------------------------------------------------------------------
.const SETLFS = $ffba
.const SETNAM = $ffbd
.const SETBNK = $ff6b
.const OPEN   = $ffc0
.const CLOSE  = $ffc3
.const CHKIN  = $ffc6
.const CLRCHN = $ffcc
.const CHRIN  = $ffcf
.const READST = $ffb7
.const CHROUT = $ffd2

load_device:
    lda $ba                     // device of the last LOAD (Vyper: capture_device)
    cmp #8
    bcs !+
    lda #8
!:  sta ld_device
    rts

// Load the file whose name is at A/X (lo/hi), length Y, to ld_dst (low 16 bits, bank 0-15,
// megabyte: 0 chip RAM / $80 attic RAM), at most ld_maxpg * 256 bytes (16 bit). The destination may
// cross 64 KB boundaries within its megabyte (WorldFight65 extension).
// Carry set on error (a message has been printed).
load_seq_to:
    sta ld_name
    stx ld_name+1
    sty ld_len
    lda #0
    sta ld_x
    sta ld_total
    sta ld_total+1
    sta ld_total+2
    lda ld_dst
    sta job_ldflush+DMA_DST
    lda ld_dst+1
    sta job_ldflush+DMA_DST+1
    lda ld_dst+2
    sta job_ldflush+DMA_DST+2
    lda ld_dst+3
    sta job_ldflush+DMA_DSTMB
    lda #2
    ldx ld_device
    ldy #2
    jsr SETLFS
    lda #0
    ldx #0
    jsr SETBNK                  // file name in bank 0 (Vyper rule)
    lda ld_len
    ldx ld_name
    ldy ld_name+1
    jsr SETNAM
    jsr OPEN
    bcs !err+
    ldx #2
    jsr CHKIN
    bcs !err+
!byte:
    jsr CHRIN
    ldx ld_x
    sta ld_buf,x
    inc ld_x
    jsr READST
    sta ld_st
    and #$bf                    // anything but EOF is an error
    bne !err+
    lda ld_x
    bne !+
    jsr ld_flush                // 256 bytes collected
    bcs !err+
!:  lda ld_st
    and #$40
    beq !byte-
    lda ld_x                    // EOF: write the rest
    beq !+
    jsr ld_flush
    bcs !err+
!:  jsr CLRCHN
    lda #2
    jsr CLOSE
    lda ld_total
    ora ld_total+1
    ora ld_total+2
    beq !err2+
    clc
    rts
!err:
    jsr CLRCHN
    lda #2
    jsr CLOSE
!err2:
    lda ld_title                // Stage 6: the title is shown - back to the BASIC screen before any output
    beq !+
    jsr screen_to_basic
    lda #0
    sta ld_title
!:  lda #<msg_load
    ldx #>msg_load
    jsr print
    lda ld_name
    sta ld_char+1
    lda ld_name+1
    sta ld_char+2
    lda #0
    sta ld_x
ld_char:
    lda $ffff
    jsr CHROUT
    inc ld_char+1
    bne !+
    inc ld_char+2
!:  inc ld_x
    lda ld_x
    cmp ld_len
    bne ld_char
    lda #13
    jsr CHROUT
    sec
    rts

// copy ld_x bytes (0 = 256) from ld_buf to the next destination
ld_flush:
    lda ld_x
    sta job_ldflush+DMA_COUNT
    lda #0
    sta job_ldflush+DMA_COUNT+1
    lda ld_x
    bne !+
    inc job_ldflush+DMA_COUNT+1
!:  RunDma(job_ldflush)
    clc
    lda job_ldflush+DMA_DST
    adc job_ldflush+DMA_COUNT
    sta job_ldflush+DMA_DST
    lda job_ldflush+DMA_DST+1
    adc job_ldflush+DMA_COUNT+1
    sta job_ldflush+DMA_DST+1
    bcc !+
    inc job_ldflush+DMA_DST+2      // next 64 KB bank
!:  clc
    lda ld_total
    adc job_ldflush+DMA_COUNT
    sta ld_total
    lda ld_total+1
    adc job_ldflush+DMA_COUNT+1
    sta ld_total+1
    lda ld_total+2
    adc #0
    sta ld_total+2
    cmp ld_maxpg+1                // pages loaded (total >> 8) >= maximum: file too big
    bcc !ok+
    bne !big+
    lda ld_total+1
    cmp ld_maxpg
    bcs !big+
!ok:
    lda #0
    sta ld_x
    clc
    rts
!big:
    sec
    rts

print:                          // A/X = zero-terminated text
    sta pr_char+1
    stx pr_char+2
pr_char:
    lda $ffff
    beq !+
    jsr CHROUT
    inc pr_char+1
    bne pr_char
    inc pr_char+2
    bne pr_char
!:  rts

// Load one file: name, name length, destination, max. pages (16 bit)
.macro LoadFile(name, len, dst, maxpages) {
    lda #<(dst & $ffff)
    sta ld_dst
    lda #>(dst & $ffff)
    sta ld_dst+1
    lda #((dst >> 16) & $0f)
    sta ld_dst+2
    lda #((dst >> 20) & $ff)
    sta ld_dst+3
    lda #<maxpages
    sta ld_maxpg
    lda #>maxpages
    sta ld_maxpg+1
    lda #<name
    ldx #>name
    ldy #len
    jsr load_seq_to
}

job_ldflush: DmaJob(DMA_CMD_COPY, ld_buf, 0, 256)
ld_device: .byte 8
ld_title:  .byte 0               // 1 while the title is shown during loading (main.asm)
ld_name:   .word 0
ld_len:    .byte 0
ld_x:      .byte 0
ld_st:     .byte 0
ld_total:  .fill 3, 0
ld_dst:    .fill 4, 0
ld_maxpg:  .word 0
.encoding "petscii_upper"
msg_load:  .text "WORLDFIGHT65: CANNOT LOAD "
           .byte 0
.align $100
ld_buf:    .fill 256, 0

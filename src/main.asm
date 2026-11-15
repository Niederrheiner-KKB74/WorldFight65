// ============================================================================
// WorldFight65 - Stage 1: arena and one fighter
//   H320/V200. The Rio beach arena is a static full-colour (FCM) picture; Tiago
//   is an RRB object of NCM glyphs, streamed frame by frame from attic RAM.
//   Joystick port 2: walk left/right, fire = turn round (test). Keys: F = turn
//   round, X or RUN/STOP = back to BASIC.
// Build: python3 tools/build.py   (KickAssembler 65CE02 5.25, see README)
// ============================================================================
.cpu _45gs02

#import "hw.asm"
#import "layout.asm"
#import "../build/gen/assets_const.inc"

// ---------------------------------------------------------------- zero page ($02-$3f, saved and restored)
.label back      = $02          // 0 = building buffer A, 1 = building buffer B
.label overflow  = $03          // RRB fragments dropped (debug)
.label scr_ptr   = $10          // 32-bit pointer into the screen buffer
.label col_ptr   = $14          // 32-bit pointer into colour RAM
.label tmp       = $18          // 16 bit
.label backscr   = $1a          // low 16 bits of the back screen buffer
.label backcol   = $1c          // colour RAM offset of the back buffer
.label px_x      = $20          // 16 bit signed
.label px_y      = $22          // 16 bit signed
.label px_pal    = $24
.label px_flip   = $25
.label px_base   = $26
.label px_bhi    = $27
.label px_w      = $28
.label px_h      = $29
.label px_gx     = $2a          // 16 bit
.label px_yb     = $2c
.label px_n      = $2d
.label px_i      = $2e
.label px_need   = $2f
.label px_row    = $30
.label px_r0     = $31
.label px_gl     = $32          // 16 bit
.label px_c0     = $34
.label px_step   = $35

// ---------------------------------------------------------------- BASIC stub
*=$2001
    .word basic_end, 10
    .byte $fe, $02, $30, $3a           // BANK 0:
    .byte $9e                          // SYS
    .text "8224"                       // $2020
    .byte 0
basic_end:
    .word 0

*=$2020

// ---------------------------------------------------------------- entry
start:
    jsr load_device
    jsr attic_detect                   // the frames live in attic RAM (every MEGA65 from R3 on)
    bcc !+
    lda #<msg_attic
    ldx #>msg_attic
    jmp print
!:  LoadFile(name_agfx, name_agfx_end - name_agfx, ARENA_GFX, 250)
    bcs !fail+
    LoadFile(name_amap, name_amap_end - name_amap, ARENA_MAP, 35)
    bcs !fail+
    LoadFile(name_f1, name_f1_end - name_f1, ATTIC_F1, 255)
    bcc !+
!fail:
    rts                                // failed: message printed, back to BASIC
!:  sei
    lda #$47                           // VIC-IV I/O personality
    sta VIC_KEY
    lda #$53
    sta VIC_KEY
    jsr system_save                    // everything needed to return to BASIC (also sets B = 0)
    lda #0
    sta CIA1_DDRA                      // port A as input: joystick 2 (restored on exit)
    cld
    sta overflow
    RunDma(job_blank)                  // the blank NCM glyph that ends every row
    jsr wait_vblank
    jsr video_init
    jsr palette_init
    jsr fighter_init

main_loop:
    jsr wait_vblank
    jsr flip                           // show the buffer just built
    lda build_slot                     // the shown buffer now uses the slot it was built with
    sta front_slot
    jsr read_keys
#if AUTOTEST
    jsr autotest_joy                   // test build: scripted joystick (build.py --define AUTOTEST)
#else
    lda CIA1_PRA                       // joystick port 2, active high
    eor #$ff
    and #$1f
    sta f_joy
#endif
    jsr fighter_update
    jsr buffer_clear
    jsr fighter_draw
    jmp main_loop

#if AUTOTEST
// Emulator test without a joystick: walk right for 100 frames, turn round (fire), walk back (right)
// for 40 frames, then stand still facing left.
autotest_joy:
    inc at_frame
    bne !+
    inc at_frame+1
!:  lda at_frame+1
    bne !idle+
    lda at_frame
    cmp #100
    bcs !+
    lda #JOY_RIGHT
    bne !set+
!:  cmp #100
    bne !+
    lda #JOY_FIRE
    bne !set+
!:  cmp #141
    bcs !idle+
    lda #JOY_RIGHT
    bne !set+
!idle:
    lda #0
!set:
    sta f_joy
    rts
at_frame: .word 0
#endif

wait_vblank:
!:  bit VIC_CTRL1
    bmi !-
!:  bit VIC_CTRL1
    bpl !-
    rts

// Attic RAM present? Write $A5 and $5A through DMA and read them back. Carry set = no attic RAM.
attic_detect:
    lda #<ATTIC_F1
    sta scr_ptr
    lda #>ATTIC_F1
    sta scr_ptr+1
    lda #<(ATTIC_F1 >> 16)
    sta scr_ptr+2
    lda #>(ATTIC_F1 >> 16)
    sta scr_ptr+3
    RunDma(job_attic_a5)
    ldz #0
    lda ((scr_ptr)),z
    cmp #$a5
    bne !no+
    RunDma(job_attic_5a)
    lda ((scr_ptr)),z
    cmp #$5a
    bne !no+
    clc
    rts
!no:
    sec
    rts
job_attic_a5: DmaJob(DMA_CMD_FILL, $a5, ATTIC_F1, 1)
job_attic_5a: DmaJob(DMA_CMD_FILL, $5a, ATTIC_F1, 1)

.encoding "petscii_upper"
name_agfx: .text "A-RIO-GFX,S,R"
name_agfx_end:
name_amap: .text "A-RIO-MAP,S,R"
name_amap_end:
name_f1:   .text "F-TIAGO,S,R"
name_f1_end:
msg_attic: .text "WORLDFIGHT65 NEEDS ATTIC RAM (MEGA65 R3 OR NEWER)."
           .byte 13, 0

#import "loader.asm"
#import "system.asm"
#import "video.asm"
#import "pixie.asm"
#import "fighter.asm"
#import "../build/gen/assets.inc"

pal_buf: .fill MAP_PAL_BYTES, 0

.errorif * > $c000, "program must end below $C000"

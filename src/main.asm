// ============================================================================
// WorldFight65 - Stage 4: final artwork, hit and block sparks
//   H320/V200. The Rio beach arena is a static full-colour (FCM) picture; the
//   fighters are RRB objects of NCM glyphs, streamed frame by frame from attic
//   RAM. Player 1: joystick port 1 (Tiago), player 2: port 2 (Konrad).
//   Button 1 = punch, button 2 (POT X line) = kick, forward + button = heavy;
//   down = crouch, up = jump, back = block. Best of three rounds.
//   Keys: X or RUN/STOP = back to BASIC, P = show the POT X readings in the border.
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
.label tx_ptr    = $36          // 16 bit: text pointer

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
    LoadFile(name_f1, name_f1_end - name_f1, ATTIC_F1, $400)
    bcs !fail+
    LoadFile(name_f2, name_f2_end - name_f2, ATTIC_F2, $400)
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
    sta CIA1_DDRA                      // port A as input: joystick 2, no keyboard row selected
    sta CIA1_DDRB                      // port B as input: joystick 1 (both restored on exit)
    cld
    sta overflow
    sta pot_debug
    RunDma(job_blank)                  // the blank NCM glyph that ends every row
    RunDma(job_hud)                    // energy bar glyphs
    RunDma(job_font)                   // 16x16 font
    RunDma(job_fx)                     // hit and block sparks
    lda #0
    sta fx_on
    jsr wait_vblank
    jsr video_init
    jsr palette_init
    jsr fighters_init
    jsr game_init

main_loop:
    jsr wait_vblank
    jsr flip                           // show the buffer just built
    lda build_slot                     // the shown buffer now uses the slots it was built with
    sta front_slot
    lda build_slot+1
    sta front_slot+1
    jsr read_keys
#if AUTOTEST
    jsr autotest_joy                   // test build: scripted joysticks (build.py --define AUTOTEST...)
    lda at_freeze
    bne !+
#else
    jsr read_joysticks
#endif
    jsr game_update
    jsr fighters_update
    jsr fx_update
!:  jsr buffer_clear
    jsr fighters_draw
    jsr fx_draw
    jsr hud_draw
    jmp main_loop

// Virtual joysticks: bits 0-4 from the CIA (active high), bit 5 = button 2 from the POT X line
// (C64GS / two-button adapters: pressed pulls POT X to a low reading).
// Player 1 = port 1 (CIA1 port B, POT $D620), player 2 = port 2 (CIA1 port A, POT $D622).
read_joysticks:
    lda CIA1_PRB
    eor #$ff
    and #$1f
    sta f_joy
    lda $d620
    cmp #$80
    bcs !+
    lda f_joy
    ora #JOY_B2
    sta f_joy
!:  lda CIA1_PRA
    eor #$ff
    and #$1f
    sta f_joy+1
    lda $d622
    cmp #$80
    bcs !+
    lda f_joy+1
    ora #JOY_B2
    sta f_joy+1
!:  lda pot_debug                      // key P: border colour = POT X of port 2 (pressing button 2 changes it)
    beq !+
    lda $d622
    lsr
    lsr
    lsr
    lsr
    sta VIC_BORDER
!:  rts
pot_debug: .byte 0

#if AUTOTEST
// Emulator test without joysticks: a script of (frame, joystick 1, joystick 2) events; the joystick
// values hold until the next event. At the frame marked with $ff the game freezes (drawing goes on),
// so the emulator screenshot shows that moment. Frame 0 = start; the fight begins at frame 140.
autotest_joy:
    lda at_freeze
    bne !done+
    ldy at_pos
    lda at_script,y             // next event due?
    cmp at_frame
    bne !run+
    lda at_script+1,y
    cmp at_frame+1
    bne !run+
    lda at_script+2,y
    cmp #$ff
    bne !+
    lda #1
    sta at_freeze
    rts
!:  sta at_j1
    lda at_script+3,y
    sta at_j2
    tya
    clc
    adc #4
    sta at_pos
!run:
#if AUTOTEST_KO
    lda at_frame+1                      // after the walk-in: kick every 16 frames while walking forward
    bne !k+
    lda at_frame
    cmp #196
    bcc !+
!k: lda at_frame
    and #16
    asl                                 // JOY_B2
    ora #JOY_RIGHT
    sta at_j1
!:
#endif
    lda at_j1
    sta f_joy
    lda at_j2
    sta f_joy+1
    inc at_frame
    bne !done+
    inc at_frame+1
!done:
    rts
at_frame:  .word 0
at_pos:    .byte 0
at_j1:     .byte 0
at_j2:     .byte 0
at_freeze: .byte 0
.macro AtEvent(frame, j1, j2) { .word frame
    .byte j1, j2 }
at_script:
#if AUTOTEST_INTRO
    AtEvent(60, $ff, 0)                                  // "ROUND 1" banner
#elif AUTOTEST_JUMP
    AtEvent(150, JOY_RIGHT, 0)                            // Tiago walks in
    AtEvent(176, JOY_UP | JOY_RIGHT, 0)                   // jumps forward
    AtEvent(178, 0, 0)
    AtEvent(186, JOY_B2, 0)                               // flying kick
    AtEvent(188, 0, 0)
    AtEvent(194, $ff, 0)
#elif AUTOTEST_KO
    AtEvent(150, JOY_RIGHT, 0)                            // Tiago walks in, then keeps kicking
    AtEvent(620, $ff, 0)
#elif AUTOTEST_BLOCK
    AtEvent(150, JOY_RIGHT, 0)                            // Tiago walks in
    AtEvent(196, 0, 0)
    AtEvent(200, 0, JOY_RIGHT)                            // Konrad holds back (blocks)
    AtEvent(204, JOY_FIRE | JOY_RIGHT, JOY_RIGHT)         // Tiago: heavy punch
    AtEvent(206, 0, JOY_RIGHT)
    AtEvent(214, $ff, 0)
#else
    AtEvent(150, JOY_RIGHT, 0)                            // Tiago walks in
    AtEvent(196, JOY_DOWN | JOY_RIGHT, 0)                 // crouches, forward
    AtEvent(200, JOY_DOWN | JOY_RIGHT | JOY_B2, 0)        // sweep
    AtEvent(202, JOY_DOWN, 0)
    AtEvent(250, $ff, 0)                                  // Konrad on the floor
#endif
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
name_f2:   .text "F-KONRAD,S,R"
name_f2_end:
msg_attic: .text "WORLDFIGHT65 NEEDS ATTIC RAM (MEGA65 R3 OR NEWER)."
           .byte 13, 0

#import "loader.asm"
#import "system.asm"
#import "video.asm"
#import "pixie.asm"
#import "fighter.asm"
#import "game.asm"
#import "fx.asm"
#import "../build/gen/assets.inc"
#import "../build/gen/texts.inc"

pal_buf: .fill MAP_PAL_BYTES, 0
hud_gfx: .import binary "../build/gen/HUD.bin"
job_hud: DmaJob(DMA_CMD_COPY, hud_gfx, HUD_GFX, 17 * 64)
font_gfx: .import binary "../build/gen/FONT.bin"
job_font: DmaJob(DMA_CMD_COPY, font_gfx, FONT_GFX, 80 * 64)
fx_gfx: .import binary "../build/gen/FX.bin"
job_fx: DmaJob(DMA_CMD_COPY, fx_gfx, FX_GFX, 5 * FX_GLYPHS * 64)

.errorif * > $c000, "program must end below $C000"

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
#import "../build/gen/music_const.inc"

.const M_TITLE  = 0               // game modes (Stage 6, menu.asm)
.const M_SELECT = 1
.const M_VERSUS = 2
.const M_FIGHT  = 3

// ---------------------------------------------------------------- zero page ($02-$3f, saved and restored)
.label back      = $02          // 0 = building buffer A, 1 = building buffer B
.label overflow  = $03          // RRB fragments dropped (debug)
.label scr_ptr   = $10          // 32-bit pointer into the screen buffer
.label col_ptr   = $14          // 32-bit pointer into colour RAM
.label tmp       = $18          // 16 bit
.label tmp2      = $1e          // walk: half pixels this frame (Stage 4b)
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
    // Stage 6 (as in Vyper Stage 5d-1): the title picture is loaded first and shown while the rest loads.
    // Pictures live in attic RAM and are copied into the chip-RAM picture area when a screen needs them.
!:  LoadFile(name_tgfx, name_tgfx_end - name_tgfx, ATTIC_TGFX, 252)
    bcc !+
    rts                                // failed: message printed, back to BASIC
!:  LoadFile(name_tmap, name_tmap_end - name_tmap, ATTIC_TMAP, 35)
    bcc !+
    rts
!:  sei
    lda #$47                           // VIC-IV I/O personality
    sta VIC_KEY
    lda #$53
    sta VIC_KEY
    jsr system_save                    // everything needed to return to BASIC (also sets B = 0)
    cld
    lda #0
    sta overflow
    sta pot_debug
    sta mot_debug
    sta fx_on
    RunDma(job_blank)                  // the blank NCM glyph that ends every row
    RunDma(job_hud)                    // energy bar glyphs
    RunDma(job_font)                   // 16x16 font
    RunDma(job_fx)                     // hit and block sparks
    jsr fighters_init                  // f_id and slots (the palettes need them)
    jsr wait_vblank
    jsr video_init
    lda #1                             // the title picture with "LOADING"
    jsr picture_copy
    jsr palette_init
    lda #M_TITLE
    sta g_mode
    lda #1
    sta m_loading
    jsr buffer_clear
    jsr menu_draw
    jsr wait_vblank
    jsr flip
    lda #1                             // a load error first switches back to the BASIC screen
    sta ld_title
    cli                                // the KERNAL loads the rest under the title (IRQ on, no KERNAL output)
    LoadFile(name_agfx, name_agfx_end - name_agfx, ATTIC_AGFX, 252)
    bcc !+
    jmp exit_to_basic                  // failed: the message is on the BASIC screen behind the title
!:  LoadFile(name_amap, name_amap_end - name_amap, ATTIC_AMAP, 35)
    bcc !+
    jmp exit_to_basic
!:  LoadFile(name_f1, name_f1_end - name_f1, ATTIC_F1, $400)
    bcc !+
    jmp exit_to_basic
!:  LoadFile(name_f2, name_f2_end - name_f2, ATTIC_F2, $400)
    bcc !+
    jmp exit_to_basic
!:  LoadFile(name_music, name_music_end - name_music, MUSIC_ADDR, (MUSIC_BYTES + 255) / 256)   // Stage 5
    bcc !+
    jmp exit_to_basic
!:  sei
    lda #0
    sta ld_title
    sta m_loading
    sta CIA1_DDRA                      // port A as input: joystick 2, no keyboard row selected
    sta CIA1_DDRB                      // port B as input: joystick 1 (both restored on exit)
    jsr sound_init                     // before title_enter starts the music (Stage 5: sound effects SID 2 + 4)
#if AUTOTEST && !AUTOTEST_MENU
    lda #0                             // emulator tests of the fight start in the fight, in the arena
    jsr show_picture
    lda #M_FIGHT
    sta g_mode
    jsr game_init
#else
    jsr title_enter                    // Stage 6: title -> selection -> versus -> fight
#endif

main_loop:
    jsr wait_vblank
    jsr sound_frame                    // music (Stage 6) and sound effects, once per frame
    jsr flip                           // show the buffer just built
    lda build_slot                     // the shown buffer now uses the slots it was built with
    sta front_slot
    lda build_slot+1
    sta front_slot+1
    jsr read_keys
#if AUTOTEST
    jsr autotest_joy                   // test build: scripted joysticks (build.py --define AUTOTEST...)
    lda at_freeze
    bne main_draw
#else
    jsr read_joysticks
    jsr spar_update                    // key T: one player attacks by himself (solo tests)
#endif
    jsr game_update
    lda g_mode                         // Stage 6: the fighters only fight in the fight mode
    cmp #M_FIGHT
    bne !+
    jsr fighters_update
    jsr motion_debug                   // key M: special-move recogniser in the border
!:  jsr fx_update
main_draw:
    jsr buffer_clear
    lda g_mode                         // no fighters on the title screen
    beq !+
    jsr fighters_draw
!:  jsr fx_draw
    lda g_mode
    cmp #M_FIGHT
    bne !+
    jsr hud_draw
    jmp !d+
!:  jsr menu_draw
!d:
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
#if AUTOTEST_KO2
    lda at_frame+1                      // Konrad: after the walk-in, kick every 16 frames while walking forward
    bne !k+
    lda at_frame
    cmp #196
    bcc !+
!k: lda at_frame
    and #16
    asl                                 // JOY_B2
    ora #JOY_LEFT
    sta at_j2
!:
#endif
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
#if AUTOTEST_SPAR
    lda f_anim                          // freeze as soon as Tiago shows the guard pose
#if AUTOTEST_SPAR_LOW
    cmp #ANIM_C_BLOCK
#else
    cmp #ANIM_BLOCK
#endif
    bne !+
    lda f_stun                          // the pose, not a blockstun after the hit
    bne !+
    inc at_guard
    lda at_guard
    cmp #3                              // a few frames into the guard
    bne !+
    lda #1
    sta at_freeze
!:  lda #1                              // the sparring partner plays Konrad (player 2)
    sta spar_mode
    lda at_frame+1
    bne !s+
    lda at_frame
    cmp #150
    bcc !+
!s: jsr spar_update
!:
#endif
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
at_guard:  .byte 0
.macro AtEvent(frame, j1, j2) { .word frame
    .byte j1, j2 }
at_script:
#if AUTOTEST_INTRO
    AtEvent(60, $ff, 0)                                  // "ROUND 1" banner
#elif AUTOTEST_MENU
    // Stage 6: title -> selection (player 1 takes Konrad, player 2 too: mirror match) -> versus -> fight
#if AUTOTEST_MENU_T
    AtEvent(60, $ff, 0)
#endif
    AtEvent(80, JOY_FIRE, 0)
    AtEvent(82, 0, 0)
    AtEvent(100, JOY_RIGHT, 0)
    AtEvent(102, 0, 0)
    AtEvent(110, JOY_FIRE, 0)
    AtEvent(112, 0, 0)
#if AUTOTEST_MENU_S
    AtEvent(116, $ff, 0)
#endif
    AtEvent(120, 0, JOY_FIRE)
    AtEvent(122, 0, 0)
#if AUTOTEST_MENU_V
    AtEvent(240, $ff, 0)
#endif
    AtEvent(560, $ff, 0)
#elif AUTOTEST_JUMP
    AtEvent(150, JOY_RIGHT, 0)                            // Tiago walks in
    AtEvent(176, JOY_UP | JOY_RIGHT, 0)                   // jumps forward
    AtEvent(178, 0, 0)
    AtEvent(186, JOY_B2, 0)                               // flying kick
    AtEvent(188, 0, 0)
    AtEvent(194, $ff, 0)
#elif AUTOTEST_WALK
    AtEvent(150, JOY_RIGHT, JOY_LEFT)                     // both walk forward for 40 frames (Stage 4b)
    AtEvent(190, $ff, 0)
#elif AUTOTEST_WALKB
    AtEvent(150, JOY_LEFT, JOY_RIGHT)                     // both walk back for 40 frames
    AtEvent(190, $ff, 0)
#elif AUTOTEST_SPAR
    AtEvent(150, JOY_LEFT, 0)                             // Tiago holds back, Konrad = sparring partner
#if AUTOTEST_SPAR_LOW
    AtEvent(152, JOY_LEFT | JOY_DOWN, 0)                  // down-back (freezes in the crouching guard)
#endif
    AtEvent(1500, $ff, 0)
#elif AUTOTEST_KO
    AtEvent(150, JOY_RIGHT, 0)                            // Tiago walks in, then keeps kicking
#if AUTOTEST_LONG
    AtEvent(1780, $ff, 0)                                // Stage 6: match won, selection, versus screen
#else
    AtEvent(620, $ff, 0)
#endif
#elif AUTOTEST_KO2
    AtEvent(150, 0, JOY_LEFT)                             // Konrad walks in, then keeps kicking
    AtEvent(900, $ff, 0)
#elif AUTOTEST_QCF
    AtEvent(150, JOY_RIGHT, 0)                            // Tiago walks in (Stage 5)
    AtEvent(176, JOY_DOWN, 0)                             // quarter circle forward ...
    AtEvent(180, JOY_DOWN | JOY_RIGHT, 0)
    AtEvent(184, JOY_DOWN | JOY_RIGHT | JOY_B2, 0)        // kick pressed early, at down-forward (sweep starts)
    AtEvent(185, JOY_RIGHT | JOY_B2, 0)                   // forward: the sweep becomes the meia-lua de compasso
    AtEvent(189, 0, 0)
#if AUTOTEST_LATE
    AtEvent(240, $ff, 0)                                  // Konrad on the floor
#else
    AtEvent(199, $ff, 0)                                  // the kick lands
#endif
#elif AUTOTEST_CHARGE
    AtEvent(150, 0, JOY_LEFT)                             // Konrad walks in (Stage 5)
    AtEvent(190, 0, JOY_RIGHT | JOY_DOWN)                 // charges down-back ...
    AtEvent(234, 0, 0)                                    // ... through neutral (as on a pad) ...
    AtEvent(237, 0, JOY_LEFT)                             // ... forward
    AtEvent(238, 0, JOY_LEFT | JOY_FIRE)                  // ... + punch: Rammbock
    AtEvent(240, 0, 0)
#if AUTOTEST_LATE
    AtEvent(293, $ff, 0)
#else
    AtEvent(249, $ff, 0)
#endif
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
name_tgfx: .text "T-TITLE-GFX,S,R"
name_tgfx_end:
name_tmap: .text "T-TITLE-MAP,S,R"
name_tmap_end:
name_f1:   .text "F-TIAGO,S,R"
name_f1_end:
#if AUTOTEST_LOADFAIL
name_f2:   .text "F-MISSING,S,R"         // test build: a load error under the title
#else
name_f2:   .text "F-KONRAD,S,R"
#endif
name_f2_end:
name_music: .text "MUSIC,S,R"
name_music_end:
msg_attic: .text "WORLDFIGHT65 NEEDS ATTIC RAM (MEGA65 R3 OR NEWER)."
           .byte 13, 0

#import "loader.asm"
#import "system.asm"
#import "video.asm"
#import "pixie.asm"
#import "fighter.asm"
#import "game.asm"
#import "fx.asm"
#import "sparring.asm"
#import "menu.asm"
#import "sound.asm"
#import "../build/gen/assets.inc"
#import "../build/gen/texts.inc"

pal_buf: .fill MAP_PAL_BYTES, 0
hud_gfx: .import binary "../build/gen/HUD.bin"
job_hud: DmaJob(DMA_CMD_COPY, hud_gfx, HUD_GFX, 17 * 64)
font_gfx: .import binary "../build/gen/FONT.bin"
job_font: DmaJob(DMA_CMD_COPY, font_gfx, FONT_GFX, 80 * 64)
fx_gfx: .import binary "../build/gen/FX.bin"
job_fx: DmaJob(DMA_CMD_COPY, fx_gfx, FX_GFX, 5 * FX_GLYPHS * 64)

prg_end:
.errorif * > $c000, "program must end below $C000"

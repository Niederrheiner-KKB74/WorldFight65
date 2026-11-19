// ----------------------------------------------------------------------------
// Stage 6: game flow around the fight - title, fighter selection, versus screen.
//   title --fire--> select --both ready--> versus --VERSUS_TIME--> fight (game.asm)
//   fight: match won --MATCH_END--> select
// All fighter packages are loaded at start into attic RAM (docs/design.md §3.2), so choosing a fighter
// only changes f_id (the index into the data tables) and the palette - no disk access here.
// The menus read the joysticks through f_joy like the fight does; the screens are the arena backdrop with
// the 16x16 font (placeholder until the owner's title picture and portraits arrive).
// ----------------------------------------------------------------------------

// game modes M_TITLE .. M_FIGHT: main.asm
.const READY_WAIT  = 50         // frames after both players are ready
.const VERSUS_TIME = 150        // frames on the versus screen
.const SEL_X0 = 96              // fighters' anchors on the select and versus screens
.const SEL_X1 = 224

title_enter:
    lda #MUS_TITLE              // title music, also during the selection and the versus screen
    jsr music_play
    lda #M_TITLE
    sta g_mode
    lda #0
    sta m_timer
    sta fx_on
    rts

select_enter:
    lda g_mode                  // back from a match: the title music again
    cmp #M_FIGHT
    bne !+
    lda #MUS_TITLE
    jsr music_play
!:  lda #M_SELECT
    sta g_mode
    lda #0
    sta m_timer
    sta m_ok
    sta m_ok+1
    sta fx_on
    jsr round_init              // standing at the start positions, facing each other, idle
    jmp fighter_palettes

versus_enter:
    lda #M_VERSUS
    sta g_mode
    lda #0
    sta m_timer
    ldx #1
!:  lda #ST_IDLE
    jsr set_state
    dex
    bpl !-
    lda #SFX_SPECIAL
    jmp sfx_play

// once per frame, from game_update while g_mode != M_FIGHT
menu_update:
    ldx #1                      // button and direction edges of both ports
!:  lda f_joy,x
    eor m_prev,x
    and f_joy,x
    sta m_press,x
    lda f_joy,x
    sta m_prev,x
    dex
    bpl !-
    inc m_timer
    ldy g_mode
    beq m_title
    cpy #M_SELECT
    beq m_select
    jmp m_versus

m_title:
    lda m_press
    ora m_press+1
    and #JOY_FIRE | JOY_B2
    beq !+
    lda #SFX_HIT_HEAVY
    jsr sfx_play
    jmp select_enter
!:  rts

// Left / right changes the fighter, a button confirms (win pose). Once player 1 is ready, his joystick
// also chooses for player 2 (solo tests until the CPU opponent of Stage 7).
m_select:
    ldx #0
    jsr sel_player
    ldx #1
    jsr sel_player
    lda m_ok
    and m_ok+1
    beq !+
    lda m_wait                  // both ready: a moment in the win pose, then the versus screen
    cmp #READY_WAIT
    bcc !w+
    jmp versus_enter
!w: inc m_wait
    rts
!:  lda #0
    sta m_wait
    rts

sel_player:
    lda m_press,x
    cpx #0
    beq !+
    ldy m_ok                    // player 2 not ready yet, player 1 ready: both ports choose for him
    beq !+
    ora m_press
!:  sta tmp
    lda m_ok,x
    bne !anim+
    lda tmp
    and #JOY_FIRE | JOY_B2
    beq !+
    lda #1
    sta m_ok,x
    lda #0                      // the press is used up (it must not confirm player 2 as well)
    sta m_press
    lda #SFX_HIT_HEAVY
    jsr sfx_play
    lda #ST_WIN
    jsr set_state
    jmp !anim+
!:  lda tmp
    and #JOY_LEFT | JOY_RIGHT
    beq !anim+
    and #JOY_RIGHT
    beq !left+
    inc f_id,x                  // next fighter
    lda f_id,x
    cmp #FIGHTER_COUNT
    bcc !ch+
    lda #0
    sta f_id,x
    beq !ch+
!left:
    dec f_id,x                  // previous fighter
    bpl !ch+
    lda #FIGHTER_COUNT - 1
    sta f_id,x
!ch:
    lda #SFX_SWING_LIGHT
    jsr sfx_play
    lda #ST_IDLE                // restart the animation with the frames of the new fighter
    jsr set_state
    jsr fighter_palettes
!anim:
    jmp anim_step

m_versus:
    ldx #0
    jsr anim_step
    ldx #1
    jsr anim_step
    lda m_timer
    cmp #VERSUS_TIME
    bcc !+
    lda #M_FIGHT
    sta g_mode
    lda #MUS_FIGHT
    jsr music_play
    jmp game_init
!:  rts

// ---------------------------------------------------------------- drawing (instead of hud_draw)
menu_draw:
    lda g_mode
    bne !+
    // title
    lda #<txt_title1
    ldy #>txt_title1
    ldx #6
    jsr text_centre
    lda #<txt_title2
    ldy #>txt_title2
    ldx #9
    jsr text_centre
    lda m_timer                 // "PRESS FIRE" blinks
    and #32
    bne !r+
    lda #<txt_press
    ldy #>txt_press
    ldx #16
    jmp text_centre
!r: rts
!:  cmp #M_SELECT
    bne !vs+
    lda #<txt_choose
    ldy #>txt_choose
    ldx #0
    jsr text_centre
    lda #<txt_fighter
    ldy #>txt_fighter
    ldx #2
    jsr text_centre
    ldx #0
    jsr sel_header
    ldx #1
    jsr sel_header
    ldx #6
    jmp names_draw
!vs:
    ldx #4
    jsr names_draw
    lda #<txt_vs
    ldy #>txt_vs
    ldx #2
    jmp text_centre

// "1P" / "2P" above player X, or "READY" once he has chosen
sel_header:
    stx m_who
    lda m_ok,x
    beq !+
    lda #<txt_ready
    ldy #>txt_ready
    jmp !d+
!:  lda p_txt_lo,x
    ldy p_txt_hi,x
!d: sta tx_ptr
    sty tx_ptr+1
    ldx m_who
    lda sel_cx,x
    ldx #4
    jmp text_at
p_txt_lo: .byte <txt_p1, <txt_p2
p_txt_hi: .byte >txt_p1, >txt_p2

// names in rows X/X+1, countries two rows below, centred over the fighters
names_draw:
    stx m_row
    ldx #0
    jsr !one+
    ldx #1
!one:
    stx m_who
    ldy f_id,x
    lda name_lo,y
    sta tx_ptr
    lda name_hi,y
    sta tx_ptr+1
    lda sel_cx,x
    ldx m_row
    jsr text_at
    ldx m_who
    ldy f_id,x
    lda country_lo,y
    sta tx_ptr
    lda country_hi,y
    sta tx_ptr+1
    lda sel_cx,x
    ldx m_row
    inx
    inx
    jmp text_at
sel_cx: .byte SEL_X0, SEL_X1

// text A/Y centred on the screen in rows X/X+1
text_centre:
    sta tx_ptr
    sty tx_ptr+1
    lda #160
    // fall through
// text at tx_ptr centred on logical x A in rows X/X+1
text_at:
    sta tmp+1
    ldy #0
    lda (tx_ptr),y
    asl
    asl
    asl
    sta tmp
    lda tmp+1
    clc
    adc #GOTOX_BIAS
    sec
    sbc tmp
    sta tx_x
    jmp text_draw_ptr

g_mode:  .byte M_TITLE
m_timer: .byte 0
m_wait:  .byte 0
m_ok:    .fill 2, 0
m_prev:  .fill 2, 0
m_press: .fill 2, 0
m_who:   .byte 0
m_row:   .byte 0

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

// Every screen starts with all buttons and directions counted as held: only a new press after a release
// counts (owner report 2026-11-20: the title was skipped at once on hardware), and the title ignores
// the joysticks for TITLE_LOCK frames.
.const TITLE_LOCK = 50
menu_hold:
    lda #$ff
    sta m_prev
    sta m_prev+1
    rts

title_enter:
    jsr menu_hold
    lda #TITLE_LOCK
    sta m_lock
    lda #MUS_TITLE              // title music, also during the selection and the versus screen
    jsr music_play
    lda #1                      // the owner's title picture
    jsr show_picture
    lda #M_TITLE
    sta g_mode
    lda #0
    sta m_timer
    sta fx_on
    rts

select_enter:
    jsr menu_hold
    lda g_mode                  // back from a match: the title music again
    cmp #M_WINNER
    bne !+
    lda #MUS_TITLE
    jsr music_play
    jmp !a+                     // (the arena is already shown)
!:  lda #PIC_RIO                // from the title: the arena again
    jsr show_picture
!a: lda #M_SELECT
    sta g_mode
    lda #0
    sta m_timer
    sta m_ok
    sta m_ok+1
    sta fx_on
    jsr round_init              // standing at the start positions, facing each other, idle
    jmp fighter_palettes

versus_enter:
    // Stage 8: the fight takes place in the home arena of player 2's fighter (the challenger visits
    // player 1's opponent); in a mirror match the arena changes with every match. The versus screen
    // already shows it.
    ldy f_id+1
    lda ft_home,y
    ldy f_id
    cpy f_id+1
    bne !+
    inc m_match
    lda m_match
    and #1
!:  tay
    lda arena_pic,y
    jsr show_picture
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

// Stage 9: winner screen - the winner alone in the middle of the arena in his win pose, "CHAMPION",
// name and country, a short fanfare; a button (after WIN_LOCK frames) or WIN_TIME frames: the selection.
.const WIN_LOCK = 75
.const WIN_TIME = 255
winner_enter:
    jsr menu_hold
    lda #M_WINNER
    sta g_mode
    lda #0
    sta m_timer
    sta fx_on
    ldx g_winner
    stx w_who
    lda #<160                   // the winner in the middle, facing right
    sta f_x_lo,x
    lda #>160
    sta f_x_hi,x
    lda #0
    sta f_y,x
    sta f_facing,x
    lda #ST_WIN
    jsr set_state
    txa                         // the loser leaves the screen (clipped by the pixie emitter)
    eor #1
    tax
    lda #<500
    sta f_x_lo,x
    lda #>500
    sta f_x_hi,x
    lda #ST_IDLE
    jsr set_state
    lda #MUS_WIN
    jmp music_play

m_winner:
    ldx w_who
    jsr anim_step
    lda m_timer
    cmp #WIN_TIME
    bcs !go+
    cmp #WIN_LOCK
    bcc !+
    lda m_press
    ora m_press+1
    and #JOY_FIRE | JOY_B2
    beq !+
!go:
    jmp select_enter
!:  rts

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
    cpy #M_WINNER
    bne !+
    jmp m_winner
!:  jmp m_versus

m_title:
    lda m_lock
    beq !l+
    dec m_lock
    rts
!l: lda m_press+1               // Stage 7: fire on joystick 2 - a second player instead of the CPU
    and #JOY_FIRE | JOY_B2
    beq !+
    lda #0
    sta cpu_on+CPU_P
!:  lda m_press
    ora m_press+1
    and #JOY_FIRE | JOY_B2
    beq !+
    lda #SFX_HIT_HEAVY
    jsr sfx_play
    jmp select_enter
!:  rts

// Left / right changes the fighter, a button confirms (win pose). Player 2 is the CPU (Stage 7) until
// joystick 2 is used here; once player 1 is ready, his joystick chooses the CPU's fighter, up / down its
// level. With a human player 2, joystick 1 can still choose for him after player 1 is ready.
m_select:
    lda m_press+1               // joystick 2 moved or pressed: a human player 2
    beq !+
    lda cpu_on+CPU_P
    beq !+
    lda #0
    sta cpu_on+CPU_P
    sta m_press+1               // this press only takes over the side
!:  ldx #0
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
    cpx #CPU_P                  // CPU level with up / down
    bne !+
    lda cpu_on+CPU_P
    beq !+
    lda tmp
    and #JOY_UP | JOY_DOWN
    beq !+
    and #JOY_UP
    bne !up+
    lda cpu_level+CPU_P
    cmp #2
    bcs !+
    inc cpu_level+CPU_P
    bne !lv+
!up:
    lda cpu_level+CPU_P
    beq !+
    dec cpu_level+CPU_P
!lv:
    lda #SFX_BLOCK
    jsr sfx_play
!:  lda tmp
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
    bne md_menu
    // title
    lda #<txt_title1
    ldy #>txt_title1
    ldx #1
    jsr text_centre
    lda #<txt_title2
    ldy #>txt_title2
    ldx #4
    jsr text_centre
    lda m_loading               // while the rest loads: "LOADING"
    beq !+
    lda #<txt_loading
    ldy #>txt_loading
    ldx #21
    jmp text_centre
!:  lda m_timer                 // "PRESS FIRE" blinks
    and #32
    bne !r+
    lda #<txt_press
    ldy #>txt_press
    ldx #21
    jmp text_centre
!r: rts
md_menu:
    cmp #M_WINNER
    bne !+
    jmp winner_draw
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

winner_draw:
    lda #<txt_winner
    ldy #>txt_winner
    ldx #1
    jsr text_centre
    ldx w_who
    ldy f_id,x
    lda name_lo,y
    sta tx_ptr
    lda name_hi,y
    sta tx_ptr+1
    lda #160
    ldx #4
    jsr text_at
    ldx w_who
    ldy f_id,x
    lda country_lo,y
    sta tx_ptr
    lda country_hi,y
    sta tx_ptr+1
    lda #160
    ldx #6
    jsr text_at
    lda m_timer                 // "PRESS FIRE" once a button counts
    cmp #WIN_LOCK
    bcc !+
    and #32
    bne !+
    lda #<txt_press
    ldy #>txt_press
    ldx #21
    jmp text_centre
!:  rts

// "1P" / "2P" above player X, or "READY" once he has chosen
sel_header:
    stx m_who
    lda m_ok,x
    beq !+
    lda #<txt_ready
    ldy #>txt_ready
    jmp !d+
!:  cpx #CPU_P                  // Stage 7: "CPU EASY" / "CPU NORMAL" / "CPU HARD"
    bne !+
    lda cpu_on+CPU_P
    beq !+
    ldy cpu_level+CPU_P
    lda cpu_txt_lo,y
    pha
    lda cpu_txt_hi,y
    tay
    pla
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
cpu_txt_lo: .byte <txt_cpu0, <txt_cpu1, <txt_cpu2
cpu_txt_hi: .byte >txt_cpu0, >txt_cpu1, >txt_cpu2

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
m_loading: .byte 0
m_lock:  .byte 0
w_who:   .byte 0                 // the winner (Stage 9)
m_match: .byte 0                // mirror matches so far (Stage 8)
arena_pic: .byte PIC_RIO, PIC_ZOLL // arena number (ft_home) -> picture
m_row:   .byte 0

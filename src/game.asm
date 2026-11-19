// ----------------------------------------------------------------------------
// Match flow and HUD (Stage 3): best of three rounds, 99-second round timer,
// "ROUND n" / "FIGHT!" / "K.O." / "TIME" / "DRAW" / "<NAME> WINS" banners,
// energy bars, timer, names and round markers. Text uses the 16x16 font
// (two NCM glyphs per character, tools/make_assets.py).
// ----------------------------------------------------------------------------

.const G_INTRO   = 0
.const G_FIGHT   = 1
.const G_KO      = 2
.const G_TIMEUP  = 3
.const G_MATCH   = 4
.const SECOND    = 50           // frames per timer second
.const INTRO_FIGHT = 90         // intro: "ROUND n" until this frame, then "FIGHT!"
.const INTRO_END = 140
.const END_WIN   = 70           // after KO / time up: the winner celebrates from this frame
.const END_NEXT  = 220          // ... and the next round starts here
.const MATCH_END = 300
.const BANNER_ROW = 8

game_init:
    lda #0
    sta g_wins
    sta g_wins+1
    lda #1
    sta g_round
    // fall through
round_start:
    jsr round_init
    lda #99
    sta g_clock
    lda #0
    sta g_sub
    sta g_input
    sta g_banner2
    lda #G_INTRO
    sta g_state
    jsr g_timer0
    ldx g_round                 // "ROUND n"
    lda round_txt_lo-1,x
    ldy round_txt_hi-1,x
    jmp set_banner
round_txt_lo: .byte <txt_round1, <txt_round2, <txt_round3
round_txt_hi: .byte >txt_round1, >txt_round2, >txt_round3

g_timer0:
    lda #0
    sta g_timer
    sta g_timer+1
    rts

// A/Y = text (lo/hi) for the banner line, 0/0 = none
set_banner:
    sta g_banner
    sty g_banner+1
    rts

// once per frame
game_update:
    lda g_mode                  // Stage 6: title, selection and versus screen (menu.asm)
    cmp #M_FIGHT
    beq !+
    jmp menu_update
!:  inc g_timer
    bne !+
    inc g_timer+1
!:  ldy g_state
    lda gs_lo,y
    sta gs_jmp+1
    lda gs_hi,y
    sta gs_jmp+2
gs_jmp:
    jmp $ffff
gs_lo: .byte <g_intro, <g_fight, <g_end, <g_end, <g_match
gs_hi: .byte >g_intro, >g_fight, >g_end, >g_end, >g_match

g_intro:
    lda g_timer
    cmp #INTRO_FIGHT
    bne !+
    lda #SFX_FIGHT              // Stage 5
    jsr sfx_play
    lda #<txt_fight
    ldy #>txt_fight
    jmp set_banner
!:  cmp #INTRO_END
    bne !+
    lda #G_FIGHT
    sta g_state
    lda #1
    sta g_input
    lda #0
    tay
    jmp set_banner
!:  rts

g_fight:
    inc g_sub
    lda g_sub
    cmp #SECOND
    bcc !+
    lda #0
    sta g_sub
    dec g_clock
    bne !+
    lda #G_TIMEUP               // time up
    sta g_state
    lda #0
    sta g_input
    jsr g_timer0
    lda #<txt_time
    ldy #>txt_time
    jsr set_banner
    // winner: more energy; equal: nobody
    lda #$ff
    sta g_winner
    lda f_health
    cmp f_health+1
    beq !+
    lda #0
    bcs !w+
    lda #1
!w: sta g_winner
!:  rts

// called by land_hit when fighter X is knocked out
game_ko:
    lda #SFX_KO                 // Stage 5
    jsr sfx_play
    lda #G_KO
    sta g_state
    lda #0
    sta g_input
    txa
    eor #1
    sta g_winner
    jsr g_timer0
    lda #<txt_ko
    ldy #>txt_ko
    jmp set_banner

// after KO / time up: the winner celebrates, then the round is counted
g_end:
    lda g_timer+1
    bne !next+
    lda g_timer
    cmp #END_WIN
    bcc !done+
    bne !+
    lda g_state                 // time up without a winner: "DRAW"
    cmp #G_TIMEUP
    bne !+
    lda g_winner
    bpl !+
    lda #<txt_draw
    ldy #>txt_draw
    jsr set_banner
!:  ldx g_winner                // the winner strikes the win pose once he is back on his feet
    bmi !+
    lda f_state,x
    cmp #ST_ATTACK
    bcc !w+
    cmp #ST_CROUCH
    beq !w+
    cmp #ST_BLOCK
    bcc !+
    cmp #ST_KNOCK
    bcs !+
!w: lda #0
    sta f_y,x
    lda #ST_WIN
    jsr set_state
!:  lda g_timer
    cmp #END_NEXT
    bcc !done+
!next:
    ldx g_winner                // count the round
    bmi !round+
    inc g_wins,x
    lda g_wins,x
    cmp #2
    bcc !round+
    lda #G_MATCH                // match won: "<NAME>" / "WINS"
    sta g_state
    jsr g_timer0
    ldy f_id,x
    lda name_lo,y
    pha
    lda name_hi,y
    tay
    pla
    jsr set_banner
    lda #1
    sta g_banner2
    rts
!round:
    lda g_round
    cmp #3
    bcs !+
    inc g_round
!:  jmp round_start
!done:
    rts

g_match:
    lda g_timer+1
    beq !+
    lda g_timer
    cmp #<MATCH_END
    bcc !+
    jmp select_enter            // Stage 6: back to the fighter selection
!:  rts

// ---------------------------------------------------------------- HUD
hud_draw:
    ldx #0
    jsr hud_bar
    ldx #1
    jsr hud_bar
    // timer: two digits between the bars
    lda g_clock
    ldx #0
!:  cmp #10
    bcc !+
    sbc #10
    inx
    bne !-
!:  clc
    adc #1                      // font index of the digit
    sta clk_txt+2
    inx
    stx clk_txt+1
    lda #<clk_txt
    ldy #>clk_txt
    ldx #<(144 + GOTOX_BIAS)
    stx tx_x
    ldx #1
    jsr text_draw
    // names under the bars: fighter 0 at the left, fighter 1 right-aligned
    ldy f_id
    lda name_lo,y
    sta tx_ptr
    lda name_hi,y
    sta tx_ptr+1
    lda #<(12 + GOTOX_BIAS)
    sta tx_x
    ldx #2
    jsr text_draw_ptr
    ldy f_id+1
    lda name_lo,y
    sta tx_ptr
    lda name_hi,y
    sta tx_ptr+1
    ldy #0                      // x = 308 - 16 * length
    lda (tx_ptr),y
    asl
    asl
    asl
    asl
    sta tmp
    lda #<(308 + GOTOX_BIAS)
    sec
    sbc tmp
    sta tx_x
    ldx #2
    jsr text_draw_ptr
    // round markers: a star for every won round, next to the timer
    lda g_wins
    beq !+
    sta star_txt
    lda #<(108 + GOTOX_BIAS)
    sta tx_x
    lda #<star_txt
    ldy #>star_txt
    ldx #3
    jsr text_draw
!:  lda g_wins+1
    beq !+
    sta star_txt
    lda #<(180 + GOTOX_BIAS)
    sta tx_x
    lda #<star_txt
    ldy #>star_txt
    ldx #3
    jsr text_draw
!:  // banner in the middle of the screen
    lda g_banner+1
    beq !+
    sta tx_ptr+1
    lda g_banner
    sta tx_ptr
    jsr center_x
    ldx #BANNER_ROW
    jsr text_draw_ptr
    lda g_banner2               // second line: "WINS"
    beq !+
    lda #<txt_wins
    sta tx_ptr
    lda #>txt_wins
    sta tx_ptr+1
    jsr center_x
    ldx #BANNER_ROW + 2
    jsr text_draw_ptr
!:  rts

// tx_x = centre position for the text at tx_ptr: 160 - 8 * length
center_x:
    ldy #0
    lda (tx_ptr),y
    asl
    asl
    asl
    sta tmp
    lda #<(160 + GOTOX_BIAS)
    sec
    sbc tmp
    sta tx_x
    rts

// Text at A/Y (lo/hi, length-prefixed font indices) in rows X and X+1 at logical x tx_x (+ bias, < 256).
text_draw:
    sta tx_ptr
    sty tx_ptr+1
text_draw_ptr:
    stx tx_row
    ldy #0
    lda (tx_ptr),y
    sta tx_len
    asl
    clc
    adc #2
    sta px_need
    lda #0                      // top halves (glyph 2k), then bottom halves (2k+1)
    sta tx_half
!line:
    lda tx_row
    clc
    adc tx_half
    sta px_row
    lda tx_x
    sta px_gx
    lda #0
    sta px_gx+1
    lda #$10
    sta px_yb
    jsr frag_begin
    bcs !next+
    ldy #1
!ch:
    lda (tx_ptr),y
    asl
    clc
    adc tx_half
    clc
    adc #<FONT_CHAR
    sta ((scr_ptr)),z
    lda #$08
    sta ((col_ptr)),z
    inz
    lda #>FONT_CHAR
    adc #0
    sta ((scr_ptr)),z
    lda #(HUD_BANK << 4) | $0f
    sta ((col_ptr)),z
    inz
    iny
    dec tx_len
    bne !ch-
    ldy #0
    lda (tx_ptr),y
    sta tx_len
    ldz #0
!next:
    inc tx_half
    lda tx_half
    cmp #2
    bne !line-
    rts
.errorif (FONT_CHAR & $ff) + 2 * 40 > $ff, "font glyphs must not cross a 256-character boundary"

// energy bar of fighter X: row HUD_ROW, fighter 0 at x 12..139 (fills from the left),
// fighter 1 at x 180..307 (mirrored: fills from the right); glyph k = k pixels filled
hud_bar:
    stx hb_fighter
    lda #HUD_ROW
    sta px_row
    lda #9 * 2
    sta px_need
    lda hud_x,x
    sta px_gx
    lda #0
    sta px_gx+1
    lda #$10                    // GOTOX, Y offset 0
    sta px_yb
    jsr frag_begin              // Z = 2 after the GOTOX token
    bcs !out+
    ldx hb_fighter
    lda f_health,x
    sta tmp
    lda #$08
    cpx #0
    beq !+
    lda #$48                    // fighter 1: mirrored glyphs
!:  sta px_c0
    ldy #0                      // screen column 0..7
!seg:
    tya                         // segment: column (fighter 0), 7 - column (fighter 1)
    ldx hb_fighter
    beq !+
    eor #7
!:  asl                         // amount = clamp(health - 16 * segment, 0, 16)
    asl
    asl
    asl
    sta tmp+1
    lda tmp
    sec
    sbc tmp+1
    bcs !+
    lda #0
!:  cmp #17
    bcc !+
    lda #16
!:  clc
    adc #<HUD_CHAR
    sta ((scr_ptr)),z
    lda px_c0
    sta ((col_ptr)),z
    inz
    lda #>HUD_CHAR
    adc #0
    sta ((scr_ptr)),z
    lda #(HUD_BANK << 4) | $0f
    sta ((col_ptr)),z
    inz
    iny
    cpy #8
    bne !seg-
    ldz #0
!out:
    rts
hud_x: .byte 12 + GOTOX_BIAS, 180 + GOTOX_BIAS
.errorif (HUD_CHAR & $ff) > $ff - 16, "HUD glyphs must not cross a 256-character boundary"

clk_txt:  .byte 2, 0, 0
star_txt: .byte 0, 39, 39               // 1 or 2 stars ('*' is font index 39)
g_state:   .byte 0
g_timer:   .word 0
g_round:   .byte 1
g_wins:    .fill 2, 0
g_clock:   .byte 99
g_sub:     .byte 0
g_input:   .byte 0
g_winner:  .byte 0
g_banner:  .word 0
g_banner2: .byte 0
hb_fighter: .byte 0
tx_x:      .byte 0
tx_row:    .byte 0
tx_len:    .byte 0
tx_half:   .byte 0

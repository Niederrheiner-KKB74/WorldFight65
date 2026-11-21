// ----------------------------------------------------------------------------
// Stage 7: the CPU opponent. It plays player 2 and only writes his virtual joystick (f_joy+1), exactly
// like a human on joystick 2 (CLAUDE.md rule 9) - the fighter code does not know who is playing.
// It reads the same game state a player sees: distance, the other fighter's state and move, its own
// state. Move reaches come from the fighter data (mv_reach, measured on the art by make_assets.py), so
// the CPU works for every fighter package without fighter-specific code.
//
// Every frame: (1) in the air: jump attack when close and falling; (2) reaction: when the other fighter
// starts an attack nearby, after a reaction time the CPU blocks with a level-dependent chance (low moves
// crouching); (3) otherwise it carries on with its current action, and when that ends it decides anew:
// walk in, keep the distance, guard, jump in, attack with a move that reaches, or its special move.
// Three levels (easy / normal / hard), chosen on the selection screen.
// ----------------------------------------------------------------------------

// CPU_P (main.asm): the CPU plays player 2

.const A_IDLE   = 0             // actions
.const A_FWD    = 1
.const A_BACK   = 2             // standing guard / walking back
.const A_CBACK  = 3             // crouching guard
.const A_ATK    = 4             // press cpu_joy for 3 frames, then wait
.const A_JUMP   = 5             // jump forward
.const A_QCF    = 6             // down, down-forward, forward + button
.const A_CHARGE = 7             // down-back CHARGE_T + 2 frames, then forward + button

// level tables: [easy, normal, hard]
lv_block:   .byte 70, 140, 210  // block chance of 256 when an attack is seen
lv_react:   .byte 14, 8, 3      // shortest reaction time in frames ...
lv_rrange:  .byte 15, 7, 3      // ... plus random 0..range (mask)
lv_think:   .byte 20, 10, 4     // pause after an action (random 0..value)
lv_aggr:    .byte 90, 150, 200  // chance of 256 to attack when a move reaches

cpu_on:     .byte 1             // 1: player 2 is the CPU (until joystick 2 is used on the selection screen)
cpu_level:  .byte 1
cpu_act:    .byte 0
cpu_t:      .byte 0             // frames done in the current action
cpu_len:    .byte 0             // length of the current action
cpu_joy:    .byte 0             // attack: direction + button (forward resolved per frame: bit 7)
cpu_react:  .byte 0             // frames until the CPU reacts to the attack it saw (0 = none pending)
cpu_seen:   .byte 0             // the other fighter was attacking last frame
cpu_dx:     .byte 0             // distance in pixels (255 = far)
cpu_seed:   .byte $5a
.const C_FWD = $80              // in cpu_joy: "forward", resolved by the facing

// at the start of every round (game.asm)
cpu_reset:
    lda #A_IDLE
    sta cpu_act
    lda #20
    sta cpu_len
    lda #0
    sta cpu_t
    sta cpu_react
    sta cpu_seen
    lda VIC_RASTER              // a little randomness from where the raster is
    eor cpu_seed
    ora #1
    sta cpu_seed
    rts

// 8-bit Galois LFSR -> A
cpu_rnd:
    lda cpu_seed
    asl
    bcc !+
    eor #$1d
!:  sta cpu_seed
    rts

// once per frame in the fight, after the joysticks are read (main.asm)
cpu_update:
    lda cpu_on
    bne !+
    rts
!:  ldx #CPU_P
    lda #0
    sta f_joy,x
    lda g_input                 // rounds not running: hands off
    bne !+
    rts
!:  jsr cpu_rnd                 // keep the generator moving every frame
    jsr cpu_distance
    lda f_state,x
    cmp #ST_JUMP
    bne !ground+
    // (1) in the air: attack when falling and close
    lda f_jatk,x
    bne !+
    lda f_jt,x
    cmp #JUMP_T / 2 - 4
    bcc !+
    lda cpu_dx
    cmp #64
    bcs !+
    lda #JOY_B2
    sta f_joy,x
!:  rts
!ground:
    // (2) reaction to an attack of the other fighter
    ldy #1 - CPU_P
    lda f_state,y
    cmp #ST_ATTACK
    beq !att+
    cmp #ST_JUMP
    bne !na+
    lda f_jatk,y
    bne !att+
!na:
    lda #0
    sta cpu_seen
    beq !act+
!att:
    lda cpu_seen                // a new attack: the reaction time starts
    bne !+
    lda #1
    sta cpu_seen
    lda cpu_dx
    cmp #110
    bcs !+
    ldy cpu_level
    jsr cpu_rnd
    and lv_rrange,y
    clc
    adc lv_react,y
    sta cpu_react
!:  lda cpu_react
    beq !act+
    dec cpu_react
    bne !act+
    ldy cpu_level               // reaction time over: block?
    jsr cpu_rnd
    cmp lv_block,y
    bcs !act+
    lda #A_BACK                 // stand for mid and overhead moves, crouch for low ones
    ldy #1 - CPU_P
    jsr cpu_movetab
    lda mv_height,y
    cmp #1
    bne !+
    lda #A_CBACK
    .byte $2c                   // bit abs: skip the next lda
!:  lda #A_BACK
    ldy #24
    jsr cpu_start
!act:
    // (3) the current action, or a new decision
    lda cpu_t
    cmp cpu_len
    bcc !+
    jsr cpu_decide
!:  inc cpu_t
    lda cpu_act
    asl
    tay
    lda cpu_out,y
    sta !jmp+ + 1
    lda cpu_out + 1,y
    sta !jmp+ + 2
!jmp:
    jmp $ffff

cpu_out: .word o_idle, o_fwd, o_back, o_cback, o_atk, o_jump, o_qcf, o_charge

o_idle:
    rts
o_fwd:
    jsr cpu_fwd
    sta f_joy,x
    rts
o_back:
    jsr cpu_back
    sta f_joy,x
    rts
o_cback:
    jsr cpu_back
    ora #JOY_DOWN
    sta f_joy,x
    rts
o_atk:                          // 2 frames the direction alone (a crouch move needs the crouch first),
    lda cpu_t                   // then 4 frames direction + button
    cmp #2
    bcs !+
    jsr cpu_press
    and #JOY_UP | JOY_DOWN | JOY_LEFT | JOY_RIGHT
    sta f_joy,x
    rts
!:  cmp #6
    bcs !+
    jmp cpu_press
!:  rts
o_jump:
    lda cpu_t
    cmp #3
    bcs !+
    jsr cpu_fwd
    ora #JOY_UP
    sta f_joy,x
!:  rts
o_qcf:
    lda cpu_t
    cmp #4
    bcs !+
    lda #JOY_DOWN
    sta f_joy,x
    rts
!:  cmp #8
    bcs !+
    jsr cpu_fwd
    ora #JOY_DOWN
    sta f_joy,x
    rts
!:  cmp #11
    bcs !+
    jmp cpu_press               // cpu_joy = forward + button
!:  rts
o_charge:
    lda cpu_t
    cmp #CHARGE_T + 2
    bcs !+
    jsr cpu_back
    ora #JOY_DOWN               // crouching charge: also a low guard
    sta f_joy,x
    rts
!:  cmp #CHARGE_T + 6
    bcs !+
    jmp cpu_press
!:  rts

// cpu_joy (bit 7 = forward) -> f_joy
cpu_press:
    lda cpu_joy
    bpl !+
    and #$7f
    sta tmp
    jsr cpu_fwd
    ora tmp
!:  sta f_joy,x
    rts

cpu_fwd:                        // A = the joystick bit pointing at the other fighter
    lda f_facing,x
    bne !+
    lda #JOY_RIGHT
    rts
!:  lda #JOY_LEFT
    rts
cpu_back:
    lda f_facing,x
    bne !+
    lda #JOY_LEFT
    rts
!:  lda #JOY_RIGHT
    rts

// A = action, Y = length in frames
cpu_start:
    sta cpu_act
    sty cpu_len
    lda #0
    sta cpu_t
    rts

// Y = (fighter type of fighter Y) * 16 + f_move,y  (index into the mv_* tables)
cpu_movetab:
    lda f_id,y
    asl
    asl
    asl
    asl
    clc
    adc f_move,y
    tay
    rts

// cpu_dx = |x1 - x0|, 255 when farther
cpu_distance:
    sec
    lda f_x_lo+1
    sbc f_x_lo
    sta tmp
    lda f_x_hi+1
    sbc f_x_hi
    bpl !+
    sta tmp+1
    lda #0
    sec
    sbc tmp
    sta tmp
    lda #0
    sbc tmp+1
!:  beq !+
    lda #255
    sta cpu_dx
    rts
!:  lda tmp
    sta cpu_dx
    rts

// ---------------------------------------------------------------- decisions
cpu_decide:
    ldy cpu_level               // first a short pause (thinking time), then a real action
    lda cpu_act
    cmp #A_IDLE
    beq !+
    jsr cpu_rnd
    and #15
    cmp lv_think,y
    bcs !+
    tay
    iny
    lda #A_IDLE
    jmp cpu_start
!:  ldy #1 - CPU_P              // the other fighter on the floor or getting up: come closer, wait
    lda f_state,y
    cmp #ST_KNOCK
    beq !down+
    cmp #ST_GETUP
    beq !down+
    cmp #ST_KO
    bne !+
!down:
    lda cpu_dx
    cmp #56
    bcc !w+
    lda #A_FWD
    ldy #8
    jmp cpu_start
!w: lda #A_IDLE
    ldy #8
    jmp cpu_start
!:  cmp #ST_JUMP                // the other fighter jumps in: anti-air heavy punch or guard
    bne !+
    lda cpu_dx
    cmp #90
    bcs !+
    jsr cpu_rnd
    bmi !g+
    lda #JOY_FIRE | C_FWD
    sta cpu_joy
    lda #A_ATK
    ldy #24
    jmp cpu_start
!g: lda #A_BACK
    ldy #30
    jmp cpu_start
!:  lda cpu_dx                  // far away: walk in, sometimes jump in or wait
    cmp #120
    bcc !mid+
    jsr cpu_rnd
    cmp #180
    bcs !+
    and #15
    adc #16
    tay
    lda #A_FWD
    jmp cpu_start
!:  cmp #215
    bcs !+
    lda #A_JUMP
    ldy #JUMP_T + 4
    jmp cpu_start
!:  lda #A_IDLE
    ldy #14
    jmp cpu_start
!mid:
    ldy cpu_level               // in reach of an attack: attack (chance by level)
    jsr cpu_rnd
    cmp lv_aggr,y
    bcs !noatk+
    jsr cpu_pick_attack
    bcc !noatk+
    rts
!noatk:
    jsr cpu_rnd                 // otherwise: walk in, guard, step back or jump in
    cmp #100
    bcs !+
    lda cpu_dx
    cmp #44                     // already close: guard instead
    bcc !gd+
    lda #A_FWD
    ldy #10
    jmp cpu_start
!:  cmp #190
    bcs !+
!gd:
    jsr cpu_rnd
    and #15
    adc #12
    tay
    lda #A_BACK
    jmp cpu_start
!:  cmp #225
    bcs !+
    lda #A_CBACK
    ldy #18
    jmp cpu_start
!:  lda cpu_dx
    cmp #60
    bcc !gd-
    lda #A_JUMP
    ldy #JUMP_T + 4
    jmp cpu_start

// Choose a move that reaches: start at a random place in the list and take the first one whose
// reach + the other fighter's hurt half-width covers the distance. C = 1 when an attack was started.
cpu_moves:  .byte MOVE_LP, MOVE_HP, MOVE_LK, MOVE_HK, MOVE_C_LP, MOVE_C_LK, MOVE_SWEEP, MOVE_SP1
cpu_mjoy:   .byte JOY_FIRE, JOY_FIRE | C_FWD, JOY_B2, JOY_B2 | C_FWD
            .byte JOY_FIRE | JOY_DOWN, JOY_B2 | JOY_DOWN, JOY_B2 | JOY_DOWN | C_FWD, 0
.const CPU_NMOVES = 8
cpu_pick_attack:
    jsr cpu_rnd
    and #7
    sta cpu_i
    lda #CPU_NMOVES
    sta cpu_n
!try:
    ldy cpu_i                   // reach of this move of our fighter
    lda f_id+CPU_P
    asl
    asl
    asl
    asl
    clc
    adc cpu_moves,y
    tay
    lda mv_reach,y
    ldy f_id+1-CPU_P
    clc
    adc ft_hurt_w,y
    sec
    sbc #3                      // a little safety margin
    cmp cpu_dx
    bcs !hit+
!next:
    inc cpu_i
    lda cpu_i
    and #7
    sta cpu_i
    dec cpu_n
    bne !try-
    clc
    rts
!hit:
    ldy cpu_i
    lda cpu_moves,y
    cmp #MOVE_SP1
    beq !sp+
    lda cpu_mjoy,y
    sta cpu_joy
    lda #A_ATK
    ldy #22
    jsr cpu_start
    sec
    rts
!sp:
    ldy f_id+CPU_P              // special: its motion and button from the fighter data
    lda ft_sp_button,y
    ora #C_FWD
    sta cpu_joy
    lda ft_sp_motion,y
    bne !ch+
    lda #A_QCF
    ldy #40
    jsr cpu_start
    sec
    rts
!ch:
    lda cpu_dx                  // the charge takes almost a second: only from a distance
    cmp #70
    bcc !next-
    lda #A_CHARGE
    ldy #CHARGE_T + 34
    jsr cpu_start
    sec
    rts
cpu_i: .byte 0
cpu_n: .byte 0

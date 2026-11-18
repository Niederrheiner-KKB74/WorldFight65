// WorldFight65 - sparring partner for solo tests on the real machine (Stage 4b)
//
// Key T cycles: off -> player 2 attacks by himself (border red) -> player 1 attacks by himself (border blue)
// -> off. The sparring partner only writes the virtual joystick f_joy of his fighter (docs/design.md §5),
// exactly like the later CPU opponent will: he walks up to the other fighter and then runs through all of
// his attacks, one every SPAR_PERIOD frames, so the other player can test blocking (hold back, or
// down-back for low attacks) and getting hit. Runs after read_joysticks and overwrites one port.

.const SPAR_PERIOD = 56         // frames per attack
.const SPAR_RANGE  = 76         // walks closer while the distance is larger than this

// sequence: direction (0 none, 1 forward, D = down, U = up) and buttons for phase A (frames 0-5)
// and phase B (frames 14-19, for the jump attacks); "down" is held until frame 30 for crouching moves
.const S_F = $80                // forward (resolved to left/right each frame)
spar_a: .byte JOY_FIRE                      // light punch
        .byte S_F | JOY_FIRE                // heavy punch
        .byte JOY_B2                        // light kick
        .byte S_F | JOY_B2                  // heavy kick
        .byte JOY_DOWN | JOY_FIRE           // crouching punch
        .byte JOY_DOWN | JOY_B2             // crouching kick (low)
        .byte JOY_DOWN | S_F | JOY_B2       // sweep (low, knocks down)
        .byte JOY_UP | S_F                  // jump in ...
        .byte JOY_UP | S_F                  // jump in ...
        .byte 0                             // special move (Stage 5, spar_special)
spar_b: .byte 0, 0, 0, 0, 0, 0, 0
        .byte JOY_FIRE                      // ... with a jumping punch (overhead)
        .byte JOY_B2                        // ... with a jumping kick (overhead)
        .byte 0
.const SPAR_STEPS = 10
.const SPAR_SPECIAL = 9

spar_mode: .byte 0              // 0 off, 1 = player 2 (fighter 1), 2 = player 1 (fighter 0)
spar_t:    .byte 0
spar_i:    .byte 0

// key T (from read_keys)
spar_toggle:
    lda spar_mode
    clc
    adc #1
    cmp #3
    bcc !+
    lda #0
!:  sta spar_mode
    lda #0
    sta spar_t
    sta spar_i
    ldy spar_mode
    lda spar_border,y
    sta VIC_BORDER
    rts
spar_border: .byte 0, 2, 6

spar_update:
    lda spar_mode
    bne !+
    rts
!:  ldx #1                      // X = sparring fighter, Y = the other one
    ldy #0
    cmp #1
    beq !+
    ldx #0
    ldy #1
    // forward = towards the other fighter
!:  lda #JOY_RIGHT
    sta spar_fwd
    lda f_x_hi,x
    cmp f_x_hi,y
    bne !+
    lda f_x_lo,x
    cmp f_x_lo,y
!:  bcc !+
    lda #JOY_LEFT
    sta spar_fwd
!:  // distance (16 bit, absolute) -> walk closer between attacks
    sec
    lda f_x_lo,x
    sbc f_x_lo,y
    sta tmp
    lda f_x_hi,x
    sbc f_x_hi,y
    sta tmp+1
    bpl !+
    lda #0
    sec
    sbc tmp
    sta tmp
    lda #0
    sbc tmp+1
    sta tmp+1
!:  inc spar_t
    lda spar_t
    cmp #SPAR_PERIOD
    bcc !+
    lda #0
    sta spar_t
    inc spar_i
    lda spar_i
    cmp #SPAR_STEPS
    bcc !+
    lda #0
    sta spar_i
!:  lda spar_t
    bne !go+
    lda tmp+1                   // at the start of a period: too far away -> walk, start the attack later
    bne !walk+
    lda tmp
    cmp #SPAR_RANGE
    bcc !go+
!walk:
    lda #$ff                    // stay at frame 0 of this period
    sta spar_t
    lda spar_fwd
    sta f_joy,x
    rts
!go:
    ldy spar_i
    cpy #SPAR_SPECIAL
    bne !+
    jmp spar_special
!:  lda spar_t
    cmp #6
    bcs !+
    lda spar_a,y                // phase A
    jmp spar_out
!:  cmp #14
    bcc !hold+
    cmp #20
    bcs !hold+
    lda spar_b,y                // phase B
    jmp spar_out
!hold:
    lda spar_t                  // between the phases: keep crouching for crouching moves
    cmp #30
    bcs !none+
    lda spar_a,y
    and #JOY_DOWN
    jmp spar_out
!none:
    lda #0
spar_out:
    bpl !+                      // bit 7 = forward
    and #$7f
    ora spar_fwd
!:  sta f_joy,x
    rts
spar_fwd: .byte 0

// Stage 5: the special move of the sparring fighter, entered like a player would (fighter data:
// ft_sp_motion, ft_sp_button). QCF: down 4 frames, down-forward 4, forward 4, then forward + button.
// Charge: down-back for 42 frames (crouching, so he does not walk away), then forward + button.
spar_special:
    ldy f_id,x
    lda ft_sp_motion,y
    bne !chg+
    lda spar_t
    cmp #4
    bcs !+
    lda #JOY_DOWN
    jmp spar_out
!:  cmp #8
    bcs !+
    lda #JOY_DOWN | S_F
    jmp spar_out
!:  cmp #12
    bcs !+
    lda #S_F
    jmp spar_out
!:  cmp #15
    bcs !none+
    lda #S_F
    ora ft_sp_button,y
    jmp spar_out
!chg:
    lda spar_t
    cmp #42
    bcs !+
    lda spar_fwd                // back = away from the other fighter
    eor #JOY_LEFT | JOY_RIGHT
    ora #JOY_DOWN
    sta f_joy,x
    rts
!:  cmp #45
    bcs !none+
    lda #S_F
    ora ft_sp_button,y
    jmp spar_out
!none:
    lda #0
    jmp spar_out

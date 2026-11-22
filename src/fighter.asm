// ----------------------------------------------------------------------------
// Fighters (Stage 3, sparks Stage 4): walking, crouching, jumping, blocking, standing, crouching
// and jumping attacks, hits, knockdown, getting up, KO, win pose.
// Everything is indexed by the fighter number (X = 0/1); what makes Tiago or
// Konrad different is data from tools/make_assets.py (frame, animation, box,
// move and stat tables), not code (CLAUDE.md rule 9). Each fighter reads its
// virtual joystick f_joy (docs/design.md §5): bits 0-4 as CIA (up, down, left,
// right, fire = button 1), bit 5 = button 2.
// Frames are streamed from attic RAM into two chip-RAM slots per fighter
// (confirmed on hardware in Stage 1).
// ----------------------------------------------------------------------------

.const ST_IDLE   = 0
.const ST_FWD    = 1
.const ST_BACK   = 2
.const ST_ATTACK = 3
.const ST_HIT    = 4
.const ST_KO     = 5            // knocked out: falls and stays down
.const ST_CROUCH = 6
.const ST_JUMP   = 7
.const ST_BLOCK  = 8
.const ST_CBLOCK = 9
.const ST_KNOCK  = 10           // knocked down: falls, lies, then gets up
.const ST_GETUP  = 11
.const ST_WIN    = 12
.const X_MIN = 24
.const X_MAX = 296
.const PUSH_MIN = 34            // the fighters' anchors never come closer than this (on the ground)
.const HITSTOP = 6              // frames both fighters freeze when a hit lands
.const BLOCKSTOP = 4
.const JUMP_T = 40              // frames in the air
.const JUMP_H = 60              // jump height in pixels
.const JUMP_DX = 2
.const DOWN_TIME = 50           // frames a knocked-down fighter lies on the floor (incl. the fall)
.const GETUP_TIME = 20

fighters_init:
    lda #0
    sta hitstop
    ldx #3
    lda #$ff
!:  sta slot_frame,x
    dex
    bpl !-
    ldx #1
!:  lda #0
    sta front_slot,x
    sta build_slot,x
    sta f_joy,x
    sta f_joyprev,x
    dex
    bpl !-
    lda #0                      // fighter types: 0 = Tiago (bank 12), 1 = Konrad (bank 13)
    sta f_id
    lda #1
    sta f_id+1
    rts

// start positions, full energy
round_init:
    ldx #1
!:  lda start_x_lo,x
    sta f_x_lo,x
    lda start_x_hi,x
    sta f_x_hi,x
    txa
    sta f_facing,x              // fighter 0 faces right, fighter 1 left
    ldy f_id,x
    lda ft_health,y
    sta f_health,x
    lda #0
    sta f_push,x
    sta f_stun,x
    sta f_y,x
    sta f_back,x
    sta f_down,x
    lda #ST_IDLE
    jsr set_state
    dex
    bpl !-
    lda #0
    sta hitstop
    rts
start_x_lo: .byte <96, <224
start_x_hi: .byte >96, >224

// A = new state, X = fighter: set the state and start its animation
set_state:
    sta f_state,x
    tay
    lda state_anim,y
    // fall through
// A = animation, X = fighter: start the animation at its first frame
start_anim:
    sta f_anim,x
    lda #0
    sta f_aframe,x
    sta f_tick,x
    jmp anim_frame
state_anim: .byte ANIM_IDLE, ANIM_WALK, ANIM_WALK, ANIM_IDLE, ANIM_HIT, ANIM_FALL, ANIM_CROUCH, ANIM_JUMP
            .byte ANIM_BLOCK, ANIM_C_BLOCK, ANIM_FALL, ANIM_GETUP, ANIM_WIN

// Y = fighter type * ANIM_SLOTS + animation
anim_index:
    lda f_id,x
    asl
    asl
    asl
    asl
    asl
    clc
    adc f_anim,x
    tay
    rts
.errorif ANIM_SLOTS != 32, "anim_index multiplies by 32"

// f_frame = global frame number of the current animation frame (walking back: played backwards)
anim_frame:
    jsr anim_index
    lda f_state,x
    cmp #ST_BACK
    bne !+
    lda anim_first,y            // backwards: first + len - 1 - aframe
    clc
    adc anim_len,y
    sec
    sbc #1
    sec
    sbc f_aframe,x
    sta f_frame,x
    rts
!:  lda anim_first,y
    clc
    adc f_aframe,x
    sta f_frame,x
    rts

// Advance the animation by one video frame. Idle, walking and the win pose loop; other animations
// hold their last frame. Carry set when the animation has just ended.
anim_step:
    inc f_tick,x
    ldy f_frame,x
    lda f_tick,x
    cmp frame_ticks,y
    bcc !same+
    lda #0
    sta f_tick,x
    inc f_aframe,x
    jsr anim_index
    lda f_aframe,x
    cmp anim_len,y
    bcc !next+
    lda f_state,x               // end of the animation
    cmp #ST_ATTACK
    bcc !loop+
    cmp #ST_WIN
    beq !loop+
    dec f_aframe,x              // hold the last frame
    sec
    rts
!loop:
    lda #0
    sta f_aframe,x
!next:
    jsr anim_frame
!same:
    clc
    rts

// Walking (Stage 4b): the animation is driven by the distance walked, so the feet stay on the ground
// at every speed (walking back is slower than forward). frame_ticks of walk frames hold half pixels
// (ticks x forward speed, see make_assets.py); tmp2 = half pixels walked in this video frame.
walk_step:
    clc
    lda f_tick,x
    adc tmp2
    sta f_tick,x
    ldy f_frame,x
    cmp frame_ticks,y
    bcc !same+
    sec
    sbc frame_ticks,y
    sta f_tick,x
    inc f_aframe,x
    jsr anim_index
    lda f_aframe,x
    cmp anim_len,y
    bcc !+
    lda #0
    sta f_aframe,x
!:  jsr anim_frame
!same:
    rts

// ---------------------------------------------------------------- per frame
fighters_update:
    lda hitstop                 // a hit has just landed: both freeze
    beq !+
    dec hitstop
    rts
!:  ldx #0
    jsr fighter_update
    ldx #1
    jsr fighter_update
    jmp push_apart

fighter_update:
    txa
    eor #1
    sta other
    // button edges
    lda f_joy,x
    eor f_joyprev,x
    and f_joy,x
    sta f_press
    lda f_joy,x
    sta f_joyprev,x
    sta f_hold
    lda g_input                 // no input outside the fight (intro, KO, time up)
    bne !+
    lda #0
    sta f_press
    sta f_hold
!:  // direction relative to the facing: 1 = forward, 2 = back, 0 = none
    lda f_hold
    and #JOY_LEFT | JOY_RIGHT
    ldy #0
    cmp #JOY_RIGHT
    bne !+
    ldy #1
    lda f_facing,x
    beq !d+
    ldy #2
    bne !d+
!:  cmp #JOY_LEFT
    bne !d+
    ldy #2
    lda f_facing,x
    beq !d+
    ldy #1
!d: sty f_dir
    lda #0                      // holding back (for blocking)
    cpy #2
    bne !+
    lda #1
!:  sta f_back,x
    lda f_hold
    and #JOY_DOWN
    beq !+
    lda #1
!:  sta f_down,x
    jsr motion_track            // Stage 5: special-move motions
    // dispatch on the state
    ldy f_state,x
    lda st_lo,y
    sta st_jmp+1
    lda st_hi,y
    sta st_jmp+2
st_jmp:
    jmp $ffff
st_lo: .byte <st_ground, <st_ground, <st_ground, <st_attack, <st_hit, <st_knock, <st_crouch, <st_jump
       .byte <st_block, <st_block, <st_knock, <st_getup, <anim_step
st_hi: .byte >st_ground, >st_ground, >st_ground, >st_attack, >st_hit, >st_knock, >st_crouch, >st_jump
       .byte >st_block, >st_block, >st_knock, >st_getup, >anim_step

// face the opponent (on the ground): facing = (my x >= other x)
face_other:
    ldy other
    lda f_x_hi,x
    cmp f_x_hi,y
    bne !+
    lda f_x_lo,x
    cmp f_x_lo,y
!:  lda #0
    rol
    sta f_facing,x
    rts

// ---- standing / walking
st_ground:
    jsr face_other
    jsr special_check           // Stage 5: a finished special motion + its button wins over everything
    bcc !+
    rts
!:  lda f_hold                  // jump: up, with forward or back for a jump in that direction
    and #JOY_UP
    beq !+
    jmp start_jump
!:  lda f_down,x
    beq !+
    lda #ST_CROUCH
    jmp set_state
!:  lda f_press
    and #JOY_FIRE
    beq !+
    lda #MOVE_LP                // button 1: punch, heavy when holding forward
    ldy f_dir
    cpy #1
    bne !atk+
    lda #MOVE_HP
    bne !atk+
!:  lda f_press
    and #JOY_B2
    beq !walk+
    lda #MOVE_LK                // button 2: kick, heavy when holding forward
    ldy f_dir
    cpy #1
    bne !atk+
    lda #MOVE_HK
!atk:
    jmp start_attack
!walk:
    jsr guard                   // holding back while the opponent attacks nearby: block pose, no walking
    bcc !+
    lda f_state,x
    beq !g+
    lda #ST_IDLE
    jsr set_state
!g: lda #ANIM_BLOCK
    jmp guard_anim
!:  lda f_dir                   // 0 idle, 1 forward, 2 back = the state numbers
    cmp f_state,x
    beq !+
    jsr set_state
    jmp !st+
!:  lda f_state,x               // still idle after a guard: back to the idle animation
    bne !st+
    lda f_anim,x
    cmp #ANIM_BLOCK
    bne !st+
    lda #ST_IDLE
    jsr set_state
!st:
    lda f_state,x
    beq !anim+
    ldy f_id,x
    cmp #ST_FWD
    bne !+
    lda ft_walk_fwd,y
    bne !mv+
!:  lda ft_walk_back,y
!mv:
    // speeds are in half pixels per video frame (Stage 4b): f_sub keeps the odd half pixel
    sta tmp2
    clc
    adc f_sub,x
    lsr
    sta tmp
    lda #0
    rol
    sta f_sub,x
    // moving right if (forward and facing right) or (back and facing left)
    lda f_state,x
    cmp #ST_FWD
    beq !+
    lda f_facing,x
    eor #1
    jmp !dir+
!:  lda f_facing,x
!dir:
    jsr move_x                  // A = 0: right, 1: left; tmp = pixels
    jmp walk_step
!anim:
    jmp anim_step

// ---- crouching: crouching attacks; down-forward + button 2 = sweep
st_crouch:
    jsr face_other
    jsr special_check           // before leaving the crouch: QCF ends with down released in this frame
    bcc !+
    rts
!:  lda f_down,x
    bne !+
    lda #ST_IDLE
    jmp set_state
!:  lda f_press
    and #JOY_FIRE
    beq !+
    lda #MOVE_C_LP
    jmp start_attack
!:  lda f_press
    and #JOY_B2
    beq !+
    lda #MOVE_C_LK
    ldy f_dir
    cpy #1
    bne !atk+
    lda #MOVE_SWEEP
!atk:
    jmp start_attack
!:  jsr guard                   // crouching block pose while the opponent attacks nearby
    lda #ANIM_CROUCH
    bcc guard_anim
    lda #ANIM_C_BLOCK
    // fall through
// A = animation: switch to it if it is not running yet, else keep animating
guard_anim:
    cmp f_anim,x
    beq !+
    jmp start_anim
!:  jmp anim_step

// Proximity guard (Stage 4b, as in Street Fighter II): C = 1 when fighter X holds back while the other
// fighter attacks (on the ground or in the air) within GUARD_DIST pixels. Blocking itself is decided at
// the hit (hit_test); this only shows the pose and stops walking back.
.const GUARD_DIST = 100
guard:
    lda f_back,x
    beq !no+
    ldy other
    lda f_state,y
    cmp #ST_ATTACK
    beq !near+
    cmp #ST_JUMP
    bne !no+
    lda f_jatk,y
    beq !no+
!near:
    sec                         // tmp = x - other x (16 bit), then its absolute value
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
!:  lda tmp+1
    bne !no+
    lda tmp
    cmp #GUARD_DIST
    bcs !no+
    sec
    rts
!no:
    clc
    rts

// A = move: start the attack
start_attack:
    sta f_move,x
    lda #0
    sta f_hitdone,x
    lda #ST_ATTACK
    sta f_state,x
    jsr swing_sfx
    ldy f_move,x
    lda move_anim,y
    jmp start_anim

// Stage 5: the swing sound of move f_move,X (light / heavy)
swing_sfx:
    ldy f_move,x
    lda move_swing,y
    jmp sfx_play
move_swing: .byte SFX_SWING_LIGHT, SFX_SWING_HEAVY, SFX_SWING_LIGHT, SFX_SWING_HEAVY
            .byte SFX_SWING_LIGHT, SFX_SWING_LIGHT, SFX_SWING_HEAVY, SFX_SWING_LIGHT, SFX_SWING_HEAVY
            .byte SFX_SPECIAL
            .fill MOVE_SLOTS - 10, SFX_SWING_HEAVY

// ---------------------------------------------------------------- special moves (Stage 5)
// Each fighter has one special move (MOVE_SP1). Its motion and button are data (ft_sp_motion,
// ft_sp_button); the recogniser below runs every frame in every state, so a motion can be entered while
// an earlier attack or a hitstun is still running (input buffer).
//  QCF:    down (f_q1) -> down-forward within Q_WIN (f_q2) -> forward within Q_WIN (f_q3), button within Q3_WIN
//  charge: back (or down-back) held CHARGE_T frames, then forward + button within CHARGE_WIN frames
// Owner report 2026-11-19 (hardware, 8BitDo): no special came out. Made lenient: QCF may skip the diagonal,
// the charge window opens when back is released (a pad passes through neutral on its way forward), the
// button press is buffered for BTN_BUF frames, and a normal attack in its first animation frame is
// cancelled into the special (button pressed a moment before the motion was finished).
.const Q_WIN = 12
.const Q3_WIN = 14
.const CHARGE_T = 40
.const CHARGE_WIN = 14
.const BTN_BUF = 6
motion_track:
    ldy f_id,x                  // buffer the special's button
    lda f_press
    and ft_sp_button,y
    beq !+
    lda #BTN_BUF
    sta f_bbuf,x
    bne !b+
!:  lda f_bbuf,x
    beq !b+
    dec f_bbuf,x
!b:
    lda f_q1,x                  // count the windows down
    beq !+
    dec f_q1,x
!:  lda f_q2,x
    beq !+
    dec f_q2,x
!:  lda f_q3,x
    beq !+
    dec f_q3,x
!:  lda f_cwin,x
    beq !+
    dec f_cwin,x
!:  lda f_qb2,x                 // Stage 10: quarter circle back
    beq !+
    dec f_qb2,x
!:  lda f_qb3,x
    beq !+
    dec f_qb3,x
!:  lda f_dir
    ldy f_down,x
    beq !up+
    cmp #0                      // down
    bne !+
    lda #Q_WIN
    sta f_q1,x
    bne !chg+
!:  cmp #1                      // down-forward after down
    bne !db+
    lda f_q1,x
    beq !chg+
    lda #Q_WIN
    sta f_q2,x
    bne !chg+
!db:
    lda f_q1,x                  // down-back after down (Stage 10, QCB)
    beq !chg+
    lda #Q_WIN
    sta f_qb2,x
    bne !chg+
!up:
    cmp #2                      // back after down-back or right after down (QCB)
    bne !+
    lda f_qb2,x
    ora f_q1,x
    beq !chg+
    lda #Q3_WIN
    sta f_qb3,x
    bne !chg+
!:  cmp #1                      // forward after down-forward (or right after down: diagonal skipped)
    bne !chg+
    lda f_q2,x
    ora f_q1,x
    beq !chg+
    lda #Q3_WIN
    sta f_q3,x
!chg:
    lda f_dir
    cmp #2
    bne !rel+
    lda f_chg,x                 // holding back: count up to 255
    cmp #255
    beq !+
    inc f_chg,x
!:  rts
!rel:
    lda f_chg,x                 // back released after a full charge: the window opens
    cmp #CHARGE_T
    bcc !+
    lda #CHARGE_WIN
    sta f_cwin,x
!:  lda #0
    sta f_chg,x
    rts

// C = 1 when the special move of fighter X has started (motion done and its button pressed now)
special_check:
    ldy f_id,x
    lda f_bbuf,x                // button pressed within the last BTN_BUF frames
    beq !no+
    lda ft_sp_motion,y
    beq !qcf+
    cmp #2
    bne !chg+
    lda f_qb3,x                 // QCB (Stage 10)
    beq !no+
    bne !go+
!qcf:
    lda f_q3,x
    beq !no+
    bne !go+
!chg:
    lda f_dir                   // still holding forward
    cmp #1
    bne !no+
    lda f_cwin,x
    beq !no+
!go:
    lda #0
    sta f_bbuf,x
    sta f_qb2,x
    sta f_qb3,x
    sta f_q1,x
    sta f_q2,x
    sta f_q3,x
    sta f_cwin,x
    lda #MOVE_SP1
    jsr start_attack
    sec
    rts
!no:
    clc
    rts

// Key M (test aid, Stage 5): the border shows the special-move recogniser of both fighters:
// yellow = charged, cyan = QCF down-forward reached, white = motion complete (press the button now)
motion_debug:
    lda mot_debug
    bne !+
    rts
!:  ldy #0                      // black
    ldx #1
!f: lda f_chg,x
    cmp #CHARGE_T
    bcc !+
    ldy #7
!:  lda f_q2,x
    beq !+
    ldy #3
!:  lda f_q3,x
    ora f_cwin,x
    beq !+
    ldy #1
    bne !d+
!:  dex
    bpl !f-
!d: sty VIC_BORDER
    rts
mot_debug: .byte 0

// The special move dashes forward by ft_sp_dash pixels per frame until it has hit or been blocked
// (at most up to its last active frame); push_apart keeps the fighters from passing through.
special_dash:
    lda f_move,x
    cmp #MOVE_SP1
    bne !+
    lda f_hitdone,x
    bne !+
    lda f_aframe,x
    cmp #3
    bcs !+
    ldy f_id,x
    lda ft_sp_dash,y
    sta tmp
    lda f_facing,x              // 0 = right
    jmp move_x
!:  rts

// ---- attack: on active frames test the hit box once; at the end back to standing or crouching
st_attack:
    lda f_move,x                // a ground normal in its first frame can still become the special
    cmp #MOVE_J_P
    bcs !+
    lda f_aframe,x
    bne !+
    jsr special_check
    bcc !+
    rts
!:  jsr special_dash
    jsr attack_active
    jsr anim_step
    bcc !+
    lda f_move,x                // crouching moves return to the crouch while down is held
    cmp #MOVE_C_LP
    bcc !idle+
    cmp #MOVE_SWEEP+1
    bcs !idle+
    lda f_down,x
    beq !idle+
    lda #ST_CROUCH
    jmp set_state
!idle:
    lda #ST_IDLE
    jmp set_state
!:  rts

attack_active:
    ldy f_frame,x
    lda frame_hit,y
    beq !+
    lda f_hitdone,x
    bne !+
    jmp hit_test
!:  rts

// ---- jumping: arc from the table, sideways movement, one jump attack per jump
start_jump:
    ldy #0                      // sideways: 0 none, 1 right, 2 left
    lda f_dir
    beq !set+
    cmp #1
    beq !fwd+
    lda f_facing,x              // back: away from the facing direction
    eor #1
    jmp !d+
!fwd:
    lda f_facing,x
!d: tay
    iny
!set:
    tya
    sta f_jdx,x
    lda #0
    sta f_jt,x
    sta f_jatk,x
    lda #SFX_JUMP               // Stage 5
    jsr sfx_play
    lda #ST_JUMP
    jmp set_state

st_jump:
    inc f_jt,x
    ldy f_jt,x
    lda jump_h,y
    sta f_y,x
    lda f_jdx,x
    beq !+
    sec
    sbc #1                      // 1 -> 0 right, 2 -> 1 left
    pha
    lda #JUMP_DX
    sta tmp
    pla
    jsr move_x
!:  lda f_jatk,x                // a jump attack: button 1 = punch, button 2 = kick
    bne !act+
    lda f_press
    and #JOY_FIRE
    beq !+
    lda #MOVE_J_P
    bne !ja+
!:  lda f_press
    and #JOY_B2
    beq !anim+
    lda #MOVE_J_K
!ja:
    sta f_move,x
    lda #1
    sta f_jatk,x
    lda #0
    sta f_hitdone,x
    jsr swing_sfx
    ldy f_move,x
    lda move_anim,y
    jsr start_anim
!act:
    jsr attack_active
!anim:
    jsr anim_step
    lda f_jt,x
    cmp #JUMP_T
    bcc !+
    lda #0                      // landed
    sta f_y,x
    lda #SFX_LAND
    jsr sfx_play
    lda #ST_IDLE
    jmp set_state
!:  rts

// ---- hitstun: pushed back, then idle
st_hit:
    jsr pushback
    jsr anim_step
    dec f_stun,x
    bne !+
    lda #ST_IDLE
    jmp set_state
!:  rts

// ---- blockstun: pushed back, then standing or crouching again
st_block:
    jsr pushback
    jsr anim_step
    dec f_stun,x
    bne !+
    lda f_state,x
    cmp #ST_CBLOCK
    beq !c+
    lda #ST_IDLE
    jmp set_state
!c: lda #ST_CROUCH
    jmp set_state
!:  rts

// ---- knocked down / knocked out: fall (also from the air), lie, get up (not after a KO)
st_knock:
    lda f_y,x
    beq !+
    sec
    sbc #3
    bcs !y+
    lda #0
!y: sta f_y,x
!:  jsr pushback
    jsr anim_step
    lda f_thud,x                // Stage 5: thud once when he lands on his back (last fall frame)
    bne !t+
    jsr anim_index
    lda f_aframe,x
    clc
    adc #1
    cmp anim_len,y
    bne !t+
    lda f_y,x
    bne !t+
    inc f_thud,x
    lda #SFX_THUD
    jsr sfx_play
!t: lda f_state,x
    cmp #ST_KO
    beq !+
    dec f_stun,x
    bne !+
    lda #GETUP_TIME
    sta f_stun,x
    lda #ST_GETUP
    jmp set_state
!:  rts

st_getup:
    jsr anim_step
    dec f_stun,x
    bne !+
    lda #ST_IDLE
    jmp set_state
!:  rts

// slide back by 2 px per frame while f_push lasts; at the wall the attacker is pushed back instead
pushback:
    lda f_push,x
    beq !done+
    sec
    sbc #2
    bcs !+
    lda #0
!:  sta f_push,x
    lda #2
    sta tmp
    lda f_pushdir,x
    jsr move_x
    bcc !done+
    stx sh_save
    lda f_pushdir,x
    eor #1
    ldx other
    ldy f_y,x                   // not while the attacker is in the air
    bne !+
    jsr move_x
!:  ldx sh_save
!done:
    rts

// Move fighter X by tmp pixels: A = 0 right, 1 left. Carry set if stopped by the screen edge.
move_x:
    cmp #0
    bne !left+
    clc
    lda f_x_lo,x
    adc tmp
    sta f_x_lo,x
    lda f_x_hi,x
    adc #0
    sta f_x_hi,x
    beq !ok+
    lda f_x_lo,x
    cmp #<X_MAX
    bcc !ok+
    lda #<X_MAX
    sta f_x_lo,x
    lda #>X_MAX
    sta f_x_hi,x
    sec
    rts
!left:
    sec
    lda f_x_lo,x
    sbc tmp
    sta f_x_lo,x
    lda f_x_hi,x
    sbc #0
    sta f_x_hi,x
    bmi !min+
    bne !ok+
    lda f_x_lo,x
    cmp #X_MIN
    bcs !ok+
!min:
    lda #X_MIN
    sta f_x_lo,x
    lda #0
    sta f_x_hi,x
    sec
    rts
!ok:
    clc
    rts

// Is the other fighter crouching (smaller hurt box)? A = 1 yes, 0 no.
other_crouching:
    ldy other
    lda f_state,y
    cmp #ST_CROUCH
    beq !yes+
    cmp #ST_CBLOCK
    beq !yes+
    cmp #ST_ATTACK
    bne !no+
    lda f_move,y
    cmp #MOVE_C_LP
    bcc !no+
    cmp #MOVE_SWEEP+1
    bcs !no+
!yes:
    lda #1
    rts
!no:
    lda #0
    rts

// ---- does the attack of fighter X hit the other fighter?
hit_test:
    lda g_input                 // only during the fight
    bne !+
    rts
!:  ldy other                   // invulnerable while down, getting up or winning
    lda f_state,y
    cmp #ST_KO
    bne !+
    rts
!:  cmp #ST_KNOCK
    bcc !+
    rts
!:  ldy f_frame,x
    // hit box x range in screen coordinates (16 bit); facing left mirrors it: [x - x2, x - x1]
    lda f_facing,x
    bne !left+
    lda frame_hb_x1,y
    jsr add_x_signed
    sta hb_l
    lda tmp+1
    sta hb_l+1
    lda frame_hb_x2,y
    jsr add_x_signed
    sta hb_r
    lda tmp+1
    sta hb_r+1
    jmp !vert+
!left:
    lda frame_hb_x2,y
    neg
    jsr add_x_signed
    sta hb_l
    lda tmp+1
    sta hb_l+1
    lda frame_hb_x1,y
    neg
    jsr add_x_signed
    sta hb_r
    lda tmp+1
    sta hb_r+1
!vert:
    // vertical, as heights above the floor: hit box [lo + y, hi + y], hurt box [y, y + height]
    lda frame_hb_lo,y
    clc
    adc f_y,x
    sta hv_lo
    lda frame_hb_hi,y
    clc
    adc f_y,x
    sta hv_hi
    jsr other_crouching
    sta lh_low
    ldy other
    lda f_id,y
    tay
    lda ft_hurt_h,y
    ldz lh_low
    beq !+
    lda ft_crouch_h,y
!:  ldz #0
    ldy other
    clc
    adc f_y,y
    sta hu_hi                   // hurt top
    lda hv_lo                   // hit lo <= hurt top
    cmp hu_hi
    beq !+
    bcs !miss+
!:  lda hv_hi                   // hit hi >= hurt bottom (= other y)
    cmp f_y,y
    bcc !miss+
    // horizontal: hb_l <= other x + hurt_w and hb_r >= other x - hurt_w
    lda f_id,y
    tay
    lda ft_hurt_w,y
    sta tmp+1
    ldy other
    clc
    lda f_x_lo,y
    adc tmp+1
    sta hu_r
    lda f_x_hi,y
    adc #0
    sta hu_r+1
    sec
    lda f_x_lo,y
    sbc tmp+1
    sta hu_l
    lda f_x_hi,y
    sbc #0
    sta hu_l+1
    sec                         // hu_r - hb_l >= 0
    lda hu_r
    sbc hb_l
    lda hu_r+1
    sbc hb_l+1
    bmi !miss+
    sec                         // hb_r - hu_l >= 0
    lda hb_r
    sbc hu_l
    lda hb_r+1
    sbc hu_l+1
    bmi !miss+
    jmp land_hit
!miss:
    rts

// A = signed 8-bit offset; returns A = low byte of f_x + offset, tmp+1 = high byte, Y = f_frame (fighter X)
add_x_signed:
    sta ax_ofs
    ldy #0
    cmp #$80
    bcc !+
    dey
!:  sty ax_hi
    clc
    lda ax_ofs
    adc f_x_lo,x
    pha
    lda ax_hi
    adc f_x_hi,x
    sta tmp+1
    pla
    ldy f_frame,x
    rts

// fighter X hits the other fighter with f_move: blocked, hit, knocked down or knocked out
land_hit:
    lda #1
    sta f_hitdone,x
    lda f_id,x                  // y = fighter type * MOVE_SLOTS + move
    asl
    asl
    asl
    asl
    clc
    adc f_move,x
    tay
    lda mv_damage,y
    sta lh_damage
    lda mv_stun,y
    sta lh_stun
    lda mv_push,y
    sta lh_push
    lda mv_height,y
    sta lh_height
    lda mv_knock,y
    sta lh_knock
    lda f_facing,x              // the defender is pushed in the attacker's facing direction
    sta lh_dir
    stx sh_save
    ldx other
    lda lh_dir
    sta f_pushdir,x
    lda lh_push
    sta f_push,x
    // ---- blocked? on the ground, standing/walking/crouching/blocking, holding back, right height
    lda f_y,x
    bne !hit+
    lda f_back,x
    beq !hit+
    lda f_state,x
    cmp #ST_ATTACK
    bcc !ok+                    // idle, walking
    cmp #ST_CROUCH
    beq !ok+
    cmp #ST_BLOCK
    beq !ok+
    cmp #ST_CBLOCK
    bne !hit+
!ok:
    lda lh_height               // low: must crouch; overhead: must stand
    cmp #1
    bne !+
    lda f_down,x
    beq !hit+
    bne !blk+
!:  cmp #2
    bne !blk+
    lda f_down,x
    bne !hit+
!blk:
    lda lh_stun
    lsr
    clc
    adc #2
    sta f_stun,x
    lda #ST_BLOCK
    ldy f_down,x
    beq !+
    lda #ST_CBLOCK
!:  jsr set_state
    lda #SFX_BLOCK              // Stage 5
    jsr sfx_play
    lda #1                      // block spark
    jsr fx_spawn
    lda #BLOCKSTOP
    sta hitstop
    ldx sh_save
    rts
!hit:
    lda lh_stun
    sta f_stun,x
    lda f_health,x
    sec
    sbc lh_damage
    bcs !+
    lda #0
!:  sta f_health,x
    bne !alive+
    lda #0
    sta f_thud,x
    lda #ST_KO                  // knocked out
    jsr set_state
    lda #40
    sta f_push,x
    jsr game_ko                 // X = loser
    jmp !done+
!alive:
    lda lh_knock                // knockdown: sweeps, and every hit in the air
    ora f_y,x
    beq !+
    lda #DOWN_TIME
    sta f_stun,x
    lda #0
    sta f_thud,x
    lda #ST_KNOCK
    jsr set_state
    jmp !done+
!:  lda #ST_HIT
    jsr set_state
!done:
    lda #SFX_HIT_LIGHT          // Stage 5: heavy sound from 10 points of damage on
    ldy lh_damage
    cpy #10
    bcc !+
    lda #SFX_HIT_HEAVY
!:  jsr sfx_play
    lda #0                      // hit spark
    jsr fx_spawn
    ldx sh_save
    lda #HITSTOP
    sta hitstop
    rts

// ---- push boxes: keep the anchors PUSH_MIN apart, inside the screen (not while one is in the air)
push_apart:
    lda f_y
    ora f_y+1
    beq !+
    rts
!:  sec                         // d = x1 - x0 (16 bit signed)
    lda f_x_lo+1
    sbc f_x_lo
    sta tmp
    lda f_x_hi+1
    sbc f_x_hi
    sta tmp+1
    bpl !+
    lda #0                      // fighter 1 is left of fighter 0: |d|
    sec
    sbc tmp
    sta tmp
    lda #0
    sbc tmp+1
    sta tmp+1
    ldx #1                      // x = left fighter, y = right fighter
    ldy #0
    jmp !cmp+
!:  ldx #0
    ldy #1
!cmp:
    lda tmp+1
    beq !+
    rts                         // far apart
!:  lda tmp
    cmp #PUSH_MIN
    bcc !+
    rts
!:  clc                         // left = (left + right) / 2 - PUSH_MIN / 2
    lda f_x_lo,x
    adc f_x_lo,y
    sta hb_l
    lda f_x_hi,x
    adc f_x_hi,y
    lsr
    ror hb_l
    sta hb_l+1
    sec
    lda hb_l
    sbc #PUSH_MIN / 2
    sta hb_l
    lda hb_l+1
    sbc #0
    sta hb_l+1
    bmi !lmin+                  // clamp the left fighter to X_MIN
    bne !+
    lda hb_l
    cmp #X_MIN
    bcs !+
!lmin:
    lda #X_MIN
    sta hb_l
    lda #0
    sta hb_l+1
!:  clc                         // right = left + PUSH_MIN, clamped to X_MAX (then left = right - PUSH_MIN)
    lda hb_l
    adc #PUSH_MIN
    sta hb_r
    lda hb_l+1
    adc #0
    sta hb_r+1
    beq !set+
    lda hb_r
    cmp #<X_MAX
    bcc !set+
    lda #<X_MAX
    sta hb_r
    lda #>X_MAX
    sta hb_r+1
    sec
    lda hb_r
    sbc #PUSH_MIN
    sta hb_l
    lda hb_r+1
    sbc #0
    sta hb_l+1
!set:
    lda hb_l
    sta f_x_lo,x
    lda hb_l+1
    sta f_x_hi,x
    lda hb_r
    sta f_x_lo,y
    lda hb_r+1
    sta f_x_hi,y
    rts

// ---------------------------------------------------------------- drawing
// Draw both fighters; an attacking fighter 0 is drawn last (in front), otherwise fighter 1 is.
fighters_draw:
    ldx #0
    lda f_state
    cmp #ST_ATTACK
    beq !front+
    cmp #ST_JUMP
    bne !+
    lda f_jatk
    beq !+
!front:
    ldx #1
!:  stx draw_first
    jsr fighter_draw
    lda draw_first
    eor #1
    tax
    jmp fighter_draw

// Bring f_frame of fighter X into a slot that the shown buffer does not use, then draw it.
fighter_draw:
    txa
    asl
    sta fd_slot0                // fighter X uses the slots 2X and 2X+1
    lda front_slot,x
    clc
    adc fd_slot0
    tay
    lda f_frame,x
    cmp slot_frame,y
    beq !use+                   // the shown buffer already has this frame: share its slot
    tya
    eor #1
    tay
    lda f_frame,x
    cmp slot_frame,y
    beq !use+
    sta slot_frame,y
    stx sh_save
    tax
    lda frame_ofs_lo,x          // source in attic RAM
    sta job_frame+DMA_SRC
    lda frame_ofs_hi,x
    sta job_frame+DMA_SRC+1
    lda frame_ofs_bk,x
    sta job_frame+DMA_SRC+2
    lda frame_bytes_lo,x
    sta job_frame+DMA_COUNT
    lda frame_bytes_hi,x
    sta job_frame+DMA_COUNT+1
    lda slot_lo,y               // destination slot
    sta job_frame+DMA_DST
    lda slot_hi,y
    sta job_frame+DMA_DST+1
    lda slot_bk,y
    sta job_frame+DMA_DST+2
    RunDma(job_frame)
    ldx sh_save
!use:
    tya
    and #1
    sta build_slot,x
    lda slot_char_lo,y          // glyph 0 of column 0 = slot character + 1
    sta px_base
    lda slot_char_hi,y
    sta px_bhi
    ldy f_frame,x
    lda frame_w,y
    sta px_w
    lda frame_h,y
    sta px_h
    // x of the left edge: anchor + offset (signed), the mirrored offset when facing left
    lda f_facing,x
    sta px_flip
    beq !+
    lda frame_xofs_r,y
    jmp !add+
!:  lda frame_xofs,y
!add:
    jsr add_x_signed
    sta px_x
    lda tmp+1
    sta px_x+1
    // y of the top edge: floor - canvas anchor + trimmed rows - height in the air
    lda #<(FLOOR_Y - FRAME_TOP)
    clc
    adc frame_ytop,y
    sec
    sbc f_y,x
    sta px_y
    lda #0
    sta px_y+1
    lda #(FIGHTER_BANK << 4) | $0f
    cpx #0
    beq !+
    lda #((FIGHTER_BANK + 1) << 4) | $0f
!:  sta px_pal
    jmp pixie_draw
.errorif FLOOR_Y - FRAME_TOP + 112 > 255 || FLOOR_Y - FRAME_TOP < JUMP_H, "fighter y must stay within 0..255"

move_anim:    .byte ANIM_LP, ANIM_HP, ANIM_LK, ANIM_HK, ANIM_C_LP, ANIM_C_LK, ANIM_SWEEP, ANIM_J_P, ANIM_J_K, ANIM_SP1
slot_lo:      .byte <SLOT_A, <SLOT_B, <SLOT_C, <SLOT_D
slot_hi:      .byte >SLOT_A, >SLOT_B, >SLOT_C, >SLOT_D
slot_bk:      .byte (SLOT_A >> 16) & $0f, (SLOT_B >> 16) & $0f, (SLOT_C >> 16) & $0f, (SLOT_D >> 16) & $0f
slot_char_lo: .byte <(SLOT_A_CHAR + 1), <(SLOT_B_CHAR + 1), <(SLOT_C_CHAR + 1), <(SLOT_D_CHAR + 1)
slot_char_hi: .byte >(SLOT_A_CHAR + 1), >(SLOT_B_CHAR + 1), >(SLOT_C_CHAR + 1), >(SLOT_D_CHAR + 1)
slot_frame:   .fill 4, $ff          // frame currently held by each slot
job_frame:    DmaJob(DMA_CMD_COPY, ATTIC_F1, SLOT_A, 0)
// jump arc: height above the floor for every frame in the air (parabola)
jump_h:       .fill JUMP_T + 1, round(4 * JUMP_H * i * (JUMP_T - i) / (JUMP_T * JUMP_T))

// ---------------------------------------------------------------- state
f_id:       .fill 2, 0              // fighter type (index into the data tables)
f_x_lo:     .fill 2, 0
f_x_hi:     .fill 2, 0
f_y:        .fill 2, 0              // height above the floor
f_facing:   .fill 2, 0              // 0 = right, 1 = left
f_state:    .fill 2, 0
f_anim:     .fill 2, 0
f_aframe:   .fill 2, 0
f_tick:     .fill 2, 0
f_sub:      .fill 2, 0      // odd half pixel of the walk movement
f_thud:     .fill 2, 0      // Stage 5: the landing thud of this knockdown has sounded
f_frame:    .fill 2, 0
f_joy:      .fill 2, 0
f_joyprev:  .fill 2, 0
f_health:   .fill 2, 0
f_move:     .fill 2, 0
f_hitdone:  .fill 2, 0
f_stun:     .fill 2, 0              // hitstun / blockstun / time on the floor / getting up
f_push:     .fill 2, 0
f_pushdir:  .fill 2, 0
f_back:     .fill 2, 0              // holding back (block)
f_down:     .fill 2, 0              // holding down (crouch)
f_jt:       .fill 2, 0              // frames in the air
f_jdx:      .fill 2, 0              // jump sideways: 0 none, 1 right, 2 left
f_jatk:     .fill 2, 0              // jump attack used
f_q1:       .fill 2, 0              // Stage 5 QCF: frames left after down
f_q2:       .fill 2, 0              //              after down-forward
f_q3:       .fill 2, 0              //              after forward (the button may come now)
f_chg:      .fill 2, 0              // Stage 5 charge: frames back has been held
f_cwin:     .fill 2, 0              //                 frames left for forward + button after a charge
f_qb2:      .fill 2, 0              // Stage 10 QCB: frames left after down-back
f_qb3:      .fill 2, 0              //               after back (the button may come now)
f_bbuf:     .fill 2, 0              //                 frames left of the buffered special button
front_slot: .fill 2, 0              // slot (0/1) used by the shown buffer
build_slot: .fill 2, 0              // slot (0/1) used by the buffer being built
other:      .byte 0
f_press:    .byte 0
f_hold:     .byte 0
f_dir:      .byte 0
hitstop:    .byte 0
draw_first: .byte 0
fd_slot0:   .byte 0
sh_save:    .byte 0
ax_ofs:     .byte 0
ax_hi:      .byte 0
lh_damage:  .byte 0
lh_stun:    .byte 0
lh_push:    .byte 0
lh_dir:     .byte 0
lh_height:  .byte 0
lh_knock:   .byte 0
lh_low:     .byte 0
hv_lo:      .byte 0
hv_hi:      .byte 0
hb_l:       .word 0
hb_r:       .word 0
hu_l:       .word 0
hu_r:       .word 0
hu_hi:      .byte 0

// ----------------------------------------------------------------------------
// Fighters (Stage 2): two fighters, walking, four attacks, hits, hitstun,
// pushback, push boxes, KO and the next round.
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
.const ST_KO     = 5
.const X_MIN = 24
.const X_MAX = 296
.const PUSH_MIN = 36            // the fighters' anchors never come closer than this
.const HITSTOP = 6              // frames both fighters freeze when a hit lands
.const KO_TIME = 150            // frames until the next round starts after a KO

fighters_init:
    lda #0
    sta hitstop
    sta ko_timer
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
    // fall through: start of a round
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
    lda #ST_IDLE
    jsr set_state
    dex
    bpl !-
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
state_anim: .byte ANIM_IDLE, ANIM_WALK, ANIM_WALK, ANIM_IDLE, ANIM_HIT, ANIM_HIT

// Y = fighter type * 8 + animation (index into anim_first / anim_len)
anim_index:
    lda f_id,x
    asl
    asl
    asl
    clc
    adc f_anim,x
    tay
    rts

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

// Advance the animation by one video frame. Carry set when an attack animation has ended.
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
    beq !end+
    bcs !hold+                  // hit / KO: hold the last frame
    lda #0                      // idle / walking: loop
    sta f_aframe,x
!next:
    jsr anim_frame
!same:
    clc
    rts
!hold:
    dec f_aframe,x
    clc
    rts
!end:
    dec f_aframe,x
    sec
    rts

// ---------------------------------------------------------------- per frame
fighters_update:
    lda hitstop                 // a hit has just landed: both freeze
    beq !+
    dec hitstop
    rts
!:  lda ko_timer
    beq !+
    dec ko_timer
    bne !+
    jsr round_init              // next round
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
    lda #0
    sta f_dir
    lda ko_timer                // after a KO nobody takes input
    beq !+
    lda #0
    sta f_press
    jmp !states+
!:  // direction relative to the facing: 1 = forward, 2 = back, 0 = none
    lda f_joy,x
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
!states:
    lda f_state,x
    cmp #ST_ATTACK
    bne !+
    jmp st_attack
!:  bcc !+
    jmp st_hit                  // hit and KO
!:
    // ---- idle / walking: face the opponent, start attacks, walk
    ldy other
    lda f_x_hi,x                // facing = (my x >= other x)
    cmp f_x_hi,y
    bne !+
    lda f_x_lo,x
    cmp f_x_lo,y
!:  lda #0
    rol
    sta f_facing,x
    lda f_press
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
    sta f_move,x
    lda #0
    sta f_hitdone,x
    lda #ST_ATTACK
    sta f_state,x
    ldy f_move,x
    lda move_anim,y
    jmp start_anim
!walk:
    lda f_dir                   // 0 idle, 1 forward, 2 back = the state numbers
    cmp f_state,x
    beq !+
    jsr set_state
!:  lda f_state,x
    beq !anim+
    ldy f_id,x
    cmp #ST_FWD
    bne !+
    lda ft_walk_fwd,y
    bne !mv+
!:  lda ft_walk_back,y
!mv:
    sta tmp
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
!anim:
    jsr anim_step
    rts

// ---- attack: on active frames test the hit box once; back to idle at the end
st_attack:
    ldy f_frame,x
    lda frame_hit,y
    beq !+
    lda f_hitdone,x
    bne !+
    jsr hit_test
!:  jsr anim_step
    bcc !+
    lda #ST_IDLE
    jmp set_state
!:  rts

// ---- hitstun / KO: pushed back, then idle (a KO fighter stays down)
st_hit:
    lda f_push,x
    beq !anim+
    sec
    sbc #2
    bcs !+
    lda #0
!:  sta f_push,x
    lda #2
    sta tmp
    lda f_pushdir,x
    jsr move_x
    bcc !anim+                  // reached the wall: the attacker is pushed back instead
    stx sh_save
    lda f_pushdir,x
    eor #1
    ldx other
    jsr move_x
    ldx sh_save
!anim:
    jsr anim_step
    lda f_state,x
    cmp #ST_KO
    beq !+
    dec f_stun,x
    bne !+
    lda #ST_IDLE
    jmp set_state
!:  rts

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

// ---- does the attack of fighter X hit the other fighter?
hit_test:
    ldy f_frame,x
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
    eor #$ff
    clc
    adc #1
    jsr add_x_signed
    sta hb_l
    lda tmp+1
    sta hb_l+1
    lda frame_hb_x1,y
    eor #$ff
    clc
    adc #1
    jsr add_x_signed
    sta hb_r
    lda tmp+1
    sta hb_r+1
!vert:
    // vertical: the hit box must reach below the defender's hurt-box top (both stand on the floor)
    ldy other
    lda f_id,y
    tay
    lda ft_hurt_top,y
    sta tmp
    lda ft_hurt_w,y
    sta tmp+1
    ldy f_frame,x
    lda frame_hb_y2,y           // signed: y2 - hurt_top >= 0
    sec
    sbc tmp
    bvc !+
    eor #$80
!:  bmi !miss+
    // horizontal: hb_l <= other x + hurt_w and hb_r >= other x - hurt_w
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

// A = signed 8-bit offset; returns A = low byte of f_x + offset, tmp+1 = high byte (fighter X)
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
    ldy f_frame,x               // callers rely on Y = current frame
    rts

// fighter X hits the other fighter with f_move
land_hit:
    lda #1
    sta f_hitdone,x
    lda f_id,x                  // y = fighter type * 4 + move
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
    lda f_facing,x              // the defender is pushed in the attacker's facing direction
    sta lh_dir
    stx sh_save
    ldx other
    lda lh_dir
    sta f_pushdir,x
    lda lh_push
    sta f_push,x
    lda lh_stun
    sta f_stun,x
    lda f_health,x
    sec
    sbc lh_damage
    bcs !+
    lda #0
!:  sta f_health,x
    bne !alive+
    lda #ST_KO
    jsr set_state
    lda #KO_TIME
    sta ko_timer
    lda #40                     // a KO hits hard: the defender slides back further
    sta f_push,x
    jmp !done+
!alive:
    lda #ST_HIT
    jsr set_state
!done:
    ldx sh_save
    lda #HITSTOP
    sta hitstop
    rts

// ---- push boxes: keep the anchors PUSH_MIN apart, inside the screen
push_apart:
    sec                         // d = x1 - x0 (16 bit signed)
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
!:
    clc                         // left = (left + right) / 2 - PUSH_MIN / 2
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
    bne !+
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
    lda #<(FLOOR_Y - FRAME_TOP)
    sta px_y
    lda #>(FLOOR_Y - FRAME_TOP)
    sta px_y+1
    lda #(FIGHTER_BANK << 4) | $0f
    cpx #0
    beq !+
    lda #((FIGHTER_BANK + 1) << 4) | $0f
!:  sta px_pal
    jmp pixie_draw

move_anim:    .byte ANIM_LP, ANIM_HP, ANIM_LK, ANIM_HK
slot_lo:      .byte <SLOT_A, <SLOT_B, <SLOT_C, <SLOT_D
slot_hi:      .byte >SLOT_A, >SLOT_B, >SLOT_C, >SLOT_D
slot_bk:      .byte (SLOT_A >> 16) & $0f, (SLOT_B >> 16) & $0f, (SLOT_C >> 16) & $0f, (SLOT_D >> 16) & $0f
slot_char_lo: .byte <(SLOT_A_CHAR + 1), <(SLOT_B_CHAR + 1), <(SLOT_C_CHAR + 1), <(SLOT_D_CHAR + 1)
slot_char_hi: .byte >(SLOT_A_CHAR + 1), >(SLOT_B_CHAR + 1), >(SLOT_C_CHAR + 1), >(SLOT_D_CHAR + 1)
slot_frame:   .fill 4, $ff          // frame currently held by each slot
job_frame:    DmaJob(DMA_CMD_COPY, ATTIC_F1, SLOT_A, 0)

// ---------------------------------------------------------------- HUD: energy bars
// Row HUD_ROW: fighter 0's bar at x 20..147 (fills from the left), fighter 1's at x 172..299
// (mirrored: fills from the right). 8 glyphs of 16 px each; glyph k shows k pixels filled.
hud_draw:
    ldx #0
    jsr hud_bar
    ldx #1
hud_bar:
    stx fd_fighter
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
    ldx fd_fighter
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
    ldx fd_fighter
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
hud_x: .byte 20 + GOTOX_BIAS, 172 + GOTOX_BIAS
.errorif (HUD_CHAR & $ff) > $ff - 16, "HUD glyphs must not cross a 256-character boundary"

// ---------------------------------------------------------------- state
f_id:       .fill 2, 0              // fighter type (index into the data tables)
f_x_lo:     .fill 2, 0
f_x_hi:     .fill 2, 0
f_facing:   .fill 2, 0              // 0 = right, 1 = left
f_state:    .fill 2, 0
f_anim:     .fill 2, 0
f_aframe:   .fill 2, 0
f_tick:     .fill 2, 0
f_frame:    .fill 2, 0
f_joy:      .fill 2, 0
f_joyprev:  .fill 2, 0
f_health:   .fill 2, 0
f_move:     .fill 2, 0
f_hitdone:  .fill 2, 0
f_stun:     .fill 2, 0
f_push:     .fill 2, 0
f_pushdir:  .fill 2, 0
front_slot: .fill 2, 0              // slot (0/1) used by the shown buffer
build_slot: .fill 2, 0              // slot (0/1) used by the buffer being built
other:      .byte 0
f_press:    .byte 0
f_dir:      .byte 0
hitstop:    .byte 0
ko_timer:   .byte 0
draw_first: .byte 0
fd_fighter: .byte 0
fd_slot0:   .byte 0
sh_save:    .byte 0
ax_ofs:     .byte 0
ax_hi:      .byte 0
lh_damage:  .byte 0
lh_stun:    .byte 0
lh_push:    .byte 0
lh_dir:     .byte 0
hb_l:       .word 0
hb_r:       .word 0
hu_l:       .word 0
hu_r:       .word 0

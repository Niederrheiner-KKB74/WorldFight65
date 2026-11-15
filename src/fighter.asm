// ----------------------------------------------------------------------------
// Fighter (Stage 1: one fighter, idle and walking, turning round).
// The fighter reads the virtual joystick f_joy (docs/design.md §5); the frames
// come from attic RAM and are copied by DMA into one of two chip-RAM slots
// (double buffered with the screen, docs/design.md §3.1).
// ----------------------------------------------------------------------------

.const ST_IDLE = 0
.const ST_FWD  = 1
.const ST_BACK = 2
.const X_MIN = 24
.const X_MAX = 296
.const SPEED_FWD = 2
.const SPEED_BACK = 1
.const TICKS_IDLE = 8
.const TICKS_WALK = 4

fighter_init:
    lda #<96
    sta f_x
    lda #>96
    sta f_x+1
    lda #0
    sta f_facing
    sta f_state
    sta f_idx
    sta f_tick
    sta f_joyprev
    sta turn_req
    sta front_slot
    lda #$ff
    sta slot_frame
    sta slot_frame+1
    rts

// once per frame: f_joy = joystick bits (active high)
fighter_update:
    // turn round: fire button (edge) or key F
    lda f_joy
    and #JOY_FIRE
    tax
    eor f_joyprev
    and f_joy
    stx f_joyprev
    ora turn_req
    beq !+
    lda f_facing
    eor #1
    sta f_facing
    lda #0
    sta turn_req
!:
    // direction relative to the facing: forward / back / none
    lda f_joy
    and #JOY_LEFT | JOY_RIGHT
    ldy #ST_IDLE
    cmp #JOY_RIGHT
    bne !+
    ldy #ST_FWD
    lda f_facing
    beq !set+
    ldy #ST_BACK
    bne !set+
!:  cmp #JOY_LEFT
    bne !set+
    ldy #ST_BACK
    lda f_facing
    beq !set+
    ldy #ST_FWD
!set:
    cpy f_state
    beq !+
    sty f_state
    lda #0
    sta f_idx
    sta f_tick
!:
    // movement: forward = towards the facing direction
    lda f_state
    beq !anim+
    ldx #SPEED_FWD
    cmp #ST_FWD
    beq !+
    ldx #SPEED_BACK
!:  stx tmp
    // moving right if (forward and facing right) or (back and facing left)
    lda f_state
    cmp #ST_BACK
    beq !back+
    lda f_facing                 // forward
    bne !left+
    beq !right+
!back:
    lda f_facing
    bne !right+
!left:
    sec
    lda f_x
    sbc tmp
    sta f_x
    lda f_x+1
    sbc #0
    sta f_x+1
    bmi !min+
    bne !anim+
    lda f_x
    cmp #X_MIN
    bcs !anim+
!min:
    lda #X_MIN
    sta f_x
    lda #0
    sta f_x+1
    jmp !anim+
!right:
    clc
    lda f_x
    adc tmp
    sta f_x
    lda f_x+1
    adc #0
    sta f_x+1
    beq !anim+
    lda f_x
    cmp #<X_MAX
    bcc !anim+
    lda #<X_MAX
    sta f_x
    lda #>X_MAX
    sta f_x+1
!anim:
    // animation: idle 4 frames x 8 ticks, walking 6 frames x 4 ticks (backwards when walking back)
    inc f_tick
    lda f_state
    bne !walk+
    lda f_tick
    cmp #TICKS_IDLE
    bcc !frame+
    lda #0
    sta f_tick
    inc f_idx
    lda f_idx
    cmp #ANIM_IDLE_LEN
    bcc !frame+
    lda #0
    sta f_idx
    beq !frame+
!walk:
    lda f_tick
    cmp #TICKS_WALK
    bcc !frame+
    lda #0
    sta f_tick
    inc f_idx
    lda f_idx
    cmp #ANIM_WALK_LEN
    bcc !frame+
    lda #0
    sta f_idx
!frame:
    lda f_state
    bne !+
    lda #ANIM_IDLE
    clc
    adc f_idx
    sta f_frame
    rts
!:  cmp #ST_FWD
    bne !+
    lda #ANIM_WALK
    clc
    adc f_idx
    sta f_frame
    rts
!:  lda #ANIM_WALK + ANIM_WALK_LEN - 1
    sec
    sbc f_idx
    sta f_frame
    rts

// Bring f_frame into a slot that the shown buffer does not use, then draw it into the back buffer.
fighter_draw:
    ldx front_slot
    lda f_frame
    cmp slot_frame,x
    beq !use+                    // the shown buffer already has this frame: share its slot
    txa
    eor #1
    tax
    lda f_frame
    cmp slot_frame,x
    beq !use+
    sta slot_frame,x
    tay
    lda frame_ofs_lo,y           // source in attic RAM
    sta job_frame+DMA_SRC
    lda frame_ofs_hi,y
    sta job_frame+DMA_SRC+1
    lda frame_ofs_bk,y
    sta job_frame+DMA_SRC+2
    lda frame_bytes_lo,y
    sta job_frame+DMA_COUNT
    lda frame_bytes_hi,y
    sta job_frame+DMA_COUNT+1
    lda slot_lo,x                // destination slot
    sta job_frame+DMA_DST
    lda slot_hi,x
    sta job_frame+DMA_DST+1
    RunDma(job_frame)
!use:
    stx build_slot
    ldy f_frame
    lda frame_w,y
    sta px_w
    lda frame_h,y
    sta px_h
    lda slot_char_lo,x           // glyph 0 of column 0 = slot character + 1
    sta px_base
    lda slot_char_hi,x
    sta px_bhi
    // x of the left edge: anchor + offset (signed), the mirrored offset when facing left
    lda f_facing
    sta px_flip
    beq !+
    lda frame_xofs_r,y
    jmp !add+
!:  lda frame_xofs,y
!add:
    ldx #0
    cmp #$80
    bcc !+
    dex
!:  clc
    adc f_x
    sta px_x
    txa
    adc f_x+1
    sta px_x+1
    lda #<(FLOOR_Y - FRAME_TOP)
    sta px_y
    lda #>(FLOOR_Y - FRAME_TOP)
    sta px_y+1
    lda #(FIGHTER_BANK << 4) | $0f
    sta px_pal
    jmp pixie_draw

slot_lo:      .byte <SLOT_A, <SLOT_B
slot_hi:      .byte >SLOT_A, >SLOT_B
slot_char_lo: .byte <(SLOT_A_CHAR + 1), <(SLOT_B_CHAR + 1)
slot_char_hi: .byte >(SLOT_A_CHAR + 1), >(SLOT_B_CHAR + 1)
.errorif (SLOT_A >> 16) != (SLOT_B >> 16), "both frame slots must lie in the same bank"
slot_frame:   .byte $ff, $ff         // frame currently held by slot 0 / 1
job_frame:    DmaJob(DMA_CMD_COPY, ATTIC_F1, SLOT_A, 0)

f_x:       .word 0
f_facing:  .byte 0                   // 0 = right, 1 = left
f_state:   .byte 0
f_idx:     .byte 0
f_tick:    .byte 0
f_frame:   .byte 0
f_joy:     .byte 0
f_joyprev: .byte 0
turn_req:  .byte 0
front_slot: .byte 0
build_slot: .byte 0

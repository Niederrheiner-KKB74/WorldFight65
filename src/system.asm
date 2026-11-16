// ----------------------------------------------------------------------------
// Entry state save / exit to BASIC, keyboard via the hardware ASCII queue.
// Ported from ShooterMega65 Stage 19 (src/system.asm), which follows Vyper's
// hardware-confirmed exit (HOTREG off, saved VIC-IV registers, HOTREG last).
// WorldFight65 does not touch BASIC's screen RAM, the first 4 KB of colour RAM,
// the memory map or the stack, and changes only palette 0 (text palette).
// ----------------------------------------------------------------------------

.const KEYQUEUE = $d610          // MEGA65 hardware keyboard: ASCII of the oldest key, write = pop

.var vic_restore = List().add(
    $d010, $d015, $d017, $d01b, $d01c, $d01d, $d020, $d021,
    $d030, $d031, $d048, $d049, $d04a, $d04b, $d04c, $d04d, $d04e, $d04f,
    $d051, $d054, $d055, $d056, $d057, $d058, $d059, $d05a, $d05c, $d05e,
    $d060, $d061, $d062, $d063, $d064, $d065, $d06b, $d06c, $d06d, $d06e,
    $d070, $d07b).lock()

// called right after SEI, before anything is changed
system_save:
    tsx                          // SP as it will be after returning to the caller
    inx
    inx
    stx saved_sp
    tsy
    sty saved_sph
    tba
    sta saved_b
    lda #0
    tab                          // our zero page is $00xx
    RunDma(job_zp_save)          // zero page $02-$ff to chip RAM (SAVED_ZP)
    lda CIA1_DDRA
    sta saved_ddra
    lda CIA1_DDRB
    sta saved_ddrb
    .for (var i = 0; i < vic_restore.size(); i++) {
        lda vic_restore.get(i)
        sta saved_vic + i
    }
    lda VIC_D05D
    sta saved_d05d
    lda VIC_PALSEL               // palette 0 (all 256 entries) to SAVED_PAL0
    and #%00111111
    sta VIC_PALSEL
    jsr pal0_ptr
!:  tza
    tax
    lda PAL_RED,x
    sta ((scr_ptr)),z
    inc scr_ptr+1
    lda PAL_GREEN,x
    sta ((scr_ptr)),z
    inc scr_ptr+1
    lda PAL_BLUE,x
    sta ((scr_ptr)),z
    dec scr_ptr+1
    dec scr_ptr+1
    inz
    bne !-
    lda saved_vic + vic_restore.size() - 2   // $d070
    sta VIC_PALSEL
    jmp key_drain

exit_to_basic:
    sei
    jsr wait_vblank              // switch modes while the raster is in the border
    lda #$00                     // MAPEDPAL = 0
    sta VIC_PALSEL
    jsr pal0_ptr
!:  tza
    tax
    lda ((scr_ptr)),z
    sta PAL_RED,x
    inc scr_ptr+1
    lda ((scr_ptr)),z
    sta PAL_GREEN,x
    inc scr_ptr+1
    lda ((scr_ptr)),z
    sta PAL_BLUE,x
    dec scr_ptr+1
    dec scr_ptr+1
    inz
    bne !-
    jsr vic_to_basic
    jsr key_drain                // do not hand the exit key to BASIC
    RunDma(job_zp_rest)
    lda saved_b
    tab
    ldx saved_sp
    ldy saved_sph
    tys
    txs
    ldz #0                       // C65 ROM code expects Z = 0
    lda #0
    tax
    tay
    cli
    rts                          // back to the SYS caller -> READY.

// VIC-IV registers as BASIC had them: HOTREG off first, saved values, HOTREG last; CIA port A direction
vic_to_basic:
    lda VIC_D05D
    and #$7f
    sta VIC_D05D
    sta VIC_D05D
    .for (var i = 0; i < vic_restore.size(); i++) {
        lda saved_vic + i
        sta vic_restore.get(i)
    }
    lda saved_d05d
    sta VIC_D05D
    lda saved_ddra
    sta CIA1_DDRA
    lda saved_ddrb
    sta CIA1_DDRB
    rts

// Read one key from the hardware queue and handle it: X or RUN/STOP = exit, P = POT X debug display.
read_keys:
    lda KEYQUEUE
    beq !none+
    sta KEYQUEUE                 // pop
    cmp #$03                     // RUN/STOP
    beq !exit+
    and #$df                     // fold lower case
    cmp #$58                     // X
    beq !exit+
    cmp #$54                     // T: sparring partner (sparring.asm)
    bne !+
    jmp spar_toggle
!:  cmp #$50                     // P: POT X debug display in the border on/off
    bne !+
    lda pot_debug
    eor #1
    sta pot_debug
    bne !+
    lda #0
    sta VIC_BORDER
!:
!none:
    rts
!exit:
    jmp exit_to_basic

key_drain:
!:  lda KEYQUEUE
    beq !+
    sta KEYQUEUE
    bne !-
!:  rts

// palette 0 (768 bytes) at SAVED_PAL0 in chip RAM: scr_ptr -> it, Z = 0
pal0_ptr:
    lda #<SAVED_PAL0
    sta scr_ptr
    lda #>SAVED_PAL0
    sta scr_ptr+1
    lda #[SAVED_PAL0 >> 16] & $ff
    sta scr_ptr+2
    lda #0
    sta scr_ptr+3
    taz
    rts

saved_sp:   .byte 0
saved_sph:  .byte 0
saved_b:    .byte 0
saved_ddra: .byte 0
saved_ddrb: .byte 0
saved_d05d: .byte 0
saved_vic:  .fill vic_restore.size(), 0
job_zp_save: DmaJob(DMA_CMD_COPY, $0002, SAVED_ZP + 2, 254)
job_zp_rest: DmaJob(DMA_CMD_COPY, SAVED_ZP + 2, $0002, 254)

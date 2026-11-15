// ----------------------------------------------------------------------------
// Video mode, palette, screen buffers and page flipping.
// video_init follows ShooterMega65 Stage 19 (src/video.asm, hardware-confirmed
// H320/RRB settings); without scrolling, row 0 starts at the top border.
// ----------------------------------------------------------------------------

video_init:
    lda #0
    sta VIC_SPREN
    lda VIC_D05D                // HOTREG off and cancel any pending recalculation
    and #$7f
    sta VIC_D05D
    sta VIC_D05D

    lda #$40                    // FAST, H320, V200, no ATTR, no bitplanes
    sta VIC_D031
    lda VIC_D030                // RAM palette, CRAM2K off (keeps CIA1 visible)
    and #%11111110
    ora #%00000100
    sta VIC_D030
    lda VIC_D054                // keep the user's PALEMU setting (bit 5)
    and #%00100000
    ora #$45                    // CHR16 + FCLRHI (chars > $FF are full colour) + VFAST
    sta VIC_D054

    lda #104                    // top border
    sta VIC_TBDRPOS
    lda #0
    sta VIC_TBDRPOS+1
    lda #<504                   // bottom border
    sta VIC_BBDRPOS
    lda #>504
    sta VIC_BBDRPOS+1
    lda #80-32                  // text 16 logical px left of the border edge:
    sta VIC_TEXTXPOS            // logical x 0..15 of every row is hidden under the border
    lda #0
    sta VIC_TEXTXPOS+1
    lda #104                    // row 0 starts at the top border
    sta VIC_TEXTYPOS
    lda #0
    sta VIC_TEXTYPOS+1
    lda #80                     // side border width (default H320)
    sta VIC_SDBDRWD
    lda #0                      // HOTREG off, border width high bits 0
    sta VIC_D05D
    lda #120                    // CHRXSCL: H320 with logical GOTOX coordinates (Vyper rule 19a)
    sta VIC_CHRXSCL

    lda #<ROW_BYTES
    sta VIC_LINESTEP
    lda #>ROW_BYTES
    sta VIC_LINESTEP+1
    lda #<ROW_TOKENS
    sta VIC_CHRCOUNT
    lda VIC_D063                // keep bits 6-7 (as Vyper does)
    and #%11000000
    ora #((>ROW_TOKENS) << 4)   // CHRCOUNT bits 8-9, screen pointer bits 24-27 = 0
    sta VIC_D063
    lda #VIS_ROWS               // rows 0..25 are fetched; row 25 is the null row
    sta VIC_DISPROWS
    lda #0
    sta VIC_D051                // NORRDEL = 0: RRB double buffering
    sta VIC_BORDER
    sta VIC_BGCOL
    lda #0                      // edit, text and sprites: palette 0
    sta VIC_PALSEL
    RunDma(job_clean_a)         // both buffers start as the clean arena screen
    RunDma(job_cclean_a)
    RunDma(job_clean_b)
    RunDma(job_cclean_b)
    lda #0
    sta back                    // B is shown first, A is built first
    jmp show_buffer_b

// Arena palette (entries 0..ARENA_COLOURS-1) from the map file; fighter and HUD palettes into their banks.
palette_init:
    RunDma(job_pal)
    ldx #0
!:  lda pal_buf,x
    sta PAL_RED,x
    lda pal_buf+ARENA_COLOURS,x
    sta PAL_GREEN,x
    lda pal_buf+ARENA_COLOURS*2,x
    sta PAL_BLUE,x
    inx
    cpx #ARENA_COLOURS
    bne !-
    ldx #15
!:  lda pal_f1_r,x                      // fighter 1 -> bank 12, fighter 2 -> bank 13, HUD -> bank 15
    sta PAL_RED+FIGHTER_BANK*16,x
    lda pal_f1_g,x
    sta PAL_GREEN+FIGHTER_BANK*16,x
    lda pal_f1_b,x
    sta PAL_BLUE+FIGHTER_BANK*16,x
    lda pal_f2_r,x
    sta PAL_RED+(FIGHTER_BANK+1)*16,x
    lda pal_f2_g,x
    sta PAL_GREEN+(FIGHTER_BANK+1)*16,x
    lda pal_f2_b,x
    sta PAL_BLUE+(FIGHTER_BANK+1)*16,x
    lda pal_hud_r,x
    sta PAL_RED+HUD_BANK*16,x
    lda pal_hud_g,x
    sta PAL_GREEN+HUD_BANK*16,x
    lda pal_hud_b,x
    sta PAL_BLUE+HUD_BANK*16,x
    dex
    bpl !-
    rts

// Start a new back buffer: clean arena rows (background + empty overlay), all rows empty.
buffer_clear:
    lda back
    bne !b+
    RunDma(job_clean_a)
    RunDma(job_cclean_a)
    lda #<SCREEN_A
    sta backscr
    lda #>SCREEN_A
    sta backscr+1
    lda #<COLOUR_A
    sta backcol
    lda #>COLOUR_A
    sta backcol+1
    jmp !rows+
!b: RunDma(job_clean_b)
    RunDma(job_cclean_b)
    lda #<SCREEN_B
    sta backscr
    lda #>SCREEN_B
    sta backscr+1
    lda #<COLOUR_B
    sta backcol
    lda #>COLOUR_B
    sta backcol+1
!rows:
    ldx #VIS_ROWS-1
    lda #OVL_START
!:  sta rowfill,x
    dex
    bpl !-
    rts

// Show the buffer that was just built (back), then make the other one the back buffer.
flip:
    lda back
    bne !b+
    jsr show_buffer_a
    lda #1
    sta back
    rts
!b: jsr show_buffer_b
    lda #0
    sta back
    rts

show_buffer_a:
    lda #<SCREEN_A
    sta VIC_SCRNPTR
    lda #>SCREEN_A
    sta VIC_SCRNPTR+1
    lda #(SCREEN_A >> 16)
    sta VIC_SCRNPTR+2
    lda #<COLOUR_A
    sta VIC_COLPTR
    lda #>COLOUR_A
    sta VIC_COLPTR+1
    lda #0
    sta VIC_D051
    rts

show_buffer_b:
    lda #<SCREEN_B
    sta VIC_SCRNPTR
    lda #>SCREEN_B
    sta VIC_SCRNPTR+1
    lda #(SCREEN_B >> 16)
    sta VIC_SCRNPTR+2
    lda #<COLOUR_B
    sta VIC_COLPTR
    lda #>COLOUR_B
    sta VIC_COLPTR+1
    lda #0
    sta VIC_D051
    rts

job_clean_a:  DmaJob(DMA_CMD_COPY, CLEAN_SCR, SCREEN_A, BUF_BYTES)
job_clean_b:  DmaJob(DMA_CMD_COPY, CLEAN_SCR, SCREEN_B, BUF_BYTES)
job_cclean_a: DmaJob(DMA_CMD_COPY, CLEAN_COL, COLRAM + COLOUR_A, BUF_BYTES)
job_cclean_b: DmaJob(DMA_CMD_COPY, CLEAN_COL, COLRAM + COLOUR_B, BUF_BYTES)
job_pal:      DmaJob(DMA_CMD_COPY, ARENA_MAP, pal_buf, MAP_PAL_BYTES)
job_blank:    DmaJob(DMA_CMD_FILL, 0, BLANK_NCM, 64)

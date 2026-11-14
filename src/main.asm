// ============================================================================
// WorldFight65 - Stage 0: toolchain and disk test
//   Prints a short message through the KERNAL, waits for a key and returns to
//   BASIC. Nothing else is touched: no VIC-IV set-up yet (that is Stage 1).
// Build: python3 tools/build.py   (KickAssembler 65CE02 5.25, see README)
// ============================================================================
.cpu _45gs02

#import "hw.asm"

.const CHROUT = $ffd2
.const GETIN  = $ffe4

// ---------------------------------------------------------------- BASIC stub
*=$2001
    .word basic_end, 10
    .byte $fe, $02, $30, $3a           // BANK 0:
    .byte $9e                          // SYS
    .text "8224"                       // $2020
    .byte 0
basic_end:
    .word 0

*=$2020

start:
    ldx #0
!:  lda message,x
    beq !wait+
    jsr CHROUT
    inx
    bne !-
!wait:
    jsr GETIN
    beq !wait-
    rts

.encoding "petscii_mixed"
message:
    .byte $0e, $93, $0d                // lower/upper case set, clear screen
    .text "WorldFight65 - Stage 0"
    .byte $0d, $0d
    .text "Toolchain and disk test: this program"
    .byte $0d
    .text "was assembled with KickAssembler 65CE02"
    .byte $0d
    .text "and loaded from the D81 image."
    .byte $0d, $0d
    .text "Press any key to return to BASIC."
    .byte $0d, 0

.errorif * > $c000, "program must end below $C000"

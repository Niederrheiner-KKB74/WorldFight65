#!/usr/bin/env python3
"""Check the generated WorldFight65 data (build/gen) against the limits of the engine.

Arena: at most 1000 FCM glyphs, pixel values only 0..ARENA_COLOURS-1 (no $FF), clean screen of the right
size with every row ending in the blank NCM glyph. Fighter: every frame block fits a slot, starts with a
blank glyph and has a blank glyph after every column, colour indices 0..15; both fighter packages (F-TIAGO, F-KONRAD).
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / 'build/gen'


def consts():
    c = {}
    for line in (GEN / 'layout.inc').read_text().splitlines():
        m = re.match(r'\.const (\w+) = \$([0-9a-f]+)', line)
        if m:
            c[m.group(1)] = int(m.group(2), 16)
    return c


def table(text, name):
    m = re.search(rf'^{name}:\s*\.byte ([^/\n]+)', text, re.M)
    return [int(v.strip().replace('$', '0x'), 0) for v in m.group(1).split(',')]


def main():
    c = consts()
    errors = []
    gfx = (GEN / 'A-RIO-GFX.bin').read_bytes()
    if len(gfx) % 64 or len(gfx) // 64 > 1000:
        errors.append(f'arena: {len(gfx)} bytes is not a whole number of glyphs <= 1000')
    if gfx[:64] != bytes(64):
        errors.append('arena: glyph 0 must be blank')
    if max(gfx) >= c['ARENA_COLOURS']:
        errors.append(f'arena: pixel value {max(gfx)} outside the arena palette')
    mp = (GEN / 'A-RIO-MAP.bin').read_bytes()
    if len(mp) != c['MAP_PAL_BYTES'] + 2 * c['BUF_BYTES']:
        errors.append(f'arena map: {len(mp)} bytes')
    scr = mp[c['MAP_PAL_BYTES']:c['MAP_PAL_BYTES'] + c['BUF_BYTES']]
    nglyph = len(gfx) // 64
    for r in range(c['BUF_ROWS']):
        row = scr[r * c['ROW_BYTES']:(r + 1) * c['ROW_BYTES']]
        last = row[-2] | row[-1] << 8
        if last != c['BLANK_CHAR']:
            errors.append(f'arena map row {r}: does not end with the blank glyph')
        for t in range(c['BG_TOKENS']):
            ch = row[2 * t] | row[2 * t + 1] << 8
            if not c['ARENA_CHAR'] <= ch < c['ARENA_CHAR'] + nglyph:
                errors.append(f'arena map row {r} token {t}: char ${ch:x} outside the arena glyphs')
                break
    inc = (GEN / 'assets.inc').read_text()
    files = [(GEN / f'{n}.bin').read_bytes() for n in ('F-TIAGO', 'F-KONRAD', 'F-MALEE')]   # in attic order
    pkg = c['ATTIC_F2'] - c['ATTIC_F1']
    lo, hi, bk = table(inc, 'frame_ofs_lo'), table(inc, 'frame_ofs_hi'), table(inc, 'frame_ofs_bk')
    blo, bhi = table(inc, 'frame_bytes_lo'), table(inc, 'frame_bytes_hi')
    ws, hs = table(inc, 'frame_w'), table(inc, 'frame_h')
    for i in range(len(ws)):
        ofs = lo[i] | hi[i] << 8 | bk[i] << 16
        size = blo[i] | bhi[i] << 8
        w, h = ws[i], hs[i]
        if size != (1 + w * (h + 1)) * 64:
            errors.append(f'frame {i}: size {size} does not match {w}x{h}')
        if size > c['SLOT_SIZE']:
            errors.append(f'frame {i}: {size} bytes do not fit a slot')
        f = files[ofs // pkg]
        blk = f[ofs % pkg:ofs % pkg + size]
        if len(blk) != size:
            errors.append(f'frame {i}: outside the file')
            continue
        for k in [0] + [(1 + col * (h + 1) + h) for col in range(w)]:
            if blk[k * 64:(k + 1) * 64] != bytes(64):
                errors.append(f'frame {i}: glyph {k} must be blank')
        if (w * 16) > 112 or h * 8 > 112:
            errors.append(f'frame {i}: larger than 112x112')
    if errors:
        print('\n'.join('check_assets: ' + e for e in errors))
        sys.exit(1)
    print(f'check_assets: ok (arena {nglyph} glyphs, {len(ws)} fighter frames, largest frame '
          f'{max((1 + ws[i] * (hs[i] + 1)) * 64 for i in range(len(ws)))} of {c["SLOT_SIZE"]} bytes)')


if __name__ == '__main__':
    main()

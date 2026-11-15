#!/usr/bin/env python3
"""Convert Claude's artwork (assets/source/*.py) into MEGA65 data for WorldFight65.

Output in build/gen/:
  layout.inc      screen layout and memory constants shared by Python and the assembler
  assets_const.inc / assets.inc   fighter constants / frame tables and palette (bank 12) for the assembler
  A-RIO-GFX.bin   arena: full-colour (FCM) glyphs, 64 bytes each, glyph 0 blank -> loaded to ARENA_GFX
  A-RIO-MAP.bin   arena: palette entries 0..175 (R, G, B planes, nibble-swapped), then the complete
                  clean RRB screen (screen bytes, then colour bytes) -> loaded to ARENA_MAP
  F-TIAGO.bin     Tiago's frames: NCM glyph blocks (blank, then per column h glyphs + blank)
                  -> loaded to attic RAM ATTIC_F1
and preview images in build/preview/.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'assets/source'))
import fighter_art as fa      # noqa: E402

# ------------------------------------------------------------------ layout (single source of truth)
L = dict(
    BG_TOKENS=42,             # 42 FCM chars = 336 px; logical x 0..15 hidden under the left border
    ROW_TOKENS=80,
    VIS_ROWS=25,
    BUF_ROWS=26,              # + null row under the bottom border
    GOTOX_BIAS=16,
    ARENA_GFX=0x040000,       # FCM glyphs, char $1000+, max. 1000 glyphs
    SLOT_A=0x050000,          # fighter 1 frame slots (6 KB each)
    SLOT_B=0x051800,
    SLOT_SIZE=0x1800,
    BLANK_NCM=0x053000,       # one blank NCM glyph (ends every row)
    SCREEN_A=0x054000,
    SCREEN_B=0x055200,
    ARENA_MAP=0x058800,       # palette + clean screen + clean colour
    SAVED_SCR=0x05D000,
    SAVED_PAL0=0x05DB00,
    SAVED_ZP=0x05DE00,
    COLRAM=0xFF80000,
    COLOUR_A=0x1000,
    COLOUR_B=0x2400,
    ATTIC_F1=0x8000000,       # Tiago's frames
    ARENA_COLOURS=176,        # palette entries 0..175 belong to the arena
    FIGHTER_BANK=12,
)
L['ROW_BYTES'] = L['ROW_TOKENS'] * 2
L['OVL_START'] = L['BG_TOKENS'] * 2
L['OVL_END'] = (L['ROW_TOKENS'] - 1) * 2
L['ARENA_CHAR'] = L['ARENA_GFX'] // 64
L['BLANK_CHAR'] = L['BLANK_NCM'] // 64
L['SLOT_A_CHAR'] = L['SLOT_A'] // 64
L['SLOT_B_CHAR'] = L['SLOT_B'] // 64
L['MAP_PAL_BYTES'] = L['ARENA_COLOURS'] * 3
L['CLEAN_SCR'] = L['ARENA_MAP'] + L['MAP_PAL_BYTES']
L['CLEAN_COL'] = L['CLEAN_SCR'] + L['BUF_ROWS'] * L['ROW_BYTES']
L['BUF_BYTES'] = L['BUF_ROWS'] * L['ROW_BYTES']
MAX_ARENA_GLYPHS = 1000
FLOOR_Y = 190                 # screen y of the fighters' anchor (the floor)


def swap(v):
    """MEGA65 palette registers hold the colour value with swapped nibbles."""
    return ((v & 0x0F) << 4) | (v >> 4)


def fcm_glyph(a):
    assert a.shape == (8, 8)
    return bytes(int(v) for v in a.flatten())


def ncm_glyph(a):
    """16x8 colour indices -> 64 bytes NCM, left pixel in the low nibble (ShooterMega65 make_assets)."""
    assert a.shape == (8, 16)
    out = bytearray()
    for y in range(8):
        for x in range(0, 16, 2):
            out.append((int(a[y, x]) & 15) | ((int(a[y, x + 1]) & 15) << 4))
    return bytes(out)


# ------------------------------------------------------------------ arena
def arena(gen, prev):
    import arena_rio
    img = arena_rio.draw()
    n = L['ARENA_COLOURS'] - 1          # entries 1..175; 0 stays black/transparent
    q = img.quantize(colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    idx = np.array(q, np.uint8).astype(np.int32) + 1
    qpal = q.getpalette()[:n * 3]
    pal = [(0, 0, 0)] + [tuple(qpal[i * 3:i * 3 + 3]) for i in range(n)]
    pal += [(0, 0, 0)] * (L['ARENA_COLOURS'] - len(pal))
    assert idx.max() < L['ARENA_COLOURS'] and idx.min() >= 1
    glyphs = {bytes(64): 0}
    order = [bytes(64)]
    rows = []
    for r in range(L['VIS_ROWS']):
        row = []
        for c in range(40):
            g = fcm_glyph(idx[r * 8:r * 8 + 8, c * 8:c * 8 + 8])
            if g not in glyphs:
                glyphs[g] = len(order)
                order.append(g)
            row.append(glyphs[g])
        rows.append(row)
    if len(order) > MAX_ARENA_GLYPHS:
        sys.exit(f'arena: {len(order)} glyphs, max. {MAX_ARENA_GLYPHS}')
    (gen / 'A-RIO-GFX.bin').write_bytes(b''.join(order))
    # clean RRB screen: 2 hidden + 40 picture chars, null GOTOX tokens to x 320, blank NCM glyph at the end
    scr, col = bytearray(), bytearray()
    for r in range(L['BUF_ROWS']):
        chars = [0, 0] + (rows[r] if r < L['VIS_ROWS'] else [0] * 40)
        for ch in chars:
            v = L['ARENA_CHAR'] + ch
            scr += bytes((v & 0xff, v >> 8))
            col += bytes((0x00, 0x00))
        for _ in range(L['BG_TOKENS'], L['ROW_TOKENS'] - 1):
            scr += bytes((0x40, 0x01))              # GOTOX 320
            col += bytes((0x90, 0x00))
        scr += bytes((L['BLANK_CHAR'] & 0xff, L['BLANK_CHAR'] >> 8))
        col += bytes((0x08, 0x0f))
    assert len(scr) == L['BUF_BYTES']
    palb = bytes(swap(c[ch]) for ch in range(3) for c in pal)
    (gen / 'A-RIO-MAP.bin').write_bytes(palb + scr + col)
    # preview of what the MEGA65 will show
    rgb = np.array(pal, np.uint8)[idx]
    Image.fromarray(rgb).resize((960, 600), Image.NEAREST).save(prev / 'arena_rio.png')
    return len(order), pal


# ------------------------------------------------------------------ fighter
def fighter(gen, prev, arena_pal):
    import fighter_tiago as ft
    anims = ft.frames()
    names = list(anims)
    frames = [f for n in names for f in anims[n]]
    h = fa.FRAME_H // 8
    blob = bytearray()
    tab = []
    for f in frames:
        cols = np.nonzero(f.any(axis=0))[0]
        x0, x1 = int(cols[0]), int(cols[-1])
        w = (x1 - x0 + 16) // 16
        pad = np.zeros((fa.FRAME_H, w * 16), np.uint8)
        part = f[:, x0:x0 + w * 16]
        pad[:, :part.shape[1]] = part
        glyphs = [bytes(64)]
        for c in range(w):
            for r in range(h):
                glyphs.append(ncm_glyph(pad[r * 8:r * 8 + 8, c * 16:c * 16 + 16]))
            glyphs.append(bytes(64))
        data = b''.join(glyphs)
        if len(data) > L['SLOT_SIZE']:
            sys.exit(f'fighter frame too large: {len(data)} bytes')
        tab.append(dict(ofs=len(blob), glyphs=len(glyphs), w=w, h=h, xofs=x0 - fa.ANCHOR[0]))
        blob += data
    if len(blob) > 0x10000:
        sys.exit('F-TIAGO larger than 64 KB (loader limit)')
    (gen / 'F-TIAGO.bin').write_bytes(bytes(blob))
    fa.sheet(frames, ft.PALETTE, scale=3).save(prev / 'tiago.png')
    # assembler tables
    a = ['// generated by tools/make_assets.py - do not edit', '']
    first = 0
    for n in names:
        a.append(f'.const ANIM_{n.upper()} = {first}')
        a.append(f'.const ANIM_{n.upper()}_LEN = {len(anims[n])}')
        first += len(anims[n])
    a.append(f'.const FRAME_COUNT = {len(frames)}')
    a.append(f'.const FRAME_TOP = {fa.ANCHOR[1]}          // anchor y inside the frame canvas')
    a.append(f'.const FLOOR_Y = {FLOOR_Y}')
    a.append('frame_ofs_lo:  .byte ' + ', '.join(f'${t["ofs"] & 0xff:02x}' for t in tab))
    a.append('frame_ofs_hi:  .byte ' + ', '.join(f'${(t["ofs"] >> 8) & 0xff:02x}' for t in tab))
    a.append('frame_ofs_bk:  .byte ' + ', '.join(f'${(t["ofs"] >> 16) & 0x0f:02x}' for t in tab))
    a.append('frame_bytes_lo: .byte ' + ', '.join(f'${(t["glyphs"] * 64) & 0xff:02x}' for t in tab))
    a.append('frame_bytes_hi: .byte ' + ', '.join(f'${(t["glyphs"] * 64) >> 8:02x}' for t in tab))
    a.append('frame_w:       .byte ' + ', '.join(str(t['w']) for t in tab))
    a.append('frame_h:       .byte ' + ', '.join(str(t['h']) for t in tab))
    a.append('frame_xofs:    .byte ' + ', '.join(f'${t["xofs"] & 0xff:02x}' for t in tab) + '   // signed')
    a.append('frame_xofs_r:  .byte ' + ', '.join(f'${(-t["xofs"] - t["w"] * 16) & 0xff:02x}' for t in tab)
             + '   // signed, facing left')
    pal = ft.PALETTE
    a.append('fighter_pal:   .byte ' + ', '.join(f'${swap(c[0]):02x}' for c in pal))
    a.append('               .byte ' + ', '.join(f'${swap(c[1]):02x}' for c in pal))
    a.append('               .byte ' + ', '.join(f'${swap(c[2]):02x}' for c in pal))
    consts = [x for x in a if x.startswith('.const') or x.startswith('//')]
    tables = [x for x in a if not x.startswith('.const')]
    (gen / 'assets_const.inc').write_text('\n'.join(consts) + '\n')
    (gen / 'assets.inc').write_text('\n'.join(tables) + '\n')
    return tab, len(blob)


def compose_preview(prev, tab):
    """Arena with Tiago standing on the floor, as the game's first screen should look."""
    import fighter_tiago as ft
    a = Image.open(prev / 'arena_rio.png').resize((320, 200), Image.NEAREST).convert('RGB')
    f = ft.frames()['idle'][0]
    im = fa.to_image(f, ft.PALETTE)
    mask = Image.fromarray(((f > 0) * 255).astype(np.uint8))
    a.paste(im, (96 - fa.ANCHOR[0], FLOOR_Y - fa.ANCHOR[1]), mask)
    a.resize((960, 600), Image.NEAREST).save(prev / 'stage1_composite.png')


def main():
    gen = ROOT / 'build/gen'
    prev = ROOT / 'build/preview'
    gen.mkdir(parents=True, exist_ok=True)
    prev.mkdir(parents=True, exist_ok=True)
    inc = ['// generated by tools/make_assets.py - do not edit']
    inc += [f'.const {k} = ${v:x}' for k, v in L.items()]
    (gen / 'layout.inc').write_text('\n'.join(inc) + '\n')
    n, pal = arena(gen, prev)
    tab, size = fighter(gen, prev, pal)
    compose_preview(prev, tab)
    print(f'arena: {n} glyphs ({n * 64} bytes), {L["ARENA_COLOURS"] - 1} colours')
    print(f'Tiago: {len(tab)} frames, {size} bytes, widths {sorted(set(t["w"] for t in tab))}')


if __name__ == '__main__':
    main()

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
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'assets/source'))
import fighter_art as fa      # noqa: E402
import import_fighter as imf  # noqa: E402

# ------------------------------------------------------------------ layout (single source of truth)
L = dict(
    BG_TOKENS=42,             # 42 FCM chars = 336 px; logical x 0..15 hidden under the left border
    ROW_TOKENS=80,
    VIS_ROWS=25,
    BUF_ROWS=26,              # + null row under the bottom border
    GOTOX_BIAS=16,
    ARENA_GFX=0x040000,       # FCM glyphs, char $1000+, max. 1000 glyphs
    SLOT_A=0x050000,          # fighter 1 frame slots (7 KB each)
    SLOT_B=0x051C00,
    SLOT_SIZE=0x1C00,
    BLANK_NCM=0x053800,       # one blank NCM glyph (ends every row)
    HUD_GFX=0x053840,         # energy bar glyphs (17 x 64 bytes)
    SCREEN_A=0x054000,
    SCREEN_B=0x055200,
    SLOT_C=0x056400,          # fighter 2 frame slots
    ARENA_MAP=0x058800,       # palette + clean screen + clean colour
    SLOT_D=0x05AC00,
    SAVED_SCR=0x05D000,
    SAVED_PAL0=0x05DB00,
    SAVED_ZP=0x05DE00,
    COLRAM=0xFF80000,
    COLOUR_A=0x1000,
    COLOUR_B=0x2400,
    ATTIC_F1=0x8000000,       # fighter packages in attic RAM (256 KB each)
    ATTIC_F2=0x8040000,
    ATTIC_F3=0x8080000,       # Stage 10: Malee (fighters live in the first MB: frame offsets have 20 bits)
    ATTIC_TGFX=0x8200000,     # Stage 6: pictures kept in attic RAM and copied to ARENA_GFX / ARENA_MAP
    ATTIC_TMAP=0x8210000,     #   title picture (Stage 10: moved up from $8080000 for the third fighter)
    ATTIC_AGFX=0x8220000,     #   arena Rio
    ATTIC_AMAP=0x8230000,
    ATTIC_ZGFX=0x8240000,     #   Stage 8: second arena (Zeche Zollverein)
    ATTIC_ZMAP=0x8250000,
    ATTIC_WGFX=0x8260000,     #   Stage 10: third arena (Wat Arun, Bangkok)
    ATTIC_WMAP=0x8270000,
    ATTIC_PACK=0x8700000,     # Stage 10: packed files are loaded here, then unpacked (src/unpack.asm)
    ARENA_COLOURS=176,        # palette entries 0..175 belong to the arena
    FIGHTER_BANK=12,          # fighter 1: bank 12, fighter 2: bank 13
    HUD_BANK=15,
    HUD_ROW=1,
    FONT_GFX=0x05E000,        # 16x16 font: 2 NCM glyphs per char
    FX_GFX=0x05F400,          # hit and block sparks (5 frames of 2x3 NCM glyphs)
    FX_BANK=11,
)
L['ROW_BYTES'] = L['ROW_TOKENS'] * 2
L['OVL_START'] = L['BG_TOKENS'] * 2
L['OVL_END'] = (L['ROW_TOKENS'] - 1) * 2
L['ARENA_CHAR'] = L['ARENA_GFX'] // 64
L['BLANK_CHAR'] = L['BLANK_NCM'] // 64
L['SLOT_A_CHAR'] = L['SLOT_A'] // 64
L['SLOT_B_CHAR'] = L['SLOT_B'] // 64
L['SLOT_C_CHAR'] = L['SLOT_C'] // 64
L['SLOT_D_CHAR'] = L['SLOT_D'] // 64
L['HUD_CHAR'] = L['HUD_GFX'] // 64
L['FONT_CHAR'] = L['FONT_GFX'] // 64
L['FX_CHAR'] = L['FX_GFX'] // 64
L['MAP_PAL_BYTES'] = L['ARENA_COLOURS'] * 3
L['CLEAN_SCR'] = L['ARENA_MAP'] + L['MAP_PAL_BYTES']
L['CLEAN_COL'] = L['CLEAN_SCR'] + L['BUF_ROWS'] * L['ROW_BYTES']
L['BUF_BYTES'] = L['BUF_ROWS'] * L['ROW_BYTES']
MAX_ARENA_GLYPHS = 1000
FLOOR_Y = 190                 # screen y of the fighters' anchor (the floor)


def alt_palette(pal):
    """Mirror-match colours (Stage 6): skin and hair tones (orange hues) stay, saturated costume colours turn
    by 150 degrees of hue, grey, black and white costume parts are tinted blue."""
    import colorsys
    out = []
    for k, (r, g, b) in enumerate(pal):
        if k == 0:
            out.append((r, g, b))
            continue
        h, l, sat = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if 0.02 <= h <= 0.14 and sat > 0.2:         # skin, tan, blond: keep
            out.append((r, g, b))
            continue
        if sat < 0.18:                              # white / grey / black: blue tint, keep the lightness
            h, sat = 0.60, 0.55 if 0.08 < l < 0.92 else 0.35
            l = min(l, 0.85)
        else:
            h = (h + 150 / 360) % 1.0
        r2, g2, b2 = colorsys.hls_to_rgb(h, l, sat)
        out.append((round(r2 * 255), round(g2 * 255), round(b2 * 255)))
    return out


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
    src = ROOT / 'assets' / 'art' / 'arena' / 'rio_source.png'
    if src.exists():                    # owner's generator picture (Stage 4b), brought to 320 x 200
        img = Image.open(src).convert('RGB').resize((320, 200), Image.BOX)
    else:
        img = arena_rio.draw()
    return picture(img, 'A-RIO', gen, prev / 'arena_rio.png')


def zollverein(gen, prev):
    """Stage 8: Konrad's home arena, Zeche Zollverein in Essen (owner's generator picture)"""
    img = Image.open(ROOT / 'assets' / 'art' / 'arena' / 'zollverein_source.png').convert('RGB').resize(
        (320, 200), Image.BOX)
    return picture(img, 'A-ZOLL', gen, prev / 'arena_zollverein.png')


def watarun(gen, prev):
    """Stage 10: Malee's home arena, Wat Arun in Bangkok (owner's generator picture)"""
    img = Image.open(ROOT / 'assets' / 'art' / 'arena' / 'watarun_source.png').convert('RGB').resize(
        (320, 200), Image.BOX)
    return picture(img, 'A-WAT', gen, prev / 'arena_watarun.png')


def title(gen, prev):
    """Stage 6: the owner's title picture, same format as an arena (shown on the title screen)"""
    src = ROOT / 'assets' / 'art' / 'title' / 'title_source.png'
    img = Image.open(src).convert('RGB').resize((320, 200), Image.BOX)
    # octree keeps small saturated details (Tiago's green belt) that median cut loses
    return picture(img, 'T-TITLE', gen, prev / 'title.png', Image.Quantize.FASTOCTREE)


def merge_glyphs(idx, pal, limit):
    """More than limit different 8 x 8 tiles: replace the rarest tiles by their most similar tile (colour
    distance summed over the 64 pixels) until limit tiles are left. Returns the new index picture."""
    rgb = np.array(pal, np.int32)
    h, w = idx.shape
    tiles = idx.reshape(h // 8, 8, w // 8, 8).transpose(0, 2, 1, 3).reshape(-1, 64)
    keys, inv, cnt = np.unique(tiles, axis=0, return_inverse=True, return_counts=True)
    inv = inv.reshape(-1)
    alive = list(range(len(keys)))
    target = {k: k for k in alive}
    col = rgb[keys]                                     # (n, 64, 3)
    merged = 0
    while len(alive) > limit:
        k = min(alive, key=lambda a: cnt[a])
        others = [a for a in alive if a != k]
        d = ((col[others] - col[k]) ** 2).sum(axis=(1, 2))
        best = others[int(np.argmin(d))]
        for a, t in target.items():
            if t == k:
                target[a] = best
        cnt[best] += cnt[k]
        alive.remove(k)
        merged += 1
    new = np.array([keys[target[a]] for a in inv]).reshape(h // 8, w // 8, 8, 8).transpose(0, 2, 1, 3)
    print(f'  {merged} similar tiles merged')
    return new.reshape(h, w)


def picture(img, name, gen, preview, method=Image.Quantize.MEDIANCUT):
    """320 x 200 picture -> <name>-GFX (FCM glyphs) and <name>-MAP (palette, clean RRB screen and colour)"""
    n = L['ARENA_COLOURS'] - 1          # entries 1..175; 0 stays black/transparent
    q = img.quantize(colors=n, method=method, dither=Image.Dither.NONE)
    idx = np.array(q, np.uint8).astype(np.int32) + 1
    qpal = q.getpalette()[:n * 3]
    pal = [(0, 0, 0)] + [tuple(qpal[i * 3:i * 3 + 3]) for i in range(n)]
    pal += [(0, 0, 0)] * (L['ARENA_COLOURS'] - len(pal))
    assert idx.max() < L['ARENA_COLOURS'] and idx.min() >= 1
    tiles = {idx[r * 8:r * 8 + 8, c * 8:c * 8 + 8].tobytes() for r in range(25) for c in range(40)}
    if len(tiles) > MAX_ARENA_GLYPHS - 1:              # glyph 0 is the blank one
        idx = merge_glyphs(idx, pal, MAX_ARENA_GLYPHS - 1)
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
        sys.exit(f'{name}: {len(order)} glyphs, max. {MAX_ARENA_GLYPHS}')
    (gen / f'{name}-GFX.bin').write_bytes(b''.join(order))
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
    (gen / f'{name}-MAP.bin').write_bytes(palb + scr + col)
    # preview of what the MEGA65 will show
    rgb = np.array(pal, np.uint8)[idx]
    Image.fromarray(rgb).resize((960, 600), Image.NEAREST).save(preview)
    print(f'{name}: {len(order)} glyphs')
    return len(order), pal


# ------------------------------------------------------------------ fighters
FIGHTERS = [('F-TIAGO', 'fighter_tiago', 'ATTIC_F1'), ('F-KONRAD', 'fighter_konrad', 'ATTIC_F2'),
            ('F-MALEE', 'fighter_malee', 'ATTIC_F3')]
ANIMS = ['idle', 'walk', 'lp', 'hp', 'lk', 'hk', 'hit', 'crouch', 'c_lp', 'c_lk', 'sweep', 'block', 'c_block',
         'jump', 'j_p', 'j_k', 'fall', 'getup', 'win', 'sp1']
MOVES = ['lp', 'hp', 'lk', 'hk', 'c_lp', 'c_lk', 'sweep', 'j_p', 'j_k', 'sp1']
ANIM_SLOTS = 32               # anim table index = fighter * 32 + animation
MOVE_SLOTS = 16               # move table index = fighter * 16 + move


def frame_block(f):
    """Trimmed NCM glyph block of one rendered frame: (data, w, h, xofs, ytop).
    Columns are trimmed to the 16-px columns that hold pixels, rows to the first glyph row with pixels
    (ytop = its y inside the canvas); the frame always reaches down to the canvas bottom."""
    cols = np.nonzero(f.any(axis=0))[0]
    rows = np.nonzero(f.any(axis=1))[0]
    x0, x1 = int(cols[0]), int(cols[-1])
    r0 = int(rows[0]) // 8
    h = fa.FRAME_H // 8 - r0
    w = (x1 - x0 + 16) // 16
    pad = np.zeros((fa.FRAME_H, w * 16), np.uint8)
    part = f[:, x0:x0 + w * 16]
    pad[:, :part.shape[1]] = part
    glyphs = [bytes(64)]
    for c in range(w):
        for r in range(r0, r0 + h):
            glyphs.append(ncm_glyph(pad[r * 8:r * 8 + 8, c * 16:c * 16 + 16]))
        glyphs.append(bytes(64))
    return b''.join(glyphs), w, h, x0 - fa.ANCHOR[0], r0 * 8


def fighters(gen, prev):
    import importlib
    tab, rows_first, rows_len, stats, moves, pals, mods = [], [], [], [], [], [], []
    all_rendered = []
    reaches = []
    for fi, (fname, modname, attic) in enumerate(FIGHTERS):
        m = importlib.import_module(modname)
        mods.append(m)
        an = m.anims()
        base = L[attic] - L['ATTIC_F1']
        blob = bytearray()
        # skeleton-drawn frames; animations with a sprite sheet in assets/art/<fighter>/ replace them
        drawn = {a: [fa.render(fr['pose'], m.COSTUME, fr.get('face', 'normal')) for fr in an[a]] for a in ANIMS}
        # Stage 5: the special's sheet has 4 drawn cells; SPECIAL['sheet'] maps them onto its 5 game frames
        counts = {a: len(an[a]) for a in ANIMS}
        counts['sp1'] = max(m.SPECIAL['sheet']) + 1
        art = imf.import_anims(ROOT / 'assets' / 'art' / modname[8:], drawn['idle'][0], counts)
        if 'sp1' in art:
            art['sp1'] = [art['sp1'][i] for i in m.SPECIAL['sheet']]
        # Stage 5: a special move without its own sheet yet borrows frames of another imported animation
        placeholder = set()
        src, idx = m.SPECIAL['placeholder']
        if art and 'sp1' not in art and src in art:
            art['sp1'] = [art[src][i] for i in idx]
            placeholder.add('sp1')
            print(f'  sp1: placeholder frames {idx} of {src}')
        palette = m.PALETTE
        if art:
            pal = np.array(m.PALETTE, np.uint8)
            mixed, weights = [], []
            for a in ANIMS:
                for k, img in enumerate(drawn[a]):
                    if a in art:
                        mixed.append(art[a][k])
                        weights.append(0 if a in placeholder else 1)
                    else:
                        mixed.append((pal[img], img > 0))
                        weights.append(0)       # only mapped onto the palette of the imported art
            idx, palette = imf.quantise(mixed, weights=weights)
            it = iter(idx)
            drawn = {a: [next(it) for _ in drawn[a]] for a in ANIMS}
        rendered = []
        art_boxes = []
        reach_f = {}                    # Stage 7: how far each move reaches (for the CPU opponent)
        for a in ANIMS:
            rows_first.append(len(tab))
            rows_len.append(len(an[a]))
            for fi, (fr, img) in enumerate(zip(an[a], drawn[a])):
                rendered.append(img)
                data, w, h, xofs, ytop = frame_block(img)
                if len(data) > L['SLOT_SIZE']:
                    sys.exit(f'{fname}: frame too large ({len(data)} bytes)')
                hb = fr['hit'] or (0, 0, 0, 0)
                if fr['hit'] and a in art:      # imported art: the box sits on the fist / foot / knee drawn
                    hb = imf.strike_box(art[a][fi][1], hb, margin=200 if a in ('j_p', 'j_k') else 8)
                    cap = getattr(m, 'REACH_CAP', {}).get(a)
                    if cap is not None and hb[1] > cap:     # Stage 8 balancing: shorten the box
                        hb = (min(hb[0], cap - 8), cap, hb[2], hb[3])
                    art_boxes.append(f'{a} {fi + 1}: {hb}')
                # walk frames: duration in half pixels walked (fighter.asm walk_step), not in video frames
                ticks = fr['ticks'] * m.STATS['walk_fwd'] if a == 'walk' else fr['ticks']
                if not 0 < ticks < 256:
                    sys.exit(f'{fname}: {a} frame duration {ticks} out of range')
                if fr['hit'] and a in MOVES:
                    reach_f[a] = max(reach_f.get(a, -128), hb[1])
                tab.append(dict(ofs=base + len(blob), glyphs=len(data) // 64, w=w, h=h, xofs=xofs, ytop=ytop,
                                ticks=ticks, hit=1 if fr['hit'] else 0, hb=hb))
                blob += data
        if art_boxes:
            print(f'  hit boxes from the art ({fname}): ' + '; '.join(art_boxes))
        # the special dashes until its first active frame (at most into animation frame 3, fighter.asm)
        pre = 0
        for fr in an['sp1'][:3]:
            if fr['hit']:
                break
            pre += fr['ticks']
        reach_f['sp1'] = reach_f.get('sp1', 0) + m.SPECIAL['dash'] * pre
        reaches.append([max(0, min(255, reach_f.get(k, 0))) for k in MOVES] + [0] * (MOVE_SLOTS - len(MOVES)))
        print(f'  reach: ' + ', '.join(f'{k} {reach_f.get(k, 0)}' for k in MOVES))
        rows_first += [0] * (ANIM_SLOTS - len(ANIMS))
        rows_len += [0] * (ANIM_SLOTS - len(ANIMS))
        if len(blob) > 0x40000:
            sys.exit(f'{fname}: larger than 256 KB')
        (gen / f'{fname}.bin').write_bytes(bytes(blob))
        fa.sheet(rendered, palette, scale=2, cols=8).save(prev / f'{modname[8:]}.png')
        all_rendered.append(rendered)
        st = m.STATS
        stats.append(st)
        moves.append([m.MOVES[k] for k in MOVES])
        st.setdefault('crouch_top', -60)
        pals.append(palette)
        print(f'{fname}: {len(rendered)} frames, {len(blob)} bytes')
    if len(tab) > 255:
        sys.exit('more than 255 frames')

    def bl(name, vals, fmt='${:02x}'):
        return f'{name}: .byte ' + ', '.join(fmt.format(v & 0xff) for v in vals)
    c = ['// generated by tools/make_assets.py - do not edit']
    for i, a in enumerate(ANIMS):
        c.append(f'.const ANIM_{a.upper()} = {i}')
    for i, mv in enumerate(MOVES):
        c.append(f'.const MOVE_{mv.upper()} = {i}')
    c.append(f'.const FRAME_COUNT = {len(tab)}')
    c.append(f'.const FRAME_TOP = {fa.ANCHOR[1]}          // anchor y inside the frame canvas')
    c.append(f'.const FLOOR_Y = {FLOOR_Y}')
    c.append(f'.const ANIM_SLOTS = {ANIM_SLOTS}')
    c.append(f'.const MOVE_SLOTS = {MOVE_SLOTS}')
    c.append(f'.const FIGHTER_COUNT = {len(mods)}')
    t = ['// generated by tools/make_assets.py - do not edit']
    t.append(bl('frame_ofs_lo', [x['ofs'] for x in tab]))
    t.append(bl('frame_ofs_hi', [x['ofs'] >> 8 for x in tab]))
    t.append(bl('frame_ofs_bk', [(x['ofs'] >> 16) & 0x0f for x in tab]))
    t.append(bl('frame_bytes_lo', [x['glyphs'] * 64 for x in tab]))
    t.append(bl('frame_bytes_hi', [(x['glyphs'] * 64) >> 8 for x in tab]))
    t.append(bl('frame_w', [x['w'] for x in tab]))
    t.append(bl('frame_h', [x['h'] for x in tab]))
    t.append(bl('frame_xofs', [x['xofs'] for x in tab]) + '   // signed')
    t.append(bl('frame_xofs_r', [-x['xofs'] - x['w'] * 16 for x in tab]) + '   // signed, facing left')
    t.append(bl('frame_ytop', [x['ytop'] for x in tab]))
    t.append(bl('frame_ticks', [x['ticks'] for x in tab]))
    t.append(bl('frame_hit', [x['hit'] for x in tab]))
    t.append(bl('frame_hb_x1', [x['hb'][0] for x in tab]) + '   // signed, facing right')
    t.append(bl('frame_hb_x2', [x['hb'][1] for x in tab]) + '   // signed, facing right')
    # hit-box heights above the floor (unsigned): lo = -y2 (clamped to 0), hi = -y1
    t.append(bl('frame_hb_lo', [max(0, -x['hb'][3]) for x in tab]))
    t.append(bl('frame_hb_hi', [max(0, -x['hb'][2]) for x in tab]))
    t.append(bl('anim_first', rows_first) + '   // [fighter * 32 + anim]')
    t.append(bl('anim_len', rows_len))
    t.append(bl('ft_health', [x['health'] for x in stats]))
    t.append(bl('ft_walk_fwd', [x['walk_fwd'] for x in stats]))
    t.append(bl('ft_walk_back', [x['walk_back'] for x in stats]))
    t.append(bl('ft_hurt_w', [x['hurt_w'] for x in stats]))
    t.append(bl('ft_hurt_h', [-x['hurt_top'] for x in stats]) + '   // height of the standing hurt box')
    t.append(bl('ft_crouch_h', [-x['crouch_top'] for x in stats]) + '   // height of the crouching hurt box')

    sp = [importlib.import_module(modname).SPECIAL for _, modname, _ in FIGHTERS]
    t.append(bl('ft_sp_motion', [{'qcf': 0, 'charge': 1, 'qcb': 2}[x['motion']] for x in sp]) + '   // 0 QCF, 1 charge, 2 QCB')
    t.append(bl('ft_sp_button', [{'punch': 0x10, 'kick': 0x20}[x['button']] for x in sp]) + '   // JOY_FIRE / JOY_B2')
    t.append(bl('ft_sp_dash', [x['dash'] for x in sp]) + '   // pixels per frame until the hit')

    def mv(k):
        return [(m[i][k] if i < len(m) else 0) for m in moves for i in range(MOVE_SLOTS)]
    t.append(bl('mv_damage', mv(0)) + '   // [fighter * 16 + move]')
    t.append(bl('mv_stun', mv(1)))
    t.append(bl('mv_push', mv(2)))
    t.append(bl('mv_height', mv(3)) + '   // 0 mid, 1 low, 2 overhead')
    t.append(bl('mv_knock', mv(4)))
    t.append(bl('mv_reach', [r for rr in reaches for r in rr]) + '   // front of the hit box, px from the anchor (special: + dash)')
    for i, m in enumerate(mods):
        t.append(f'ftname_{i}: ' + text_bytes(m.NAME))
    t.append('name_lo: .byte ' + ', '.join(f'<ftname_{i}' for i in range(len(mods))))
    t.append('name_hi: .byte ' + ', '.join(f'>ftname_{i}' for i in range(len(mods))))
    for i, m in enumerate(mods):
        t.append(f'ftcountry_{i}: ' + text_bytes(m.COUNTRY))
    t.append(bl('ft_home', [m.HOME_ARENA for m in mods]) + '   // home arena: 0 Rio, 1 Zollverein, 2 Wat Arun')
    t.append('country_lo: .byte ' + ', '.join(f'<ftcountry_{i}' for i in range(len(mods))))
    t.append('country_hi: .byte ' + ', '.join(f'>ftcountry_{i}' for i in range(len(mods))))
    # Stage 6: palettes per fighter type [type * 16 + colour]; the second set is the mirror-match colour
    # of player 2 (same fighter on both sides), derived automatically by alt_palette()
    alts = [alt_palette(pal) for pal in pals]
    for ch, nm in enumerate('rgb'):
        t.append(bl(f'ftpal_{nm}', [swap(col[ch]) for pal in pals for col in pal]))
    for ch, nm in enumerate('rgb'):
        t.append(bl(f'ftalt_{nm}', [swap(col[ch]) for pal in alts for col in pal]))
    for (_, modname, _), fr, alt in zip(FIGHTERS, all_rendered, alts):
        fa.sheet(fr[:8], alt, scale=2, cols=8).save(prev / f'{modname[8:]}_alt.png')
    hud = [(0, 0, 0), (18, 16, 30), (250, 206, 40), (255, 240, 150), (140, 20, 32), (236, 236, 244),
           (255, 140, 30)]
    hud += [(0, 0, 0)] * (16 - len(hud))
    for ch, nm in enumerate('rgb'):
        t.append(bl(f'pal_hud_{nm}', [swap(col[ch]) for col in hud]))
    for ch, nm in enumerate('rgb'):
        t.append(bl(f'pal_fx_{nm}', [swap(col[ch]) for col in FX_PAL]))
    (gen / 'assets_const.inc').write_text('\n'.join(c) + '\n')
    (gen / 'assets.inc').write_text('\n'.join(t) + '\n')
    # energy bar glyphs: amount 0..16 px filled from the left; rows 0 and 7 border
    g = []
    for k in range(17):
        a = np.full((8, 16), 4, np.uint8)
        a[1:7, :k] = 2
        a[1, :k] = 3
        a[0, :] = 5
        a[7, :] = 1
        g.append(ncm_glyph(a))
    (gen / 'HUD.bin').write_bytes(b''.join(g))
    return tab, mods


# ------------------------------------------------------------------ font (16x16, two NCM glyphs per char)
FONT_CHARS = ' 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!.*'
FONT5x7 = {
    '0': '01110 10001 10011 10101 11001 10001 01110', '1': '00100 01100 00100 00100 00100 00100 01110',
    '2': '01110 10001 00001 00010 00100 01000 11111', '3': '11110 00001 00001 01110 00001 00001 11110',
    '4': '00010 00110 01010 10010 11111 00010 00010', '5': '11111 10000 11110 00001 00001 10001 01110',
    '6': '00110 01000 10000 11110 10001 10001 01110', '7': '11111 00001 00010 00100 01000 01000 01000',
    '8': '01110 10001 10001 01110 10001 10001 01110', '9': '01110 10001 10001 01111 00001 00010 01100',
    'A': '01110 10001 10001 11111 10001 10001 10001', 'B': '11110 10001 10001 11110 10001 10001 11110',
    'C': '01110 10001 10000 10000 10000 10001 01110', 'D': '11100 10010 10001 10001 10001 10010 11100',
    'E': '11111 10000 10000 11110 10000 10000 11111', 'F': '11111 10000 10000 11110 10000 10000 10000',
    'G': '01110 10001 10000 10111 10001 10001 01111', 'H': '10001 10001 10001 11111 10001 10001 10001',
    'I': '01110 00100 00100 00100 00100 00100 01110', 'J': '00111 00010 00010 00010 00010 10010 01100',
    'K': '10001 10010 10100 11000 10100 10010 10001', 'L': '10000 10000 10000 10000 10000 10000 11111',
    'M': '10001 11011 10101 10101 10001 10001 10001', 'N': '10001 10001 11001 10101 10011 10001 10001',
    'O': '01110 10001 10001 10001 10001 10001 01110', 'P': '11110 10001 10001 11110 10000 10000 10000',
    'Q': '01110 10001 10001 10001 10101 10010 01101', 'R': '11110 10001 10001 11110 10100 10010 10001',
    'S': '01111 10000 10000 01110 00001 00001 11110', 'T': '11111 00100 00100 00100 00100 00100 00100',
    'U': '10001 10001 10001 10001 10001 10001 01110', 'V': '10001 10001 10001 10001 10001 01010 00100',
    'W': '10001 10001 10001 10101 10101 10101 01010', 'X': '10001 10001 01010 00100 01010 10001 10001',
    'Y': '10001 10001 10001 01010 00100 00100 00100', 'Z': '11111 00001 00010 00100 01000 10000 11111',
    '!': '00100 00100 00100 00100 00100 00000 00100', '.': '00000 00000 00000 00000 00000 01100 01100',
    '*': '00100 10101 01110 11111 01110 10101 00100', ' ': '00000 00000 00000 00000 00000 00000 00000',
}
TEXTS = {'txt_round1': 'ROUND 1', 'txt_round2': 'ROUND 2', 'txt_round3': 'FINAL ROUND', 'txt_fight': 'FIGHT!',
         'txt_ko': 'K.O.', 'txt_time': 'TIME', 'txt_draw': 'DRAW', 'txt_wins': 'WINS',
         # Stage 6: title, fighter selection, versus screen
         'txt_title1': 'WORLDFIGHT', 'txt_title2': '65', 'txt_press': 'PRESS FIRE', 'txt_choose': 'CHOOSE',
         'txt_fighter': 'YOUR FIGHTER', 'txt_p1': '1P', 'txt_p2': '2P', 'txt_ready': 'READY', 'txt_vs': 'VS', 'txt_loading': 'LOADING',
         'txt_cpu0': 'CPU EASY', 'txt_cpu1': 'CPU NORMAL', 'txt_cpu2': 'CPU HARD',
         'txt_winner': 'CHAMPION'}


def text_bytes(t):
    return '.byte ' + ', '.join([str(len(t))] + [str(FONT_CHARS.index(ch)) for ch in t])


def font(gen, prev):
    """Each char: 16x16 cell, the 5x7 pattern doubled to 10x14 at x 3, y 1, dark outline, shaded from
    light yellow (top) over yellow to orange (bottom). HUD palette bank: 1 outline, 3/2/6 shading."""
    glyphs = []
    sheet = np.zeros((16, 16 * len(FONT_CHARS)), np.uint8)
    for k, ch in enumerate(FONT_CHARS):
        rows = FONT5x7[ch].split()
        cell = np.zeros((16, 16), np.uint8)
        on = np.zeros((16, 16), bool)
        for y, row in enumerate(rows):
            for x, b in enumerate(row):
                if b == '1':
                    on[1 + 2 * y:3 + 2 * y, 3 + 2 * x:5 + 2 * x] = True
        for y in range(16):
            cell[y][on[y]] = 3 if y < 5 else (2 if y < 10 else 6)
        pad = np.pad(on, 1)
        nb = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
        cell[nb & ~on] = 1
        glyphs.append(ncm_glyph(cell[0:8]))
        glyphs.append(ncm_glyph(cell[8:16]))
        sheet[:, k * 16:k * 16 + 16] = cell
    (gen / 'FONT.bin').write_bytes(b''.join(glyphs))
    pal = np.array([(0, 0, 0), (18, 16, 30), (250, 206, 40), (255, 240, 150), (0, 0, 0), (0, 0, 0),
                    (255, 140, 30)] + [(0, 0, 0)] * 9, np.uint8)
    Image.fromarray(pal[sheet]).resize((sheet.shape[1] * 3, 48), Image.NEAREST).save(prev / 'font.png')
    t = ['// generated by tools/make_assets.py - do not edit']
    for name, txt in TEXTS.items():
        t.append(f'{name}: ' + text_bytes(txt))
    (gen / 'texts.inc').write_text('\n'.join(t) + '\n')
    return len(glyphs)


# ------------------------------------------------------------------ effects: hit and block sparks
FX_PAL = [(0, 0, 0), (120, 24, 20), (255, 255, 255), (255, 246, 170), (255, 214, 60), (255, 140, 30),
          (170, 220, 255), (70, 140, 240), (230, 246, 255)] + [(0, 0, 0)] * 7


def effects(gen, prev):
    """Frames 0-2: hit spark (bright star, burst, fading rays); 3-4: block spark (blue shield arc).
    Each 32x24 px = 2 NCM columns x 3 rows, stored like fighter frames (blank, columns, blank)."""
    import math
    W, H = 32, 24
    cx, cy = 16, 12
    frames = []
    for k, (r_in, r_out, thick) in enumerate(((2, 7, 3), (3, 11, 3), (7, 12, 1))):
        img = Image.new('P', (W, H), 0)
        d = ImageDraw.Draw(img)
        for i in range(8):
            a = math.radians(i * 45 + (22 if k == 1 else 0))
            ln = r_out if i % 2 == 0 else r_out * 0.65
            p0 = (cx + r_in * math.cos(a), cy + r_in * math.sin(a))
            p1 = (cx + ln * math.cos(a), cy + ln * math.sin(a))
            d.line((p0, p1), fill=5, width=thick + 2)
            d.line((p0, p1), fill=4 if k < 2 else 3, width=thick)
        if k < 2:
            d.ellipse((cx - r_out * 0.45, cy - r_out * 0.45, cx + r_out * 0.45, cy + r_out * 0.45), fill=3)
            d.ellipse((cx - r_out * 0.25, cy - r_out * 0.25, cx + r_out * 0.25, cy + r_out * 0.25), fill=2)
        frames.append(np.array(img, np.uint8))
    for k, r in enumerate((7, 10)):
        img = Image.new('P', (W, H), 0)
        d = ImageDraw.Draw(img)
        for rr, col in ((r + 1, 7), (r, 6), (r - 1, 8)):
            d.arc((cx - rr - 4, cy - rr, cx + rr - 4, cy + rr), -70, 70, fill=col, width=2)
        if k == 0:
            d.ellipse((cx + r - 7, cy - 2, cx + r - 3, cy + 2), fill=2)
        frames.append(np.array(img, np.uint8))
    blob = b''
    for f in frames:
        glyphs = [bytes(64)]
        for c in range(2):
            for r in range(3):
                glyphs.append(ncm_glyph(f[r * 8:r * 8 + 8, c * 16:c * 16 + 16]))
            glyphs.append(bytes(64))
        blob += b''.join(glyphs)
    (gen / 'FX.bin').write_bytes(blob)
    pal = np.array(FX_PAL, np.uint8)
    sheet = np.concatenate(frames, axis=1)
    Image.fromarray(pal[sheet]).resize((sheet.shape[1] * 4, H * 4), Image.NEAREST).save(prev / 'effects.png')
    return len(frames), len(blob)


def compose_preview(prev, mods):
    """Arena with both fighters facing each other, as the game's first screen should look."""
    a = Image.open(prev / 'arena_rio.png').resize((320, 200), Image.NEAREST).convert('RGB')
    for i, (m, x) in enumerate(zip(mods, (96, 224))):
        f = fa.render(m.anims()['idle'][0]['pose'], m.COSTUME)
        if i:
            f = f[:, ::-1]
            ax = fa.FRAME_W - 1 - fa.ANCHOR[0]
        else:
            ax = fa.ANCHOR[0]
        im = fa.to_image(f, m.PALETTE)
        mask = Image.fromarray(((f > 0) * 255).astype(np.uint8))
        a.paste(im, (x - ax, FLOOR_Y - fa.ANCHOR[1]), mask)
    a.resize((960, 600), Image.NEAREST).save(prev / 'stage2_composite.png')


def main():
    gen = ROOT / 'build/gen'
    prev = ROOT / 'build/preview'
    gen.mkdir(parents=True, exist_ok=True)
    prev.mkdir(parents=True, exist_ok=True)
    inc = ['// generated by tools/make_assets.py - do not edit']
    inc += [f'.const {k} = ${v:x}' for k, v in L.items()]
    (gen / 'layout.inc').write_text('\n'.join(inc) + '\n')
    n, pal = arena(gen, prev)
    zollverein(gen, prev)
    watarun(gen, prev)
    title(gen, prev)
    tab, mods = fighters(gen, prev)
    nfont = font(gen, prev)
    nfx, fxsize = effects(gen, prev)
    compose_preview(prev, mods)
    print(f'arena: {n} glyphs ({n * 64} bytes), {L["ARENA_COLOURS"] - 1} colours')
    print(f'frames: {len(tab)}, widths {sorted(set(t["w"] for t in tab))}; font: {nfont} glyphs; '
          f'effects: {nfx} frames, {fxsize} bytes')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Skeleton renderer for WorldFight65 fighters (Claude's art pipeline).

A pose is a dict of joint positions in pixels relative to the fighter's anchor (the point on the floor
between the feet; x grows forward, y grows downwards, so the head has y about -86). A costume says which
colours and widths the body parts have. render() draws the pose into a FRAME_W x FRAME_H canvas of
palette indices (0 = transparent): shaped limbs and muscles, faces with expressions, hair and beards,
clothing details, a dark outline, light from the front-top and a warm rim of evening light at the back.

Joints: head, neck, sho_f, sho_b (shoulders front/back), elb_f, elb_b, hand_f, hand_b, hip_f, hip_b,
knee_f, knee_b, ankle_f, ankle_b, toe_f, toe_b.  "_f" is the limb nearer to the viewer.
"""
import math

import numpy as np
from PIL import Image, ImageDraw

FRAME_W = 112         # canvas; trimmed to 16-px columns later
FRAME_H = 104         # 13 glyph rows
ANCHOR = (44, 101)    # canvas position of the anchor (floor point)

OUTLINE = 1           # palette index of the outline colour


def _mask():
    return Image.new('L', (FRAME_W, FRAME_H), 0)


def _pt(p):
    return (ANCHOR[0] + p[0], ANCHOR[1] + p[1])


def capsule(m, a, b, w):
    d = ImageDraw.Draw(m)
    a, b = _pt(a), _pt(b)
    d.line((a, b), fill=255, width=int(w))
    r = w / 2
    for (x, y) in (a, b):
        d.ellipse((x - r + 0.5, y - r + 0.5, x + r - 0.5, y + r - 0.5), fill=255)


def poly(m, pts):
    ImageDraw.Draw(m).polygon([_pt(p) for p in pts], fill=255)


def disc(m, c, r):
    x, y = _pt(c)
    ImageDraw.Draw(m).ellipse((x - r, y - r, x + r, y + r), fill=255)


def limb(m, a, b, wa, wb, bulge=0.0, at=0.4, cap_b=True):
    """Tapered limb from joint a (width wa) to joint b (width wb), with a muscle bulge of `bulge` pixels
    (extra width) centred at fraction `at` of the length; round ends."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    ln = max(1e-3, (dx * dx + dy * dy) ** 0.5)
    nx, ny = -dy / ln, dx / ln
    left, right = [], []
    n = 8
    for i in range(n + 1):
        t = i / n
        w = wa + (wb - wa) * t
        if bulge:
            w += bulge * max(0.0, 1 - abs(t - at) / 0.45)
        cx, cy = ax + dx * t, ay + dy * t
        left.append((cx + nx * w / 2, cy + ny * w / 2))
        right.append((cx - nx * w / 2, cy - ny * w / 2))
    poly(m, left + right[::-1])
    disc(m, a, wa / 2 - 0.3)
    if cap_b:
        disc(m, b, wb / 2 - 0.3)


def foot_shape(m, ankle, toe, w):
    """A foot or shoe in profile: flat sole from the heel to the toes, rounded toes, instep rising to the
    ankle. Built in the foot's own direction (ankle -> toe), so it also works for kicks."""
    dx, dy = toe[0] - ankle[0], toe[1] - ankle[1]
    ln = max(1e-3, (dx * dx + dy * dy) ** 0.5)
    ux, uy = dx / ln, dy / ln
    nx, ny = uy, -ux                       # "up" from the sole (for a flat foot: -y)
    h = w / 2

    def q(base, a, b):
        return (base[0] + ux * a + nx * b, base[1] + uy * a + ny * b)
    poly(m, [q(ankle, -3, -h + 0.5), q(toe, 0.5, -h + 0.5), q(toe, 1.5, -h * 0.4), q(toe, 1, 0.2),
             q(toe, -1.5, h * 0.4), q(ankle, 2, h), q(ankle, -1, h + 1), q(ankle, -3.5, h * 0.3)])


def line(m, a, b, w=1):
    ImageDraw.Draw(m).line((_pt(a), _pt(b)), fill=255, width=w)


def _edges(a):
    """masks of the outermost pixels: back (-x), front (+x), top, bottom"""
    pad = np.pad(a, 1)
    back = a & ~pad[1:-1, :-2]
    front = a & ~pad[1:-1, 2:]
    top = a & ~pad[:-2, 1:-1]
    bottom = a & ~pad[2:, 1:-1]
    return back, front, top, bottom


def shade_layer(canvas, m, zone, back=False, rim=None, blend=None):
    """Paint mask m with a colour zone (base, shade, light, dark). Light from the front and the top
    (light edge), shadow at the back and the bottom (2 px), a warm rim of evening light on the back edge.
    Far-side limbs (back=True) use the shade as base and the dark colour as shadow, without light.
    blend: pixels where no edge is drawn (where a limb grows out of the body), so joints look seamless."""
    base, shade, light, dark = zone
    a = np.array(m) > 0
    if back:
        base, shade, light = shade, dark, None
    canvas[a] = base
    b1, f1, t1, d1 = _edges(a)
    pad2 = np.pad(a, 2)
    b2 = a & ~pad2[2:-2, :-4]
    d2 = a & ~pad2[4:, 2:-2]
    keep = ~blend if blend is not None else np.ones_like(a)
    canvas[(b2 | d2) & keep] = shade
    if light is not None:
        canvas[(f1 | t1) & ~(b2 | d2) & keep] = light
    if rim is not None and not back:
        canvas[b1 & ~d1 & keep] = rim
    return a


class Costume:
    """Colours are palette indices; zones are (base, shade, light, dark).
    Zones: skin, torso, pelvis, thigh, shin, foot. hair = (base, shade, light).
    Flags: bare_torso (muscle lines), neckline (singlet), stripes (colours of the side seam stripes on
    torso and thighs), short_thigh (the thigh zone covers only the upper part of the thigh), loose (wide
    trousers with folds), shoes (laces and sole), belt / belt2 (cord belt with a knot and tassels),
    hair_style ('curly' or 'buzz'), beard. Faces: eye (white), pupil, mouth; rim = evening light colour.
    Widths: neck_w, w_upper (shoulder, elbow, bulge), w_fore (elbow, wrist, bulge), w_thigh (hip, knee, bulge),
    w_shin (knee, ankle, bulge), hand_r, foot_w, head_r, chest (half width of the torso at the chest)."""
    def __init__(self, **kw):
        self.belt = None
        self.belt2 = None
        self.neckline = False
        self.bare_torso = False
        self.stripes = ()
        self.short_thigh = False
        self.loose = False
        self.shoes = False
        self.beard = False
        self.hair_style = 'curly'
        self.rim = None
        self.chest = 9
        self.__dict__.update(kw)


def draw_head(canvas, solid, c, head_pt, neck_pt, face):
    """Head in profile (facing +x) at head_pt: skull, jaw, nose, ear, hair or buzz cut, beard, eye, brow,
    mouth. Draws into canvas / solid."""
    yy, xx = np.indices(canvas.shape)

    def near(pt, r):
        x, y = _pt(pt)
        return (xx - x) ** 2 + (yy - y) ** 2 <= r * r

    def group(fns, zone, back=False, roots=()):
        m = _mask()
        for fn in fns:
            fn(m)
        blend = np.zeros_like(solid)
        for pt, r in roots:
            blend |= near(pt, r)
        a = shade_layer(canvas, m, zone, back, c.rim if zone == c.skin else None, blend)
        solid[:] |= a
        return a

    def paint(fn, colour, only=None):
        m = _mask()
        fn(m)
        a = np.array(m) > 0
        if only is not None:
            a &= only
        canvas[a] = colour
        return a

    hx, hy = head_pt
    r = c.head_r

    def L(ax, ay):
        """point in head units (r) relative to the head centre, facing +x"""
        return (hx + ax * r, hy + ay * r)

    def head(m):
        # cranium: longer than high, reaching back
        x0, y0 = _pt(L(-1.05, -1.02))
        x1, y1 = _pt(L(0.85, 0.62))
        ImageDraw.Draw(m).ellipse((x0, y0, x1, y1), fill=255)
        # face in profile: forehead, brow, nose, lips, chin, jaw
        poly(m, [L(0.45, -0.85), L(0.86, -0.42), L(0.92, -0.12), L(0.84, 0.02), L(1.22, 0.4), L(0.94, 0.52),
                 L(1.0, 0.64), L(0.92, 0.74), L(1.0, 0.88), L(0.96, 1.04), L(0.72, 1.16), L(0.2, 1.08),
                 L(-0.28, 0.74), L(-0.45, 0.2), L(0.0, -0.6)])
    hd = group([head], c.skin, roots=[(neck_pt, c.neck_w * 0.8)])
    paint(lambda m: poly(m, [L(-0.25, 0.05), L(-0.02, 0.1), L(-0.02, 0.45), L(-0.22, 0.42)]), c.skin[1], hd)  # ear
    paint(lambda m: line(m, L(-0.14, 0.18), L(-0.12, 0.32)), c.skin[3], hd)
    paint(lambda m: line(m, L(0.55, 0.32), L(0.72, 0.42)), c.skin[1], hd)             # cheek
    # hairline: from the forehead down to the nape; hair lies on the upper-back side of this line
    (ax_, ay_), (bx_, by_) = _pt(L(0.62, -0.72)), _pt(L(-0.42, 0.58))
    upper = ((xx - ax_) * (by_ - ay_) - (yy - ay_) * (bx_ - ax_)) < 0
    if c.hair_style == 'curly':
        # thick curls: the hair region of the head, grown outwards by a pixel
        hreg = hd & upper
        pad = np.pad(hreg, 1)
        grown = hreg | pad[:-2, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
        grown &= upper | hreg
        canvas[grown] = c.hair[0]
        canvas[grown & (((xx * 3 + yy * 5) % 7) == 0)] = c.hair[2]
        canvas[grown & (((xx * 3 + yy * 5) % 7) == 3)] = c.hair[1]
        solid |= grown
    elif c.hair_style == 'buzz':
        # military cut: a very short layer on top, the back and the sides shaved (stubble on the skin)
        pad = np.pad(hd, 2)
        edge = hd & ~(pad[:-4, 2:-2] & pad[1:-3, 2:-2])            # the top 2 px of the head
        top = hd & upper & edge & (yy < _pt(L(0, -0.3))[1])
        canvas[top] = c.hair[0]
        canvas[top & ~np.roll(hd, 1, axis=0)] = c.hair[2]
        sides = hd & upper & ~top
        canvas[sides & (((xx * 3 + yy * 5) % 9) == 0)] = c.hair[1]   # stubble
    if c.beard:
        (bx0, by0), (bx1, by1) = _pt(L(-0.3, 0.34)), _pt(L(0.8, 0.5))
        below = ((xx - bx0) * (by1 - by0) - (yy - by0) * (bx1 - bx0)) < 0
        bm = hd & below & (xx >= _pt(L(-0.35, 0))[0])
        canvas[bm] = c.hair[0]
        canvas[bm & ~np.roll(bm, -1, axis=0)] = c.hair[1]
        canvas[bm & (((xx * 3 + yy * 5) % 7) == 2)] = c.hair[1]
    # eye, brow, mouth
    ex, ey = _pt(L(0.6, -0.04))
    ex, ey = int(round(ex)), int(round(ey))
    dark_brow = c.hair[1] if c.hair_style != 'curly' else c.hair[0]
    if face == 'hit':
        canvas[ey, ex:ex + 2] = dark_brow if c.hair_style != 'curly' else OUTLINE
    else:
        canvas[ey, ex] = c.eye
        canvas[ey, ex + 1] = c.pupil
    bx, by = _pt(L(0.62, -0.32))
    bx, by = int(round(bx)), int(round(by))
    canvas[by, bx - 1:bx + 2] = dark_brow
    mx, my = _pt(L(0.82, 0.66))
    mx, my = int(round(mx)), int(round(my))
    if face in ('hit', 'win'):
        canvas[my:my + 2, mx:mx + 2] = c.mouth
    else:
        canvas[my, mx:mx + 2] = c.mouth

def render(pose, c, face='normal'):
    """Return (FRAME_H, FRAME_W) uint8 array of palette indices. face: 'normal', 'hit' or 'win'.
    Parts of the same material are merged and shaded as one area (no seams inside an arm, a trouser leg or
    the singlet), and no edges are drawn where a limb grows out of the body (shoulder, hip, knee)."""
    canvas = np.zeros((FRAME_H, FRAME_W), np.uint8)
    solid = np.zeros_like(canvas, dtype=bool)
    p = pose
    yy, xx = np.indices(canvas.shape)

    def near(pt, r):
        x, y = _pt(pt)
        return (xx - x) ** 2 + (yy - y) ** 2 <= r * r

    def group(fns, zone, back=False, roots=()):
        """draw several shapes as one area of one material; roots = [(joint, radius)] without edges"""
        m = _mask()
        for fn in fns:
            fn(m)
        blend = np.zeros_like(solid)
        for pt, r in roots:
            blend |= near(pt, r)
        rim = c.rim if zone == c.skin else None       # evening light on the skin only
        a = shade_layer(canvas, m, zone, back, rim, blend)
        solid[:] |= a
        return a

    def paint(fn, colour, only=None):
        m = _mask()
        fn(m)
        a = np.array(m) > 0
        if only is not None:
            a &= only
        canvas[a] = colour
        return a

    def upper(side):
        return lambda m: limb(m, p['sho_' + side], p['elb_' + side], c.w_upper[0], c.w_upper[1], c.w_upper[2], 0.45)

    def fore(side):
        return lambda m: limb(m, p['elb_' + side], p['hand_' + side], c.w_fore[0], c.w_fore[1], c.w_fore[2], 0.3)

    def hand(side):
        return lambda m: disc(m, p['hand_' + side], c.hand_r)

    def thigh(side, frac=1.0):
        a, b = p['hip_' + side], p['knee_' + side]
        b = (a[0] + (b[0] - a[0]) * frac, a[1] + (b[1] - a[1]) * frac)
        w2 = c.w_thigh[0] + (c.w_thigh[1] - c.w_thigh[0]) * frac
        return lambda m: limb(m, a, b, c.w_thigh[0], w2, c.w_thigh[2], 0.35)

    def shin(side):
        k, a = p['knee_' + side], p['ankle_' + side]
        if c.loose:                                   # wide trousers end just above the ankle
            a = (k[0] + (a[0] - k[0]) * 0.93, k[1] + (a[1] - k[1]) * 0.93)
        return lambda m: limb(m, k, a, c.w_shin[0], c.w_shin[1], c.w_shin[2], 0.3, cap_b=False)

    def foot(side):
        return lambda m: foot_shape(m, p['ankle_' + side], p['toe_' + side], c.foot_w)

    def along(a, b, f0, f1, off):
        """segment from fraction f0 to f1 of a->b, shifted sideways by off pixels (towards the back)"""
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = max(1e-3, (dx * dx + dy * dy) ** 0.5)
        nx, ny = dy / ln, -dx / ln
        if nx > 0:
            nx, ny = -nx, -ny
        return ((a[0] + dx * f0 + nx * off, a[1] + dy * f0 + ny * off),
                (a[0] + dx * f1 + nx * off, a[1] + dy * f1 + ny * off))

    hf, hb = p['hip_f'], p['hip_b']

    def pelvis(m):
        poly(m, [(hb[0] - 2, hb[1] - 4), (hf[0] + 3, hf[1] - 4), (hf[0] + 3, hf[1] + 3), (hb[0] - 1, hb[1] + 3)])

    def arm_group(side, back):
        a = group([upper(side), fore(side), hand(side)], c.skin, back,
                  [(p['sho_' + side], c.w_upper[0] * 0.55), (p['elb_' + side], c.w_fore[0] * 0.35)])
        if not back:                                  # knuckle line
            hx2, _ = _pt(p['hand_' + side])
            canvas[near(p['hand_' + side], c.hand_r) & a & (np.abs(xx - hx2) < 0.6)] = c.skin[1]

    def leg_skin_parts(side, back):
        """the parts of a leg that are not covered by the torso group"""
        hip, knee, ank = p['hip_' + side], p['knee_' + side], p['ankle_' + side]
        roots = [(hip, c.w_thigh[0] * 0.8), (knee, c.w_shin[0] * 0.7)]
        if c.short_thigh:                             # bare leg in one piece; the singlet part comes later
            group([thigh(side), shin(side)], c.skin, back, roots)
            if back:
                group([thigh(side, 0.62)], c.thigh, back, roots[:1])
        elif c.thigh == c.shin:                       # trouser leg in one piece (with the pelvis, near side)
            fns = [thigh(side), shin(side)]
            if not back and c.pelvis == c.thigh and c.pelvis != c.torso:
                fns.insert(0, pelvis)
            group(fns, c.thigh, back, roots)
        else:
            group([thigh(side)], c.thigh, back, roots[:1])
            group([shin(side)], c.shin, back, roots[1:])
        f = group([foot(side)], c.foot, back, [(ank, c.foot_w * 0.6)])
        if c.shoes and not back:
            toe = p['toe_' + side]
            for t in (0.3, 0.65):
                x, y = _pt((ank[0] + (toe[0] - ank[0]) * t, ank[1] + (toe[1] - ank[1]) * t - c.foot_w / 2 + 1.5 - t))
                if 0 <= int(y) < FRAME_H and 0 <= int(x) < FRAME_W and f[int(y), int(x)]:
                    canvas[int(y), int(x)] = c.eye            # laces
        if c.loose and not back:                      # folds in wide trousers
            for (a, b, f0, f1, off) in ((hip, knee, 0.35, 0.85, 2), (knee, ank, 0.2, 0.75, 2)):
                q0, q1 = along(a, b, f0, f1, off)
                paint(lambda m: line(m, q0, q1), c.thigh[1], solid)

    # ---- far side (a far arm striking across the body is drawn in front of the torso instead)
    b_front = pose.get('_b_front', False)
    if not b_front:
        arm_group('b', True)
    leg_skin_parts('b', True)
    if c.short_thigh:
        leg_skin_parts('f', False)                    # bare near leg below the singlet
    # ---- neck, torso (with the pelvis and the singlet part of the near thigh if they share the material)
    sf, sb = p['sho_f'], p['sho_b']
    mid = ((sf[0] + sb[0]) / 2, (sf[1] + sb[1]) / 2)
    hipm = ((hf[0] + hb[0]) / 2, (hf[1] + hb[1]) / 2)
    ax, ay = hipm[0] - mid[0], hipm[1] - mid[1]
    ln = max(1e-3, (ax * ax + ay * ay) ** 0.5)
    ux, uy = ax / ln, ay / ln                    # down the spine
    nx, ny = -uy, ux                             # towards the front (for an upright body: +x)
    if nx < 0:
        nx, ny = -nx, -ny

    def tpt(t, side_w):
        return (mid[0] + ax * t + nx * side_w, mid[1] + ay * t + ny * side_w)

    def torso(m):
        ch = c.chest
        # chest at the front; the back is flatter, so a bent-forward body does not get a hump
        pts = [tpt(-0.08, ch * 0.75), tpt(0.12, ch), tpt(0.45, ch * 0.78), tpt(0.8, ch * 0.72), tpt(1.05, ch * 0.75),
               tpt(1.05, -ch * 0.72), tpt(0.7, -ch * 0.66), tpt(0.3, -ch * 0.72), tpt(0.0, -ch * 0.7),
               tpt(-0.1, -ch * 0.5)]
        poly(m, pts)

    def neck(m):
        limb(m, p['neck'], tpt(0.02, 0), c.neck_w, c.neck_w + 1)

    tfns = [torso]
    if c.pelvis == c.torso:
        tfns.append(pelvis)
    if c.short_thigh and c.thigh == c.torso:
        tfns.append(thigh('f', 0.62))
    if c.torso == c.skin:
        t = group([neck] + tfns, c.skin, roots=[(p['neck'], c.neck_w)])
    else:
        group([neck], c.skin)
        t = group(tfns, c.torso, roots=[(hf, c.w_thigh[0] * 0.8)])
    if c.neckline:                               # singlet: skin at the neck and the shoulders
        paint(lambda m: poly(m, [tpt(-0.1, -1), tpt(-0.1, c.chest * 0.7), tpt(0.18, c.chest * 0.25)]),
              c.skin[0], t)
    if c.bare_torso:                             # chest and belly
        q = [tpt(0.3, c.chest * 0.85), tpt(0.36, c.chest * 0.3), tpt(0.33, -c.chest * 0.1)]
        paint(lambda m: ImageDraw.Draw(m).line([_pt(v) for v in q], fill=255), c.torso[1], t)
        paint(lambda m: line(m, tpt(0.42, c.chest * 0.45), tpt(0.92, c.chest * 0.45)), c.torso[1], t)
        for tt in (0.55, 0.7):
            paint(lambda m: line(m, tpt(tt, c.chest * 0.25), tpt(tt, c.chest * 0.65)), c.torso[1], t)
    for k, col in enumerate(c.stripes):          # side seam stripes on the torso and the near thigh
        paint(lambda m: line(m, tpt(0.05, k - 1.0), tpt(1.0, k - 1.0)), col, t)
        q0, q1 = along(hf, p['knee_f'], 0.0, 0.58 if c.short_thigh else 0.95, k - 0.5)
        paint(lambda m: line(m, q0, q1), col, solid)
    # ---- near leg (trousers: one piece with the pelvis)
    if not c.short_thigh:
        if c.pelvis != c.torso and c.pelvis != c.thigh:
            group([pelvis], c.pelvis)
        leg_skin_parts('f', False)
    if c.belt is not None:
        belt = paint(lambda m: line(m, (hb[0] - 3, hb[1] - 3), (hf[0] + 3, hf[1] - 3), 3), c.belt)
        canvas[belt & ((xx // 2) % 2 == 0)] = c.belt2
        k = (hf[0] + 2, hf[1] - 3)                # knot with two tassels
        paint(lambda m: disc(m, k, 1.5), c.belt2)
        for dx, ln2 in ((0, 9), (2, 7)):
            a = paint(lambda m: line(m, k, (k[0] + dx + 1, k[1] + ln2)), c.belt)
            solid |= a
            paint(lambda m: disc(m, (k[0] + dx + 1, k[1] + ln2), 1), c.belt2)
    # ---- head: drawn upright, then turned with the neck (lying and falling fighters look up / backwards)
    nk, hdp = p['neck'], p['head']
    ang = math.degrees(math.atan2(-(hdp[1] - nk[1]), hdp[0] - nk[0])) - 90   # counter-clockwise from upright
    dist = ((hdp[0] - nk[0]) ** 2 + (hdp[1] - nk[1]) ** 2) ** 0.5
    if abs(ang) < 25:                             # small tilts: keep the head as it is (crisp pixels)
        draw_head(canvas, solid, c, hdp, nk, face)
    else:
        # upright head above an upright neck at the same position, then rotated about the neck
        up_head = (nk[0], nk[1] - dist)
        hc = np.zeros_like(canvas)
        hs = np.zeros_like(solid)
        draw_head(hc, hs, c, up_head, nk, face)
        cx, cy = _pt(nk)
        rot = Image.fromarray(hc).rotate(ang, resample=Image.NEAREST, center=(cx, cy))
        rs = Image.fromarray((hs * 255).astype(np.uint8)).rotate(ang, resample=Image.NEAREST, center=(cx, cy))
        rc, rm = np.array(rot), np.array(rs) > 0
        canvas[rm] = rc[rm]
        solid |= rm
    # ---- far arm in front (rear-hand strikes), then the near arm
    if b_front:
        arm_group('b', False)
    arm_group('f', False)
    # ---- outline around the whole silhouette
    pad = np.pad(solid, 1)
    nb = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
    canvas[nb & ~solid] = OUTLINE
    return canvas


def to_image(frame, palette, scale=1):
    rgb = np.zeros(frame.shape + (3,), np.uint8)
    for i, col in enumerate(palette):
        rgb[frame == i] = col
    img = Image.fromarray(rgb)
    return img.resize((img.width * scale, img.height * scale), Image.NEAREST)


def sheet(frames, palette, scale=3, cols=6, bg=(70, 90, 110)):
    w, h = FRAME_W * scale, FRAME_H * scale
    rows = (len(frames) + cols - 1) // cols
    out = Image.new('RGB', (w * cols, h * rows), bg)
    for i, f in enumerate(frames):
        im = to_image(f, palette, scale)
        mask = Image.fromarray(((f > 0) * 255).astype(np.uint8)).resize(im.size, Image.NEAREST)
        out.paste(im, ((i % cols) * w, (i // cols) * h), mask)
    return out


def lerp_pose(a, b, t):
    return {k: (a[k][0] + (b[k][0] - a[k][0]) * t, a[k][1] + (b[k][1] - a[k][1]) * t) for k in a
            if not k.startswith('_')}


# ------------------------------------------------------------------ pose building
import math as _m


def ik(root, end, l1, l2, bend=1):
    """Middle joint of a two-bone limb. bend=+1: knee-like (forwards for a leg pointing down),
    bend=-1: elbow-like (downwards for an arm pointing forwards)."""
    dx, dy = end[0] - root[0], end[1] - root[1]
    d = max(1e-3, min(_m.hypot(dx, dy), l1 + l2 - 0.01))
    a = _m.atan2(dy, dx)
    cosb = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    b = _m.acos(max(-1.0, min(1.0, cosb)))
    ang = a - b * bend
    return (root[0] + l1 * _m.cos(ang), root[1] + l1 * _m.sin(ang))


def build(hip=(0, -45), lean=0.0, ankle_f=(15, -3), ankle_b=(-14, -3), toe_f=None, toe_b=None,
          hand_f=(15, -77), hand_b=(2, -54), body=None, head=(0, 0)):
    """Pose from a few targets. lean: torso tilt in degrees (+ = forwards). body: dict of segment
    lengths (thigh, shin, upper, fore, torso, shoulder and hip half widths). Elbows bend downwards, knees forwards."""
    b = dict(thigh=23, shin=22, upper=13, fore=13, torso=26, shoulder=5, hips=3)
    if body:
        b.update(body)
    r = _m.radians(lean)
    chest = (hip[0] + b['torso'] * _m.sin(r), hip[1] - b['torso'] * _m.cos(r))
    p = {'hip_f': (hip[0] + b['hips'], hip[1]), 'hip_b': (hip[0] - b['hips'], hip[1]),
         'ankle_f': ankle_f, 'ankle_b': ankle_b,
         'sho_f': (chest[0] + b['shoulder'], chest[1]), 'sho_b': (chest[0] - b['shoulder'], chest[1] - 1),
         'hand_f': hand_f, 'hand_b': hand_b}
    p['neck'] = (chest[0] + 2 + 6 * _m.sin(r), chest[1] - 6)
    p['head'] = (p['neck'][0] + 2 + 8 * _m.sin(r) + head[0], p['neck'][1] - 8 + head[1])
    p['toe_f'] = toe_f or (ankle_f[0] + 6, ankle_f[1] + 2)
    p['toe_b'] = toe_b or (ankle_b[0] + 6, ankle_b[1] + 2)
    p['knee_f'] = ik(p['hip_f'], ankle_f, b['thigh'], b['shin'], 1)
    p['knee_b'] = ik(p['hip_b'], ankle_b, b['thigh'], b['shin'], 1)
    p['elb_f'] = ik(p['sho_f'], hand_f, b['upper'], b['fore'], -1)
    p['elb_b'] = ik(p['sho_b'], hand_b, b['upper'], b['fore'], -1)
    return p


def box_at(pose, joint, w=14, h=12):
    """Hit box (x1, x2, y1, y2) around a joint, relative to the anchor, facing right."""
    x, y = pose[joint]
    return (int(round(x - w / 2)), int(round(x + w / 2)), int(round(y - h / 2)), int(round(y + h / 2)))


def frame(pose, ticks, hit=None, face='normal', b_front=False):
    """One animation frame: pose, duration in video frames, optional hit-box joint, facial expression
    ('normal', 'hit', 'win'); b_front: the far arm strikes across the body and is drawn in front."""
    if b_front:
        pose = dict(pose, _b_front=True)
    return dict(pose=pose, ticks=ticks, hit=box_at(pose, hit) if hit else None, face=face)

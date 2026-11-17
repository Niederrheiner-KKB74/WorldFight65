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

FRAME_W = 144         # canvas; trimmed to 16-px columns later (trimmed frames stay <= 112 px wide)
FRAME_H = 112         # 14 glyph rows (room above the head for a raised fist)
ANCHOR = (64, 109)    # canvas position of the anchor (floor point)

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
        x0, y0 = _pt(L(-0.78, -0.98))
        x1, y1 = _pt(L(0.85, 0.62))
        ImageDraw.Draw(m).ellipse((x0, y0, x1, y1), fill=255)
        # face in profile: forehead, brow, nose, lips, chin, jaw
        poly(m, [L(0.45, -0.85), L(0.86, -0.42), L(0.92, -0.12), L(0.84, 0.02), L(1.22, 0.4), L(0.94, 0.52),
                 L(1.0, 0.64), L(0.92, 0.74), L(1.0, 0.88), L(0.96, 1.04), L(0.72, 1.16), L(0.2, 1.08),
                 L(-0.2, 0.72), L(-0.36, 0.22), L(0.0, -0.6)])
    hd = group([head], c.skin, roots=[(neck_pt, c.neck_w * 0.8)])
    paint(lambda m: poly(m, [L(-0.12, 0.05), L(0.1, 0.1), L(0.1, 0.45), L(-0.1, 0.42)]), c.skin[1], hd)  # ear
    paint(lambda m: line(m, L(-0.02, 0.18), L(0.0, 0.32)), c.skin[3], hd)
    paint(lambda m: line(m, L(0.55, 0.32), L(0.72, 0.42)), c.skin[1], hd)             # cheek
    # hairline: from the forehead down to the nape; hair lies on the upper-back side of this line
    (ax_, ay_), (bx_, by_) = _pt(L(0.62, -0.72)), _pt(L(-0.3, 0.55))
    upper = ((xx - ax_) * (by_ - ay_) - (yy - ay_) * (bx_ - ax_)) < 0
    if c.hair_style == 'curly':
        # thick curls: the hair region of the head, grown outwards by a pixel
        hreg = hd & upper
        pad = np.pad(hreg, 1)
        grown = hreg | pad[2:, 1:-1]               # curls add volume on top only
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
        (bx0, by0), (bx1, by1) = _pt(L(-0.2, 0.34)), _pt(L(0.8, 0.5))
        below = ((xx - bx0) * (by1 - by0) - (yy - by0) * (bx1 - bx0)) < 0
        bm = hd & below & (xx >= _pt(L(-0.22, 0))[0])
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
    Frontal poses (fighter_art.front) are drawn by render_front.
    Parts of the same material are merged and shaded as one area (no seams inside an arm, a trouser leg or
    the singlet), and no edges are drawn where a limb grows out of the body (shoulder, hip, knee)."""
    if pose.get('_front'):
        return render_front(pose, c, face)
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
    """One animation frame: pose, duration in video frames, optional hit box - a joint name (box around that
    joint of the skeleton pose) or an explicit box (x0, x1, y0, y1) in game pixels relative to the anchor,
    measured on imported art -, facial expression ('normal', 'hit', 'win'); b_front: the far arm strikes
    across the body and is drawn in front."""
    if b_front:
        pose = dict(pose, _b_front=True)
    box = hit if isinstance(hit, tuple) else (box_at(pose, hit) if hit else None)
    return dict(pose=pose, ticks=ticks, hit=box, face=face)


# ------------------------------------------------------------------ frontal view (win poses)
def front(**joints):
    """A frontal pose: joints with _l / _r (screen left / right): sho, elb, hand, hip, knee, ankle; neck, head."""
    p = dict(joints)
    p['_front'] = True
    return p


def render_front(p, c, face='win'):
    """The fighter seen from the front (win poses). Proportions follow a realistic athletic figure
    (owner's reference): head about 1/6 of the body height, a short thick neck, shoulders about a third of
    the body height wide with round deltoids, a V-shaped torso with chest and belly muscles, strong arms.
    Costume widths for the front view: fr_head (half width, half height), fr_neck, fr_upper, fr_fore,
    fr_hand, fr_thigh, fr_shin, fr_waist (half width at the belt)."""
    canvas = np.zeros((FRAME_H, FRAME_W), np.uint8)
    solid = np.zeros_like(canvas, dtype=bool)
    yy, xx = np.indices(canvas.shape)

    def group(fns, zone):
        m = _mask()
        for fn in fns:
            fn(m)
        a = shade_layer(canvas, m, zone, False, c.rim if zone == c.skin else None)
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

    def lerp(a, b, t):
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    def ell(m, cx, cy, rx, ry):
        x0, y0 = _pt((cx - rx, cy - ry))
        x1, y1 = _pt((cx + rx, cy + ry))
        ImageDraw.Draw(m).ellipse((x0, y0, x1, y1), fill=255)

    sl, sr, hl, hr = p['sho_l'], p['sho_r'], p['hip_l'], p['hip_r']
    mx = (sl[0] + sr[0]) / 2
    top, belt = (sl[1] + sr[1]) / 2, (hl[1] + hr[1]) / 2
    wst = c.fr_waist
    # ---- legs and feet
    for s_ in ('l', 'r'):
        hip, knee, ank = p['hip_' + s_], p['knee_' + s_], p['ankle_' + s_]
        out = -1 if s_ == 'l' else 1
        thigh = lambda m, hip=hip, knee=knee: limb(m, hip, knee, c.fr_thigh[0], c.fr_thigh[1], 1, 0.35)
        if c.loose:
            a2 = lerp(knee, ank, 0.92)
            shin = lambda m, knee=knee, a2=a2: limb(m, knee, a2, c.fr_shin[0], c.fr_shin[1], 0, cap_b=False)
        else:
            shin = lambda m, knee=knee, ank=ank: limb(m, knee, ank, c.fr_shin[0], c.fr_shin[1], 1.5, 0.3,
                                                      cap_b=False)
        foot = lambda m, ank=ank, out=out: poly(m, [(ank[0] - c.foot_w * 0.55, ank[1] - 2),
                                                    (ank[0] + c.foot_w * 0.55, ank[1] - 2),
                                                    (ank[0] + c.foot_w * 0.65 + out, ank[1] + 3),
                                                    (ank[0] - c.foot_w * 0.65 + out, ank[1] + 3)])
        if c.short_thigh:
            group([thigh, shin], c.skin)
        else:
            group([thigh, shin], c.thigh)
            for t0, t1, (a, b), o in ((0.3, 0.85, (hip, knee), 2), (0.15, 0.75, (knee, ank), -2)):   # folds
                q0, q1 = lerp(a, b, t0), lerp(a, b, t1)
                paint(lambda m: line(m, (q0[0] + o, q0[1]), (q1[0] + o * 0.5, q1[1])), c.thigh[1], solid)
        group([foot], c.foot)
        if c.shoes:
            x, y = _pt(ank)
            canvas[int(y) - 1, int(x) - 1:int(x) + 2] = c.eye            # laces
    # ---- torso: trapezius, round deltoids, V shape to the waist; pelvis
    def torso(m):
        tr = getattr(c, 'fr_traps', 2)                         # trapezius: neck to shoulder slope
        poly(m, [(mx - c.fr_neck * 0.5, top - tr), (mx + c.fr_neck * 0.5, top - tr), (sr[0], sr[1] - 1),
                 (sr[0] - 1, sr[1] + 9), (mx + wst + 1, belt - 12), (mx + wst, belt), (mx - wst, belt),
                 (mx - wst - 1, belt - 12), (sl[0] + 1, sl[1] + 9), (sl[0], sl[1] - 1)])
        for sh in (sl, sr):                                       # deltoids
            disc(m, (sh[0], sh[1] + 2), c.fr_upper[0] * 0.55)

    def pelvis(m):
        poly(m, [(mx - wst - 1, belt - 2), (mx + wst + 1, belt - 2), (hr[0] + c.fr_thigh[0] * 0.5, hr[1] + 6),
                 (mx, hr[1] + 9), (hl[0] - c.fr_thigh[0] * 0.5, hl[1] + 6)])

    def neck(m):
        limb(m, (mx, p['neck'][1] - 2), (mx, top - 2), c.fr_neck, c.fr_neck + 2, cap_b=False)

    if c.torso == c.pelvis:
        fns = [torso, pelvis]
        if c.short_thigh:
            fns += [lambda m, s_=s_: limb(m, p['hip_' + s_], lerp(p['hip_' + s_], p['knee_' + s_], 0.5),
                                          c.fr_thigh[0], c.fr_thigh[1] + 1) for s_ in ('l', 'r')]
        group([neck], c.skin)
        t = group(fns, c.torso)
    else:
        t = group([neck, torso], c.skin)
        group([pelvis], c.pelvis)
    if c.bare_torso:                              # pectorals, abdominals, navel
        for sg in (-1, 1):
            q = [(mx + sg * 0.5, top + 3), (mx + sg * 2, top + 9), (mx + sg * 8, top + 9.5), (mx + sg * 12, top + 6)]
            paint(lambda m: ImageDraw.Draw(m).line([_pt(v) for v in q], fill=255), c.torso[1], t)
            paint(lambda m: line(m, (mx + sg * 3, top + 4), (mx + sg * 9, top + 4.5)), c.torso[2], t)
            paint(lambda m: line(m, (mx + sg * (wst - 1), top + 12), (mx + sg * (wst - 3), belt - 3)), c.torso[1], t)
        paint(lambda m: line(m, (mx, top + 10), (mx, belt - 4)), c.torso[1], t)
        for k in range(3):
            yk = top + 13 + k * 4
            paint(lambda m: line(m, (mx - 4, yk), (mx + 4, yk)), c.torso[1], t)
        canvas[int(_pt((0, belt - 4))[1]), int(_pt((mx, 0))[0])] = c.skin[3]
    if c.neckline:                                # singlet: wide straps, deep scoop showing the chest
        tr = getattr(c, 'fr_traps', 2)
        w = abs(sl[0] - mx)
        paint(lambda m: poly(m, [(mx - w + 4, top - tr - 1), (mx + w - 4, top - tr - 1), (mx + w - 4, top + 5),
                                 (mx + w - 7, top + 12), (mx, top + 15), (mx - w + 7, top + 12),
                                 (mx - w + 4, top + 5)]), c.skin[0], t)
        for sh in (sl, sr):                       # bare shoulders and traps outside the straps
            paint(lambda m: disc(m, (sh[0], sh[1] + 2), c.fr_upper[0] * 0.55), c.skin[0], t)
            paint(lambda m: poly(m, [(sh[0], sh[1] - 1), (mx + (sh[0] - mx) * 0.55, top - tr),
                                     (mx + (sh[0] - mx) * 0.75, top - tr + 3)]), c.skin[0], t)
        for sg in (-1, 1):                        # pectorals
            q = [(mx + sg * 0.5, top + 2), (mx + sg * 2, top + 9), (mx + sg * 8, top + 10), (mx + sg * (w - 6), top + 6)]
            paint(lambda m: ImageDraw.Draw(m).line([_pt(v) for v in q], fill=255), c.skin[1], t)
            paint(lambda m: line(m, (mx + sg * 3, top + 3), (mx + sg * 8, top + 3.5)), c.skin[2], t)
    for k, col in enumerate(c.stripes):           # stripes down both sides and the thighs
        for sg, (sh, hp) in ((-1, (sl, hl)), (1, (sr, hr))):
            o = -(k + 1) * sg
            paint(lambda m: line(m, (sh[0] + o - sg * 1, sh[1] + 9), (mx + sg * (wst - k - 1), belt + 4)), col, t)
            kn = lerp(hp, p['knee_' + ('l' if sg < 0 else 'r')], 0.5)
            ox = sg * (c.fr_thigh[0] / 2 - k - 1)
            paint(lambda m: line(m, (hp[0] + ox, hp[1] + 4), (kn[0] + ox, kn[1])), col, solid)
    if c.belt is not None:                        # cord belt, knot at the side, the ends hang down the thigh
        b = paint(lambda m: line(m, (mx - wst - 1, belt - 1), (mx + wst + 1, belt - 1), 3), c.belt)
        canvas[b & ((xx // 2) % 2 == 0)] = c.belt2
        k = (mx + wst - 1, belt)
        paint(lambda m: disc(m, k, 1.5), c.belt2)
        for dx, ln2 in ((0, 16), (2, 13)):
            solid |= paint(lambda m: line(m, k, (k[0] + dx, k[1] + ln2), 2), c.belt)
            paint(lambda m: line(m, (k[0] + dx, k[1] + ln2 - 3), (k[0] + dx, k[1] + ln2)), c.belt2)
    # ---- arms
    for s_ in ('l', 'r'):
        sho, elb, hand = p['sho_' + s_], p['elb_' + s_], p['hand_' + s_]
        sh2 = (sho[0], sho[1] + 2)
        a = group([lambda m: limb(m, sh2, elb, c.fr_upper[0], c.fr_upper[1], c.fr_upper[2], 0.45),
                   lambda m: limb(m, elb, hand, c.fr_fore[0], c.fr_fore[1], c.fr_fore[2], 0.3),
                   lambda m: disc(m, hand, c.fr_hand)], c.skin)
        hx2, hy2 = _pt(hand)
        canvas[a & (np.abs(yy - hy2) < 0.6) & ((xx - hx2) ** 2 < c.fr_hand ** 2)] = c.skin[1]   # knuckles
        if abs(hand[1] - elb[1]) > 8 and hand[1] < elb[1]:      # raised forearm: crease at the inner elbow
            inner = 1 if elb[0] < mx else -1
            e2 = lerp(elb, hand, 0.35)
            paint(lambda m: line(m, (elb[0] + inner * 3, elb[1] - 1), (e2[0] + inner * 2, e2[1])), c.skin[1], a)
    # ---- head from the front
    hx, hy = p['head']
    rx, ry = c.fr_head

    def head(m):
        ell(m, hx, hy - ry * 0.1, rx, ry * 0.9)
        poly(m, [(hx - rx * 0.95, hy), (hx + rx * 0.95, hy), (hx + rx * 0.55, hy + ry * 0.92),
                 (hx, hy + ry), (hx - rx * 0.55, hy + ry * 0.92)])          # cheeks, jaw, chin
        for sg in (-1, 1):
            ell(m, hx + sg * rx * 1.02, hy + ry * 0.05, 1.3, 2)             # ears
    hd = group([head], c.skin)
    cx, cy = _pt((hx, hy))
    if c.hair_style == 'curly':
        # short, close-lying braided hair: a cap over the top of the head with braid lines
        cap = hd & (yy < cy - ry * 0.38) | (hd & (yy < cy - ry * 0.05) & (np.abs(xx - cx) > rx * 0.8))
        pad = np.pad(cap, 1)
        cap = cap | (pad[2:, 1:-1] & (yy < cy - ry * 0.5))
        canvas[cap] = c.hair[0]
        canvas[cap & ((xx - int(cx)) % 2 == 0) & (yy % 3 != 0)] = c.hair[1]
        canvas[cap & ~np.roll(cap, 1, axis=0)] = c.hair[2]
        solid |= cap
    else:
        # crew cut from the front: short blond hair on top down to the forehead, shaved sides with stubble
        topband = hd & (yy < cy - ry * 0.55) & (np.abs(xx - cx) < rx * 0.85)
        canvas[topband] = c.hair[0]
        canvas[topband & (((xx * 3 + yy * 5) % 4) == 0)] = c.hair[1]
        canvas[topband & ~np.roll(hd, 1, axis=0)] = c.hair[2]
        sides = hd & (yy < cy) & (np.abs(xx - cx) >= rx * 0.85)
        canvas[sides & (((xx * 3 + yy * 5) % 5) == 0)] = c.hair[1]            # shaved sides
    if c.beard:
        bm = hd & (yy > cy + ry * 0.3) & (np.abs(xx - cx) < rx * 0.95)
        bm &= ~((np.abs(xx - cx) < 2.5) & (yy > cy + ry * 0.4) & (yy < cy + ry * 0.75))
        canvas[bm] = c.hair[0]
        canvas[bm & (((xx * 3 + yy * 5) % 7) == 2)] = c.hair[1]
    ey = int(round(cy - ry * 0.12))
    for sg in (-1, 1):
        ex = int(round(cx + sg * rx * 0.42))
        canvas[ey, ex - 1:ex + 1] = c.eye
        canvas[ey, ex + (0 if sg < 0 else -1)] = c.pupil
        canvas[ey - 2, ex - 2:ex + 1] = c.hair[1] if c.hair_style != 'curly' else c.hair[0]    # brows
    canvas[ey + 1:ey + 4, int(round(cx))] = c.skin[1]                                          # nose
    canvas[ey + 3, int(round(cx)) - 1:int(round(cx)) + 2] = c.skin[1]
    my = int(round(cy + ry * 0.55))
    mxp = int(round(cx))
    if face == 'win':                                       # broad smile with teeth
        canvas[my, mxp - 2:mxp + 3] = c.mouth
        canvas[my + 1, mxp - 2:mxp + 3] = c.eye
        canvas[my + 2, mxp - 1:mxp + 2] = c.mouth
    else:
        canvas[my, mxp - 1:mxp + 2] = c.mouth
    # ---- outline
    pad = np.pad(solid, 1)
    nb = pad[:-2, 1:-1] | pad[2:, 1:-1] | pad[1:-1, :-2] | pad[1:-1, 2:]
    canvas[nb & ~solid] = OUTLINE
    return canvas

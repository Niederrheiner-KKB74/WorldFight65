#!/usr/bin/env python3
"""Skeleton renderer for WorldFight65 fighters (Claude's art pipeline).

A pose is a dict of joint positions in pixels relative to the fighter's anchor (the point on the floor
between the feet; x grows forward, y grows downwards, so the head has y about -86). A costume says which
colours and widths the body parts have. render() draws the pose into a FRAME_W x FRAME_H canvas of
palette indices (0 = transparent) with a dark outline and simple cel shading (light from the front-top).

Joints: head, neck, sho_f, sho_b (shoulders front/back), elb_f, elb_b, hand_f, hand_b, hip_f, hip_b,
knee_f, knee_b, ankle_f, ankle_b, toe_f, toe_b.  "_f" is the limb nearer to the viewer.
"""
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


def shade_layer(canvas, m, base, shade, light=None):  # noqa: C901
    """Paint mask m with base; the edge facing away from the light (back and bottom) with shade,
    the edge facing the light (front and top) with light."""
    a = np.array(m) > 0
    canvas[a] = base
    # shadow: pixels whose neighbour 2 px towards the light-opposite side (back = -x, bottom = +y) is outside
    sh = a & ~(np.roll(a, 2, axis=1) & np.roll(a, -2, axis=0))
    canvas[sh] = shade
    if light is not None:
        li = a & ~np.roll(a, -1, axis=1) & np.roll(a, 1, axis=1)
        li |= a & ~np.roll(a, 1, axis=0)
        canvas[li & ~sh] = light
    return a


class Costume:
    """Colours are palette indices. Every body zone has a colour set (base, shade, light, dark);
    limbs on the far side are drawn with (shade, dark). Widths in pixels.
    Zones: skin (head, neck, arms, hands), torso, pelvis, thigh, shin, foot.
    Optional: belt / belt2 (striped cord belt), neckline (skin triangle at the neck of a singlet),
    stripe (colour of a stripe down the side of the torso and the thighs), beard."""
    def __init__(self, **kw):
        self.belt = None
        self.neckline = False
        self.stripe = None
        self.beard = False
        self.__dict__.update(kw)


def render(pose, c):
    """Return (FRAME_H, FRAME_W) uint8 array of palette indices."""
    canvas = np.zeros((FRAME_H, FRAME_W), np.uint8)
    solid = np.zeros_like(canvas, dtype=bool)

    def layer(draw_fn, zone, back=False):
        base, shade, light, dark = zone
        m = _mask()
        draw_fn(m)
        a = shade_layer(canvas, m, shade, dark) if back else shade_layer(canvas, m, base, shade, light)
        solid[:] |= a
        return a

    p = pose

    def arm(side, part):
        sho, elb, hand = p['sho_' + side], p['elb_' + side], p['hand_' + side]
        if part == 'upper':
            return lambda m: capsule(m, sho, elb, c.upper_w)
        if part == 'fore':
            return lambda m: capsule(m, elb, hand, c.fore_w)
        return lambda m: disc(m, hand, c.hand_r)

    def thigh(side):
        return lambda m: capsule(m, p['hip_' + side], p['knee_' + side], c.thigh_w)

    def shin(side):
        return lambda m: capsule(m, p['knee_' + side], p['ankle_' + side], c.shin_w)

    def foot(side):
        return lambda m: capsule(m, p['ankle_' + side], p['toe_' + side], c.foot_w)

    def stripe_on(a):
        """a stripe along the mask's front edge"""
        if c.stripe is None:
            return
        edge = a & ~np.roll(a, -2, axis=1)
        canvas[edge & np.roll(a, 1, axis=1)] = c.stripe

    # ---- far limbs
    for part in ('upper', 'fore', 'hand'):
        layer(arm('b', part), c.skin, back=True)
    layer(foot('b'), c.foot, back=True)
    layer(shin('b'), c.shin, back=True)
    layer(thigh('b'), c.thigh, back=True)
    # ---- torso
    def torso(m):
        sf, sb, hf, hb = p['sho_f'], p['sho_b'], p['hip_f'], p['hip_b']
        waist_f = ((sf[0] + hf[0]) / 2 + 1, (sf[1] + hf[1]) / 2)
        waist_b = ((sb[0] + hb[0]) / 2 - 1, (sb[1] + hb[1]) / 2)
        poly(m, [(sb[0] - 2, sb[1] - 1), (sf[0] + 2, sf[1] - 1), waist_f, (hf[0] + 1, hf[1]),
                 (hb[0] - 1, hb[1]), waist_b])
    def neck(m):
        sf, sb = p['sho_f'], p['sho_b']
        capsule(m, p['neck'], ((sf[0] + sb[0]) / 2, (sf[1] + sb[1]) / 2 + 2), c.neck_w)
    layer(neck, c.skin)
    t = layer(torso, c.torso)
    stripe_on(t)
    sf, sb = p['sho_f'], p['sho_b']
    mid = ((sf[0] + sb[0]) / 2, (sf[1] + sb[1]) / 2)
    if c.neckline:
        m = _mask()
        poly(m, [(mid[0] - 3, mid[1] - 1), (mid[0] + 5, mid[1] - 1), (mid[0] + 2, mid[1] + 6)])
        canvas[(np.array(m) > 0) & t] = c.skin[0]
    else:
        # chest/belly line for a muscular look
        m = _mask(); d = ImageDraw.Draw(m)
        hipm = ((p['hip_f'][0] + p['hip_b'][0]) / 2 + 2, (p['hip_f'][1] + p['hip_b'][1]) / 2)
        d.line((_pt((mid[0] + 2, mid[1] + 6)), _pt((hipm[0], hipm[1] - 3))), fill=255)
        canvas[(np.array(m) > 0) & t] = c.torso[1]
    # ---- pelvis, belt
    hf, hb = p['hip_f'], p['hip_b']
    layer(lambda m: poly(m, [(hb[0] - 3, hb[1] - 4), (hf[0] + 3, hf[1] - 4), (hf[0] + 4, hf[1] + 4),
                             (hb[0] - 4, hb[1] + 4)]), c.pelvis)
    if c.belt is not None:
        m = _mask()
        ImageDraw.Draw(m).line((_pt((hb[0] - 3, hb[1] - 3)), _pt((hf[0] + 3, hf[1] - 3))), fill=255, width=3)
        belt = np.array(m) > 0
        canvas[belt] = c.belt
        canvas[belt & ((np.indices(canvas.shape)[1] // 2) % 2 == 0)] = c.belt2
        m = _mask()
        capsule(m, (hf[0] + 1, hf[1] - 3), (hf[0] + 3, hf[1] + 9), 2)    # knot with hanging ends
        canvas[np.array(m) > 0] = c.belt2
        solid |= np.array(m) > 0
    # ---- near leg
    layer(foot('f'), c.foot)
    layer(shin('f'), c.shin)
    stripe_on(layer(thigh('f'), c.thigh))
    # ---- head
    def head(m):
        disc(m, p['head'], c.head_r)
        hx, hy = p['head']
        poly(m, [(hx - 2, hy + 2), (hx + c.head_r, hy + 1), (hx + c.head_r - 1, hy + c.head_r + 1),
                 (hx + 1, hy + c.head_r + 2)])          # jaw towards the front
    layer(head, c.skin)
    hx, hy = p['head']
    m = _mask()
    ImageDraw.Draw(m).pieslice((_pt((hx - c.head_r - 1, hy - c.head_r - 2)) + _pt((hx + c.head_r + 1, hy + c.head_r))),
                               170, 350, fill=255)
    hair = np.array(m) > 0
    canvas[hair] = c.hair
    solid |= hair
    if c.beard:
        m = _mask()
        poly(m, [(hx - 1, hy + 3), (hx + c.head_r, hy + 3), (hx + c.head_r - 1, hy + c.head_r + 2),
                 (hx + 1, hy + c.head_r + 3)])
        b = (np.array(m) > 0) & solid
        canvas[b] = c.hair
    ex, ey = _pt((hx + c.head_r - 3, hy))
    canvas[int(ey), int(ex)] = c.eye
    if not c.beard:
        canvas[int(ey) + 3, int(ex) - 1:int(ex) + 1] = c.skin[1]     # mouth
    # ---- near arm
    for part in ('upper', 'fore', 'hand'):
        layer(arm('f', part), c.skin)
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
    return {k: (a[k][0] + (b[k][0] - a[k][0]) * t, a[k][1] + (b[k][1] - a[k][1]) * t) for k in a}


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


def frame(pose, ticks, hit=None):
    """One animation frame: pose, duration in video frames, optional hit-box joint."""
    return dict(pose=pose, ticks=ticks, hit=box_at(pose, hit) if hit else None)

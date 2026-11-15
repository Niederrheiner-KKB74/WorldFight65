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

FRAME_W = 96          # canvas; trimmed to 16-px columns later
FRAME_H = 104         # 13 glyph rows
ANCHOR = (48, 101)    # canvas position of the anchor (floor point)

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


def shade_layer(canvas, m, base, shade, light=None):
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
    """Colours are palette indices; widths in pixels."""
    def __init__(self, **kw):
        self.__dict__.update(kw)


def render(pose, c):
    """Return (FRAME_H, FRAME_W) uint8 array of palette indices."""
    canvas = np.zeros((FRAME_H, FRAME_W), np.uint8)
    solid = np.zeros_like(canvas, dtype=bool)

    def layer(draw_fn, base, shade, light=None):
        m = _mask()
        draw_fn(m)
        a = shade_layer(canvas, m, base, shade, light)
        solid[:] |= a

    p = pose
    # ---- back limbs (darker)
    def leg(side, m, trouser):
        hip, knee, ank, toe = p['hip_' + side], p['knee_' + side], p['ankle_' + side], p['toe_' + side]
        if trouser:
            capsule(m, hip, knee, c.thigh_w)
            capsule(m, knee, ank, c.shin_w)
        else:
            capsule(m, ank, toe, c.foot_w)
    def arm(side, m, part):
        sho, elb, hand = p['sho_' + side], p['elb_' + side], p['hand_' + side]
        if part == 'upper':
            capsule(m, sho, elb, c.upper_w)
        elif part == 'fore':
            capsule(m, elb, hand, c.fore_w)
        else:
            disc(m, hand, c.hand_r)

    layer(lambda m: arm('b', m, 'upper'), c.skin_d, c.skin_dd)
    layer(lambda m: arm('b', m, 'fore'), c.skin_d, c.skin_dd)
    layer(lambda m: arm('b', m, 'hand'), c.skin_d, c.skin_dd)
    layer(lambda m: leg('b', m, False), c.skin_d, c.skin_dd)
    layer(lambda m: leg('b', m, True), c.pants_d, c.pants_dd)
    # ---- torso
    def torso(m):
        sf, sb, hf, hb = p['sho_f'], p['sho_b'], p['hip_f'], p['hip_b']
        waist_f = ((sf[0] + hf[0]) / 2 + 1, (sf[1] + hf[1]) / 2)
        waist_b = ((sb[0] + hb[0]) / 2 - 1, (sb[1] + hb[1]) / 2)
        poly(m, [(sb[0] - 2, sb[1] - 1), (sf[0] + 2, sf[1] - 1), waist_f, (hf[0] + 1, hf[1]),
                 (hb[0] - 1, hb[1]), waist_b])
        capsule(m, p['neck'], ((sf[0] + sb[0]) / 2, (sf[1] + sb[1]) / 2 + 2), c.neck_w)
    layer(torso, c.skin, c.skin_d, c.skin_l)
    # chest/belly lines for a muscular look
    m = _mask(); d = ImageDraw.Draw(m)
    mid = ((p['sho_f'][0] + p['sho_b'][0]) / 2 + 2, (p['sho_f'][1] + p['sho_b'][1]) / 2)
    hipm = ((p['hip_f'][0] + p['hip_b'][0]) / 2 + 2, (p['hip_f'][1] + p['hip_b'][1]) / 2)
    d.line((_pt((mid[0], mid[1] + 6)), _pt((hipm[0], hipm[1] - 3))), fill=255)
    canvas[(np.array(m) > 0) & solid] = c.skin_d
    # ---- pelvis with the belt (trousers)
    def pelvis(m):
        hf, hb = p['hip_f'], p['hip_b']
        poly(m, [(hb[0] - 3, hb[1] - 4), (hf[0] + 3, hf[1] - 4), (hf[0] + 4, hf[1] + 4), (hb[0] - 4, hb[1] + 4)])
    layer(pelvis, c.pants, c.pants_d, c.pants_l)
    m = _mask()
    hf, hb = p['hip_f'], p['hip_b']
    ImageDraw.Draw(m).line((_pt((hb[0] - 3, hb[1] - 3)), _pt((hf[0] + 3, hf[1] - 3))), fill=255, width=3)
    belt = np.array(m) > 0
    canvas[belt] = c.belt
    stripes = belt & ((np.indices(canvas.shape)[1] // 2) % 2 == 0)
    canvas[stripes] = c.belt2
    # belt knot with hanging ends at the front hip
    m = _mask()
    capsule(m, (hf[0] + 1, hf[1] - 3), (hf[0] + 3, hf[1] + 9), 2)
    canvas[np.array(m) > 0] = c.belt2
    solid |= np.array(m) > 0
    # ---- front leg
    layer(lambda m: leg('f', m, True), c.pants, c.pants_d, c.pants_l)
    layer(lambda m: leg('f', m, False), c.skin, c.skin_d)
    # ---- head
    def head(m):
        disc(m, p['head'], c.head_r)
        hx, hy = p['head']
        poly(m, [(hx - 2, hy + 2), (hx + c.head_r, hy + 1), (hx + c.head_r - 1, hy + c.head_r + 1),
                 (hx + 1, hy + c.head_r + 2)])          # jaw towards the front
    layer(head, c.skin, c.skin_d, c.skin_l)
    hx, hy = p['head']
    m = _mask()
    ImageDraw.Draw(m).pieslice((_pt((hx - c.head_r - 1, hy - c.head_r - 2)) + _pt((hx + c.head_r + 1, hy + c.head_r))),
                               170, 350, fill=255)
    hair = (np.array(m) > 0)
    canvas[hair] = c.hair
    solid |= hair
    ex, ey = _pt((hx + c.head_r - 3, hy))
    canvas[int(ey), int(ex)] = c.eye
    canvas[int(ey) + 3, int(ex) - 1:int(ex) + 1] = c.skin_d     # mouth
    # ---- front arm
    layer(lambda m: arm('f', m, 'upper'), c.skin, c.skin_d, c.skin_l)
    layer(lambda m: arm('f', m, 'fore'), c.skin, c.skin_d, c.skin_l)
    layer(lambda m: arm('f', m, 'hand'), c.skin, c.skin_d, c.skin_l)

    # ---- outline around the whole silhouette
    s = solid
    nb = np.zeros_like(s)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nb |= np.roll(np.roll(s, dy, axis=0), dx, axis=1)
    canvas[nb & ~s] = OUTLINE
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

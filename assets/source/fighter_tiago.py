#!/usr/bin/env python3
"""Tiago (Brazil, capoeira) - drawn by Claude for WorldFight65 with tools/fighter_art.py.

Look: bare torso, white capoeira trousers (abada) with a green-and-yellow cord belt (cordao), bare feet,
short black hair. Stage 1 frames: idle (ginga-like sway, 4 frames) and walk (6 frames).
frames() returns {animation name: [frames]}; palette is the fighter's 16-colour bank (index 0 transparent).
Run it directly to write a preview sheet.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import fighter_art as fa          # noqa: E402

PALETTE = [
    (0, 0, 0),          # 0 transparent
    (24, 16, 20),       # 1 outline
    (70, 40, 28),       # 2 skin, darkest
    (112, 68, 44),      # 3 skin, dark
    (152, 98, 64),      # 4 skin
    (192, 134, 92),     # 5 skin, light
    (32, 24, 28),       # 6 hair, eyes
    (128, 130, 150),    # 7 trousers, darkest
    (176, 178, 194),    # 8 trousers, dark
    (228, 228, 222),    # 9 trousers
    (255, 255, 255),    # 10 trousers, light
    (44, 156, 72),      # 11 belt green
    (244, 206, 40),     # 12 belt yellow
    (200, 40, 40),      # 13 spare (hit flash)
    (255, 200, 120),    # 14 spare
    (255, 255, 255),    # 15 spare
]

COSTUME = fa.Costume(
    skin=4, skin_d=3, skin_dd=2, skin_l=5, hair=6, eye=6,
    pants=9, pants_d=8, pants_dd=7, pants_l=10, belt=11, belt2=12,
    thigh_w=10, shin_w=9, foot_w=4, upper_w=6, fore_w=5, hand_r=3, neck_w=5, head_r=6,
)

THIGH, SHIN = 23, 22


def ik(hip, ankle, l1, l2, forward=1):
    """Knee position for a two-bone leg; the knee bends towards +x * forward."""
    dx, dy = ankle[0] - hip[0], ankle[1] - hip[1]
    d = min(math.hypot(dx, dy), l1 + l2 - 0.01)
    a = math.atan2(dy, dx)
    cosb = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    b = math.acos(max(-1, min(1, cosb)))
    ang = a - b * forward
    return (hip[0] + l1 * math.cos(ang), hip[1] + l1 * math.sin(ang))


def body(bob=0.0, lean=0.0, guard=0.0, ankle_f=(15, -3), ankle_b=(-14, -3), lift_f=0.0, lift_b=0.0):
    hy = -45 + bob
    hip_f, hip_b = (3 + lean * 0.3, hy), (-3 + lean * 0.3, hy)
    af = (ankle_f[0], ankle_f[1] - lift_f)
    ab = (ankle_b[0], ankle_b[1] - lift_b)
    sx = lean
    p = {
        'hip_f': hip_f, 'hip_b': hip_b,
        'ankle_f': af, 'ankle_b': ab,
        'toe_f': (af[0] + 6, af[1] + 2), 'toe_b': (ab[0] + 6, ab[1] + 2),
        'knee_f': ik(hip_f, af, THIGH, SHIN), 'knee_b': ik(hip_b, ab, THIGH, SHIN),
        'sho_f': (5 + sx, -72 + bob), 'sho_b': (-5 + sx, -73 + bob),
        'neck': (2 + sx, -78 + bob), 'head': (4 + sx, -86 + bob),
        # guard: front hand in front of the face, back hand low in front of the body
        'elb_f': (15 + sx, -63 + bob + guard), 'hand_f': (15 + sx, -77 + bob + guard * 1.5),
        'elb_b': (-8 + sx, -58 + bob - guard), 'hand_b': (2 + sx, -54 + bob - guard),
    }
    return p


def idle():
    out = []
    for i in range(4):
        t = i / 4 * 2 * math.pi
        out.append(fa.render(body(bob=1.5 + 1.5 * math.sin(t), lean=math.sin(t), guard=1.5 * math.sin(t)),
                             COSTUME))
    return out


def walk():
    out = []
    for i in range(6):
        ph = i / 6 * 2 * math.pi
        sw = math.cos(ph)
        af = (1 + 14 * sw, -3)
        ab = (1 - 14 * sw, -3)
        lift_f = 6 * max(0.0, math.sin(ph))
        lift_b = 6 * max(0.0, -math.sin(ph))
        out.append(fa.render(body(bob=1 + abs(math.sin(ph)) * -2 + 2, ankle_f=af, ankle_b=ab,
                                  lift_f=lift_f, lift_b=lift_b, guard=math.sin(ph)), COSTUME))
    return out


def frames():
    return {'idle': idle(), 'walk': walk()}


if __name__ == '__main__':
    f = frames()
    out = Path(sys.argv[1] if len(sys.argv) > 1 else 'tiago.png')
    fa.sheet(f['idle'] + f['walk'], PALETTE, scale=3, cols=5).save(out)
    print(out)

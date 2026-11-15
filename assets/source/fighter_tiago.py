#!/usr/bin/env python3
"""Tiago (Brazil, capoeira) - drawn by Claude for WorldFight65 with tools/fighter_art.py.

Look: bare torso, white capoeira trousers (abada) with a green-and-yellow cord belt (cordao), bare feet,
short black hair. Quick and agile; long kicks.
anims() returns {animation: [frame dicts]} (fighter_art.frame: pose, ticks, hit box);
MOVES gives damage, hitstun and pushback of the four attacks; STATS the fighter's values.
Run it directly to write a preview sheet.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import fighter_art as fa          # noqa: E402
from fighter_art import build, frame   # noqa: E402

NAME = 'TIAGO'
COUNTRY = 'BRAZIL'
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
SKIN, PANTS = (4, 3, 5, 2), (9, 8, 10, 7)
COSTUME = fa.Costume(
    skin=SKIN, torso=SKIN, pelvis=PANTS, thigh=PANTS, shin=PANTS, foot=SKIN,
    hair=6, eye=6, belt=11, belt2=12,
    thigh_w=10, shin_w=9, foot_w=4, upper_w=6, fore_w=5, hand_r=3, neck_w=5, head_r=6,
)
# health = width of the energy bar in pixels; speeds in pixels per frame; hurt box half width and top
STATS = dict(health=128, walk_fwd=2, walk_back=1, hurt_w=13, hurt_top=-92)
# damage, hitstun (frames), pushback (pixels, 2 per frame)
MOVES = dict(lp=(6, 12, 6), hp=(14, 18, 12), lk=(8, 14, 8), hk=(16, 20, 14))


def stance(bob=0.0, sway=0.0, guard=0.0, **kw):
    a = dict(hip=(sway * 0.3, -45 + bob), lean=4 + sway,
             hand_f=(15 + sway, -77 + bob + guard * 1.5), hand_b=(2 + sway, -54 + bob - guard))
    a.update(kw)
    return build(**a)


def idle():
    out = []
    for i in range(4):
        t = i / 4 * 2 * math.pi
        out.append(frame(stance(bob=1.5 + 1.5 * math.sin(t), sway=math.sin(t), guard=1.5 * math.sin(t)), 8))
    return out


def walk():
    out = []
    for i in range(6):
        ph = i / 6 * 2 * math.pi
        sw = math.cos(ph)
        af = (1 + 14 * sw, -3 - 6 * max(0.0, math.sin(ph)))
        ab = (1 - 14 * sw, -3 - 6 * max(0.0, -math.sin(ph)))
        out.append(frame(stance(bob=2 - 2 * abs(math.sin(ph)), guard=math.sin(ph), ankle_f=af, ankle_b=ab), 4))
    return out


def lp():
    # quick open-hand jab
    return [frame(stance(hand_f=(10, -74)), 3),
            frame(stance(lean=10, hand_f=(32, -73)), 4, 'hand_f'),
            frame(stance(lean=6, hand_f=(22, -75)), 5)]


def hp():
    # strong strike with the rear hand, stepping in
    return [frame(stance(lean=-6, hand_b=(-12, -70)), 4),
            frame(stance(lean=14, hip=(3, -44), ankle_f=(20, -3), hand_b=(34, -70), hand_f=(8, -66)), 5, 'hand_b'),
            frame(stance(lean=10, hip=(2, -44), ankle_f=(18, -3), hand_b=(22, -66)), 5),
            frame(stance(lean=6), 4)]


def lk():
    # ponteira: fast snap kick to the body
    return [frame(stance(lean=-4, ankle_f=(12, -30), toe_f=(17, -28)), 3),
            frame(stance(lean=-10, ankle_f=(38, -44), toe_f=(44, -47)), 4, 'toe_f'),
            frame(stance(lean=-4, ankle_f=(14, -28), toe_f=(19, -26)), 5)]


def hk():
    # martelo: high roundhouse kick
    return [frame(stance(lean=-10, ankle_f=(14, -40), toe_f=(19, -38)), 4),
            frame(stance(lean=-22, hip=(-2, -45), ankle_f=(40, -66), toe_f=(46, -70)), 5, 'toe_f'),
            frame(stance(lean=-14, ankle_f=(22, -46), toe_f=(27, -45)), 5),
            frame(stance(lean=-4, ankle_f=(12, -20), toe_f=(18, -19)), 4)]


def hit():
    return [frame(stance(lean=-14, head=(-2, 1), hand_f=(10, -62), hand_b=(-8, -58)), 4),
            frame(stance(lean=-20, hip=(-2, -44), head=(-3, 2), hand_f=(6, -58), hand_b=(-12, -56)), 4)]


def anims():
    return dict(idle=idle(), walk=walk(), lp=lp(), hp=hp(), lk=lk(), hk=hk(), hit=hit())


if __name__ == '__main__':
    a = anims()
    out = Path(sys.argv[1] if len(sys.argv) > 1 else 'tiago.png')
    frames = [fa.render(f['pose'], COSTUME) for n in a for f in a[n]]
    fa.sheet(frames, PALETTE, scale=2, cols=8).save(out)
    print(out)

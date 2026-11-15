#!/usr/bin/env python3
"""Konrad (Germany, wrestling) - drawn by Claude for WorldFight65 with tools/fighter_art.py.

Look: heavy build, black wrestling singlet with a red stripe, red wrestling shoes, short blond hair and a
blond beard. Slower than Tiago, but his attacks hit harder; low wrestling stance with open hands.
Same interface as fighter_tiago.py.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import fighter_art as fa          # noqa: E402
from fighter_art import build, frame   # noqa: E402

NAME = 'KONRAD'
COUNTRY = 'GERMANY'
PALETTE = [
    (0, 0, 0),          # 0 transparent
    (20, 16, 18),       # 1 outline
    (150, 96, 76),      # 2 skin, darkest
    (196, 134, 108),    # 3 skin, dark
    (230, 172, 140),    # 4 skin
    (250, 206, 176),    # 5 skin, light
    (226, 186, 92),     # 6 hair, beard
    (14, 14, 18),       # 7 singlet, darkest
    (30, 30, 38),       # 8 singlet, dark
    (52, 52, 64),       # 9 singlet
    (88, 88, 104),      # 10 singlet, light
    (204, 32, 36),      # 11 red (stripe, shoes)
    (130, 18, 22),      # 12 red, dark
    (255, 90, 80),      # 13 red, light
    (60, 50, 40),       # 14 eyes
    (255, 255, 255),    # 15 spare
]
SKIN, SINGLET, SHOES = (4, 3, 5, 2), (9, 8, 10, 7), (11, 12, 13, 12)
COSTUME = fa.Costume(
    skin=SKIN, torso=SINGLET, pelvis=SINGLET, thigh=SINGLET, shin=SKIN, foot=SHOES,
    hair=6, eye=14, neckline=True, stripe=11, beard=True,
    thigh_w=13, shin_w=11, foot_w=7, upper_w=9, fore_w=8, hand_r=4, neck_w=8, head_r=7,
)
BODY = dict(thigh=22, shin=21, upper=13, fore=13, torso=27, shoulder=8, hips=5)
STATS = dict(health=128, walk_fwd=1, walk_back=1, hurt_w=15, hurt_top=-90)
# damage, hitstun (frames), pushback (pixels, 2 per frame)
MOVES = dict(lp=(7, 12, 6), hp=(16, 20, 14), lk=(9, 14, 8), hk=(18, 22, 12))


def stance(bob=0.0, **kw):
    a = dict(hip=(0, -42 + bob), lean=16, ankle_f=(17, -3), ankle_b=(-16, -3),
             hand_f=(24, -64 + bob), hand_b=(15, -58 + bob), body=BODY)
    a.update(kw)
    return build(**a)


def idle():
    return [frame(stance(bob=1.2 + 1.2 * math.sin(i / 4 * 2 * math.pi)), 9) for i in range(4)]


def walk():
    out = []
    for i in range(6):
        ph = i / 6 * 2 * math.pi
        sw = math.cos(ph)
        af = (3 + 13 * sw, -3 - 4 * max(0.0, math.sin(ph)))
        ab = (-2 - 13 * sw, -3 - 4 * max(0.0, -math.sin(ph)))
        out.append(frame(stance(bob=1.5 - 1.5 * abs(math.sin(ph)), ankle_f=af, ankle_b=ab), 5))
    return out


def lp():
    # straight jab
    return [frame(stance(hand_f=(16, -66)), 3),
            frame(stance(lean=20, hand_f=(36, -68)), 4, 'hand_f'),
            frame(stance(lean=18, hand_f=(28, -66)), 6)]


def hp():
    # forearm smash from above
    return [frame(stance(lean=4, hand_f=(10, -84)), 5),
            frame(stance(lean=26, hip=(3, -41), ankle_f=(20, -3), hand_f=(36, -60)), 5, 'hand_f'),
            frame(stance(lean=22, hip=(2, -41), hand_f=(30, -54)), 6),
            frame(stance(lean=18), 4)]


def lk():
    # low stomp kick
    return [frame(stance(lean=12, ankle_f=(14, -22), toe_f=(19, -20)), 4),
            frame(stance(lean=8, ankle_f=(36, -14), toe_f=(40, -8)), 4, 'ankle_f'),
            frame(stance(lean=12, ankle_f=(22, -10), toe_f=(28, -8)), 6)]


def hk():
    # knee strike
    return [frame(stance(lean=8, ankle_f=(8, -18), toe_f=(13, -16), hand_f=(20, -70), hand_b=(14, -68)), 5),
            frame(stance(lean=4, hip=(4, -44), ankle_f=(14, -34), toe_f=(18, -30),
                         hand_f=(26, -74), hand_b=(20, -72)), 5, 'knee_f'),
            frame(stance(lean=10, ankle_f=(12, -18), toe_f=(17, -16)), 6),
            frame(stance(lean=14), 4)]


def hit():
    return [frame(stance(lean=4, head=(-2, 1), hand_f=(14, -60), hand_b=(4, -56)), 4),
            frame(stance(lean=-4, hip=(-2, -41), head=(-3, 2), hand_f=(10, -56), hand_b=(-2, -54)), 4)]


def anims():
    return dict(idle=idle(), walk=walk(), lp=lp(), hp=hp(), lk=lk(), hk=hk(), hit=hit())


if __name__ == '__main__':
    a = anims()
    out = Path(sys.argv[1] if len(sys.argv) > 1 else 'konrad.png')
    frames = [fa.render(f['pose'], COSTUME) for n in a for f in a[n]]
    fa.sheet(frames, PALETTE, scale=2, cols=8).save(out)
    print(out)

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
    (22, 16, 20),       # 1 outline
    (150, 92, 72),      # 2 skin, darkest
    (196, 132, 104),    # 3 skin, dark
    (232, 172, 138),    # 4 skin
    (252, 210, 178),    # 5 skin, light
    (232, 190, 92),     # 6 hair, beard
    (170, 124, 52),     # 7 hair, beard, dark
    (34, 34, 44),       # 8 singlet, dark
    (56, 56, 70),       # 9 singlet
    (96, 96, 116),      # 10 singlet, light
    (210, 30, 34),      # 11 red (stripe, shoes)
    (250, 200, 30),     # 12 gold (stripe)
    (255, 158, 84),     # 13 rim light (sunset)
    (240, 238, 232),    # 14 eye white, laces
    (120, 20, 26),      # 15 dark red (shoe shadow, mouth)
]
SKIN, SINGLET, SHOES = (4, 3, 5, 2), (9, 8, 10, 1), (11, 15, 13, 15)
COSTUME = fa.Costume(
    skin=SKIN, torso=SINGLET, pelvis=SINGLET, thigh=SINGLET, shin=SKIN, foot=SHOES, rim=13,
    hair=(6, 7, 5), hair_style='crew', beard=True, eye=14, pupil=1, mouth=15,
    neckline=True, stripes=(11, 12), short_thigh=True, shoes=True,
    neck_w=8, w_upper=(9, 7, 2.5), w_fore=(8, 6, 1.5), w_thigh=(13, 11, 1.5), w_shin=(11, 8, 1.5), hand_r=4,
    foot_w=7, head_r=7, chest=11,
)
BODY = dict(thigh=22, shin=21, upper=13, fore=13, torso=27, shoulder=8, hips=5)
STATS = dict(health=128, walk_fwd=1, walk_back=1, hurt_w=15, hurt_top=-90, crouch_top=-60)
# damage, hitstun (frames), pushback (pixels, 2 per frame), height (0 mid, 1 low, 2 overhead), knockdown
MOVES = dict(lp=(7, 12, 6, 0, 0), hp=(16, 20, 14, 0, 0), lk=(9, 14, 8, 1, 0), hk=(18, 22, 12, 0, 0),
             c_lp=(6, 11, 6, 0, 0), c_lk=(8, 13, 8, 1, 0), sweep=(14, 20, 6, 1, 1),
             j_p=(12, 16, 8, 2, 0), j_k=(15, 18, 10, 2, 0))


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
    return [frame(stance(lean=4, head=(-2, 1), hand_f=(14, -60), hand_b=(4, -56)), 4, face='hit'),
            frame(stance(lean=-4, hip=(-2, -41), head=(-3, 2), hand_f=(10, -56), hand_b=(-2, -54)), 4,
                  face='hit')]


CROUCH = dict(hip=(0, -28), lean=22, hand_f=(26, -46), hand_b=(16, -40))


def crouch():
    return [frame(stance(**CROUCH), 8)]


def c_lp():
    return [frame(stance(**CROUCH), 3),
            frame(stance(**{**CROUCH, 'lean': 26, 'hand_f': (38, -44)}), 4, 'hand_f'),
            frame(stance(**{**CROUCH, 'hand_f': (30, -44)}), 6)]


def c_lk():
    c = {**CROUCH, 'lean': 12}
    return [frame(stance(**c, ankle_f=(20, -10), toe_f=(25, -9)), 4),
            frame(stance(**c, ankle_f=(38, -6), toe_f=(44, -5)), 4, 'toe_f'),
            frame(stance(**c, ankle_f=(24, -5), toe_f=(30, -4)), 6)]


def sweep():
    # low leg sweep
    c = dict(hip=(-2, -22), lean=34, hand_f=(22, -14), hand_b=(10, -10), ankle_b=(-12, -3))
    return [frame(stance(**c, ankle_f=(16, -4), toe_f=(22, -3)), 5),
            frame(stance(**c, ankle_f=(42, -4), toe_f=(48, -3)), 6, 'ankle_f'),
            frame(stance(**c, ankle_f=(30, -4), toe_f=(36, -3)), 9),
            frame(stance(**CROUCH), 6)]


def block():
    return [frame(stance(lean=8, hand_f=(18, -82), hand_b=(16, -72)), 4)]


def c_block():
    return [frame(stance(**{**CROUCH, 'lean': 12, 'hand_f': (20, -62), 'hand_b': (18, -54)}), 4)]


TUCK = dict(hip=(0, -46), lean=12, ankle_f=(12, -24), ankle_b=(-6, -22), hand_f=(22, -66), hand_b=(14, -58))


def jump():
    return [frame(stance(hip=(0, -44), ankle_f=(14, -10), ankle_b=(-10, -8)), 6),
            frame(stance(**TUCK), 14),
            frame(stance(hip=(0, -45), ankle_f=(14, -8), ankle_b=(-8, -6)), 30)]


def j_p():
    # double axe-handle blow from above
    return [frame(stance(**{**TUCK, 'hand_f': (12, -86), 'hand_b': (8, -84)}), 4),
            frame(stance(**{**TUCK, 'lean': 24, 'hand_f': (34, -56), 'hand_b': (30, -58)}), 10, 'hand_f'),
            frame(stance(**TUCK), 30)]


def j_k():
    # flying knee
    return [frame(stance(**TUCK), 3),
            frame(stance(hip=(4, -48), lean=4, ankle_f=(14, -36), toe_f=(18, -32), ankle_b=(-8, -22),
                         hand_f=(26, -74), hand_b=(20, -72)), 12, 'knee_f'),
            frame(stance(**TUCK), 30)]


LYING = dict(hip=(14, -8), lean=-86, ankle_f=(38, -4), ankle_b=(32, -3), toe_f=(40, -10), toe_b=(34, -9),
             hand_f=(4, -5), hand_b=(-2, -3), head=(0, 4))


def fall():
    return [frame(stance(lean=-24, hip=(-2, -40), ankle_f=(12, -10), hand_f=(14, -70), hand_b=(-6, -66)), 6,
                  face='hit'),
            frame(stance(lean=-62, hip=(4, -22), ankle_f=(26, -14), ankle_b=(20, -8), hand_f=(0, -36),
                         hand_b=(-10, -30)), 8, face='hit'),
            frame(stance(**LYING), 8, face='hit')]


def getup():
    return [frame(stance(hip=(6, -14), lean=-20, ankle_f=(26, -3), ankle_b=(18, -3), hand_f=(-6, -6),
                         hand_b=(-10, -4)), 10),
            frame(stance(hip=(0, -30), lean=20, ankle_f=(16, -3), ankle_b=(-10, -3), hand_f=(20, -44),
                         hand_b=(12, -34)), 10)]


def win():
    # double biceps: both fists up next to the head
    return [frame(stance(lean=2, hip=(0, -44), hand_f=(14, -86), hand_b=(-12, -84), ankle_f=(13, -3),
                         ankle_b=(-13, -3)), 16, face='win'),
            frame(stance(lean=2, hip=(0, -43), hand_f=(13, -88), hand_b=(-11, -86), ankle_f=(13, -3),
                         ankle_b=(-13, -3), head=(0, -1)), 16, face='win')]


def anims():
    return dict(idle=idle(), walk=walk(), lp=lp(), hp=hp(), lk=lk(), hk=hk(), hit=hit(),
                crouch=crouch(), c_lp=c_lp(), c_lk=c_lk(), sweep=sweep(), block=block(), c_block=c_block(),
                jump=jump(), j_p=j_p(), j_k=j_k(), fall=fall(), getup=getup(), win=win())


if __name__ == '__main__':
    a = anims()
    out = Path(sys.argv[1] if len(sys.argv) > 1 else 'konrad.png')
    frames = [fa.render(f['pose'], COSTUME, f['face']) for n in a for f in a[n]]
    fa.sheet(frames, PALETTE, scale=2, cols=8).save(out)
    print(out)

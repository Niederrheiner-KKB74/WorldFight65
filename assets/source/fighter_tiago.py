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
    (30, 16, 18),       # 1 outline
    (78, 42, 30),       # 2 skin, darkest
    (116, 66, 44),      # 3 skin, dark
    (156, 96, 62),      # 4 skin
    (196, 136, 92),     # 5 skin, light
    (28, 20, 24),       # 6 hair
    (120, 118, 142),    # 7 trousers, darkest
    (170, 170, 190),    # 8 trousers, dark
    (226, 224, 216),    # 9 trousers
    (255, 252, 240),    # 10 trousers, light
    (40, 150, 68),      # 11 belt green
    (246, 206, 40),     # 12 belt yellow
    (255, 158, 84),     # 13 rim light (sunset)
    (244, 240, 230),    # 14 eye white
    (120, 32, 32),      # 15 mouth
]
SKIN, PANTS = (4, 3, 5, 2), (9, 8, 10, 7)
COSTUME = fa.Costume(
    skin=SKIN, torso=SKIN, pelvis=PANTS, thigh=PANTS, shin=PANTS, foot=SKIN, rim=13,
    hair=(6, 1, 2), hair_style='curly', eye=14, pupil=1, mouth=15,
    belt=11, belt2=12, bare_torso=True, loose=True,
    neck_w=5, w_upper=(6, 5, 1.5), w_fore=(5, 4, 1), w_thigh=(11, 10, 1), w_shin=(10, 11, 0), hand_r=3, foot_w=5,
    head_r=6, chest=8,
)
# health = width of the energy bar in pixels; speeds in pixels per frame; hurt box half width and top
STATS = dict(health=128, walk_fwd=2, walk_back=1, hurt_w=13, hurt_top=-92, crouch_top=-62)
# damage, hitstun (frames), pushback (pixels, 2 per frame), height (0 mid, 1 low, 2 overhead), knockdown
MOVES = dict(lp=(6, 12, 6, 0, 0), hp=(14, 18, 12, 0, 0), lk=(8, 14, 8, 0, 0), hk=(16, 20, 14, 0, 0),
             c_lp=(5, 11, 6, 0, 0), c_lk=(7, 13, 8, 1, 0), sweep=(12, 20, 6, 1, 1),
             j_p=(10, 16, 8, 2, 0), j_k=(13, 18, 10, 2, 0))


def stance(bob=0.0, sway=0.0, guard=0.0, **kw):
    a = dict(hip=(sway * 0.3, -45 + bob), lean=4 + sway,
             hand_f=(15 + sway, -77 + bob + guard * 1.5), hand_b=(7 + sway, -60 + bob - guard))
    a.update(kw)
    return build(**a)


def idle():
    out = []
    for i in range(4):
        t = i / 4 * 2 * math.pi
        out.append(frame(stance(bob=1.5 + 1.5 * math.sin(t), sway=2.5 * math.sin(t), guard=2.5 * math.sin(t),
                                ankle_b=(-14 - 3 * math.sin(t), -3)), 8))
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
            frame(stance(lean=14, hip=(3, -44), ankle_f=(20, -3), hand_b=(34, -70), hand_f=(8, -66)), 5, 'hand_b',
                  b_front=True),
            frame(stance(lean=10, hip=(2, -44), ankle_f=(18, -3), hand_b=(22, -66)), 5, b_front=True),
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
    return [frame(stance(lean=-14, head=(-2, 1), hand_f=(10, -62), hand_b=(-8, -58)), 4, face='hit'),
            frame(stance(lean=-20, hip=(-2, -44), head=(-3, 2), hand_f=(6, -58), hand_b=(-12, -56)), 4,
                  face='hit')]


CROUCH = dict(hip=(0, -28), lean=12, hand_f=(16, -56), hand_b=(5, -42))


def crouch():
    return [frame(stance(**CROUCH), 8)]


def c_lp():
    return [frame(stance(**CROUCH), 3),
            frame(stance(**{**CROUCH, 'lean': 18, 'hand_f': (33, -50)}), 4, 'hand_f'),
            frame(stance(**{**CROUCH, 'hand_f': (22, -52)}), 5)]


def c_lk():
    # low snap kick along the floor
    c = {**CROUCH, 'lean': 4}
    return [frame(stance(**c, ankle_f=(18, -10), toe_f=(23, -9)), 3),
            frame(stance(**c, ankle_f=(38, -7), toe_f=(44, -6)), 4, 'toe_f'),
            frame(stance(**c, ankle_f=(22, -5), toe_f=(28, -4)), 6)]


def sweep():
    # rasteira: low sweep, the leg slides along the floor
    c = dict(hip=(-2, -22), lean=26, hand_f=(18, -16), hand_b=(6, -12), ankle_b=(-12, -3))
    return [frame(stance(**c, ankle_f=(14, -4), toe_f=(20, -3)), 4),
            frame(stance(**c, ankle_f=(42, -4), toe_f=(48, -3)), 6, 'ankle_f'),
            frame(stance(**c, ankle_f=(30, -4), toe_f=(36, -3)), 8),
            frame(stance(**CROUCH), 6)]


def block():
    return [frame(stance(lean=-4, hand_f=(14, -84), hand_b=(12, -74)), 4)]


def c_block():
    return [frame(stance(**{**CROUCH, 'lean': 4, 'hand_f': (14, -64), 'hand_b': (12, -56)}), 4)]


TUCK = dict(hip=(0, -48), lean=6, ankle_f=(12, -26), ankle_b=(-6, -24), hand_f=(16, -74), hand_b=(4, -60))


def jump():
    return [frame(stance(hip=(0, -46), ankle_f=(14, -10), ankle_b=(-10, -8)), 6),
            frame(stance(**TUCK), 14),
            frame(stance(hip=(0, -47), ankle_f=(12, -8), ankle_b=(-8, -6)), 30)]


def j_p():
    return [frame(stance(**{**TUCK, 'hand_f': (10, -70)}), 3),
            frame(stance(**{**TUCK, 'lean': 16, 'hand_f': (32, -60)}), 10, 'hand_f'),
            frame(stance(**TUCK), 30)]


def j_k():
    # flying kick
    return [frame(stance(**TUCK), 3),
            frame(stance(hip=(0, -48), lean=-12, ankle_f=(38, -30), toe_f=(44, -28), ankle_b=(-8, -26),
                         hand_f=(10, -76), hand_b=(-6, -66)), 12, 'toe_f'),
            frame(stance(**TUCK), 30)]


LYING = dict(hip=(14, -7), lean=-86, ankle_f=(38, -4), ankle_b=(32, -3), toe_f=(40, -10), toe_b=(34, -9),
             hand_f=(4, -4), hand_b=(-2, -3), head=(0, 4))


def fall():
    return [frame(stance(lean=-30, hip=(-2, -40), ankle_f=(12, -10), hand_f=(10, -70), hand_b=(-12, -66)), 6,
                  face='hit'),
            frame(stance(lean=-66, hip=(4, -22), ankle_f=(26, -14), ankle_b=(20, -8), hand_f=(-4, -36),
                         hand_b=(-14, -30)), 8, face='hit'),
            frame(stance(**LYING), 8, face='hit')]


def getup():
    return [frame(stance(hip=(6, -14), lean=-24, ankle_f=(26, -3), ankle_b=(18, -3), hand_f=(-8, -6),
                         hand_b=(-12, -4)), 10),
            frame(stance(hip=(0, -30), lean=14, ankle_f=(16, -3), ankle_b=(-10, -3), hand_f=(14, -48),
                         hand_b=(6, -36)), 10)]


def win():
    # one fist raised high, the other hand on the hip
    return [frame(stance(lean=-2, hip=(0, -46), hand_f=(10, -96), hand_b=(-8, -50), ankle_f=(10, -3),
                         ankle_b=(-11, -3)), 16, face='win'),
            frame(stance(lean=-4, hip=(0, -47), hand_f=(11, -97), hand_b=(-8, -51), ankle_f=(10, -3),
                         ankle_b=(-11, -3), head=(-1, -1)), 16, face='win')]


def anims():
    return dict(idle=idle(), walk=walk(), lp=lp(), hp=hp(), lk=lk(), hk=hk(), hit=hit(),
                crouch=crouch(), c_lp=c_lp(), c_lk=c_lk(), sweep=sweep(), block=block(), c_block=c_block(),
                jump=jump(), j_p=j_p(), j_k=j_k(), fall=fall(), getup=getup(), win=win())


if __name__ == '__main__':
    a = anims()
    out = Path(sys.argv[1] if len(sys.argv) > 1 else 'tiago.png')
    frames = [fa.render(f['pose'], COSTUME, f['face']) for n in a for f in a[n]]
    fa.sheet(frames, PALETTE, scale=2, cols=8).save(out)
    print(out)

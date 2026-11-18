#!/usr/bin/env python3
"""Pose guides (mannequins) for the generator prompts of the attacks.

  python3 tools/pose_guide.py            -> assets/art/guides/<fighter>_<anim>_<frame>.png (+ one sheet per anim)

A simple mannequin per frame, side view facing right, in the 256 x 256 cell of the sprite sheets (floor line
y = 239, standing height 224 px). The LEAD (front) arm and leg are ORANGE, the REAR arm and leg are BLUE,
torso and head grey; the small dark dot marks the face side. Hands and feet of the hitting frame are placed
on the hit boxes of the fighter module (assets/source/fighter_<name>.py), so the art and the game agree.
Limbs are solved with two-bone IK from target points; see POSES below.
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[1] / 'assets' / 'art' / 'guides'
CELL, GROUND, S = 256, 239, 4
THIGH, SHIN, UPPER, FORE = 55, 52, 36, 34
TORSO, HEAD_R = 64, 21
LEAD, REAR = ((240, 150, 40), (200, 100, 20)), ((40, 80, 200), (20, 40, 140))
BODY, HEADC = (150, 150, 150), (175, 175, 175)

# guard stance (cell coordinates): hip, feet (ankles), hands; torso lean in degrees (+ = forward)
GUARD = dict(hip=(122, 128), lean=4, lead_foot=(160, 231), rear_foot=(86, 231),
             lead_hand=(165, 82), rear_hand=(140, 88))


def P(**kw):
    p = dict(GUARD)
    p.update(kw)
    return p


# crouch (about 150 px high, as the crouch sprites)
CROUCH = dict(squat=True, hip=(118, 188), lean=20, lead_foot=(166, 231), rear_foot=(112, 231),
              lead_hand=(166, 120), rear_hand=(148, 126))


def Q(**kw):
    p = dict(CROUCH)
    p.update(kw)
    return p


def crouch_attacks():
    return {
        'c_lp': [Q(lead_hand=(180, 118), lean=22),
                 Q(lead_hand=(208, 114), lean=26, hip=(122, 190)),      # punch at stomach height of a stander
                 Q(lead_hand=(180, 120), lean=22)],
        'c_lk': [Q(lead_foot=(178, 222), lean=16),
                 Q(lead_foot=(236, 226), lean=8, hip=(114, 192)),       # foot along the floor, ankle height
                 Q(lead_foot=(184, 228), lean=14)],
        'sweep': [Q(hip=(112, 198), lean=34, rear_hand=(84, 232), lead_hand=(168, 168), lead_foot=(158, 231), rear_foot=(118, 231)),
                  Q(hip=(110, 200), lean=38, rear_hand=(82, 232), lead_hand=(166, 174), rear_foot=(116, 231),
                    lead_foot=(236, 228), arrow=((170, 236), (226, 236))),   # leg sweeps along the floor
                  Q(hip=(112, 198), lean=34, rear_hand=(84, 232), lead_hand=(168, 170), rear_foot=(118, 231),
                    lead_foot=(196, 230), arrow=((232, 222), (204, 222))),
                  Q()],
    }


# per fighter and animation: one pose per frame (only what differs from the guard)
POSES = {
    'tiago': {
        'lp': [P(lead_hand=(180, 72), lean=8),
               P(lead_hand=(198, 64), lean=12, hip=(126, 128)),          # jab, hit box x 173-207 y 49-78
               P(lead_hand=(176, 76), lean=6)],
        'hp': [P(rear_hand=(108, 84), lead_hand=(160, 86), lean=-4, hip=(118, 128)),      # wind-up
               P(rear_hand=(202, 70), lead_hand=(162, 84), lean=16, hip=(130, 130),
                 rear_foot=(92, 228)),                                                    # straight, x 178-212
               P(rear_hand=(192, 76), lead_hand=(162, 86), lean=12, hip=(128, 130)),     # follow-through
               P(rear_hand=(150, 86), lean=6)],
        'lk': [P(lead_foot=(150, 170), knee_lead=1, lean=-2, hip=(118, 126)),             # chamber
               P(lead_foot=(228, 124), lean=-10, hip=(114, 124), lead_hand=(150, 80)),   # ponteira, x 202-236
               P(lead_foot=(160, 190), lean=-2, hip=(118, 126))],
        'hk': [P(rear_foot=(120, 178), rear_knee=(154, 146), lean=-6, hip=(126, 126)),                          # rear knee rises
               P(rear_foot=(228, 72), lean=-24, hip=(112, 124), lead_foot=(140, 231),
                 lead_hand=(150, 96), rear_hand=(100, 110)),                              # martelo, x 207-240 y 56-85
               P(rear_foot=(170, 150), lean=-12, hip=(120, 126), lead_foot=(140, 231)),
               P(rear_foot=(116, 231), lean=0)],
    },
    'konrad': {
        'lp': [P(lead_hand=(180, 78), lean=8),
               P(lead_hand=(198, 70), lean=12, hip=(126, 130)),          # jab, x 171-206 y 55-85
               P(lead_hand=(176, 82), lean=6)],
        'hp': [P(rear_elbow=(90, 64), rear_hand=(80, 38), lead_hand=(168, 84), lean=-12,
                 hip=(116, 130)),                                                         # wind-up: arm raised high behind
               P(rear_elbow=(166, 92), rear_hand=(204, 88), lead_elbow=(154, 112), lead_hand=(170, 100), lean=18,
                 hip=(132, 132),
                 rear_foot=(96, 226), arrow=((86, 40), (196, 82))),                      # forearm smash x 171-206 y 75-105
               P(rear_elbow=(168, 106), rear_hand=(198, 116), lead_elbow=(156, 116), lead_hand=(172, 106), lean=22,
                 hip=(134, 134),
                 rear_foot=(98, 226), arrow=((200, 92), (196, 116))),                     # follow-through, swept down
               P(rear_hand=(146, 88), lean=8, hip=(126, 130))],                             # back towards the guard
        'lk': [P(lead_foot=(150, 176), lean=0, hip=(118, 128)),                           # knee up
               P(lead_foot=(196, 206), lean=-4, hip=(118, 130)),                          # stomp, x 171-206 y 189-219
               P(lead_foot=(160, 200), lean=0, hip=(118, 128))],
        'hk': [P(rear_foot=(116, 198), rear_knee=(150, 156), lean=6, hip=(124, 130), lead_hand=(182, 70),
                 rear_hand=(176, 78)),
               P(rear_foot=(150, 168), rear_knee=(182, 122), lean=12, hip=(130, 132),
                 lead_hand=(192, 66), rear_hand=(186, 74)),                               # knee, x 159-194 y 107-137
               P(rear_foot=(112, 208), rear_knee=(146, 164), lean=8, hip=(126, 130), lead_hand=(184, 72),
                 rear_hand=(178, 80)),
               P(lean=4)],
    },
}


def other_anims(fighter):
    air = dict(squat=True, hip=(122, 126), lean=8, lead_foot=(150, 176), rear_foot=(108, 188),
               lead_hand=(166, 80), rear_hand=(146, 86))

    def A(**kw):
        p = dict(air)
        p.update(kw)
        return p
    if fighter == 'konrad':
        win = [P(lean=0, lead_elbow=(166, 66), lead_hand=(160, 36), rear_elbow=(84, 66), rear_hand=(90, 36)),
               P(lean=0, lead_elbow=(168, 64), lead_hand=(162, 32), rear_elbow=(82, 64), rear_hand=(88, 32),
                 hip=(122, 126))]                                  # double biceps
    else:
        win = [P(lean=-2, lead_hand=(158, 12), rear_hand=(140, 96)),
               P(lean=-4, lead_hand=(160, 8), rear_hand=(136, 100), hip=(122, 126))]   # one fist raised high
    return {
        'hit': [P(lean=-20, hip=(112, 128), lead_hand=(150, 104), rear_hand=(118, 112)),
                P(lean=-8, hip=(116, 128), lead_hand=(160, 92), rear_hand=(132, 98))],
        'jump': [Q(hip=(118, 176), lean=14, lead_hand=(168, 112), rear_hand=(150, 118)),
                 A(),
                 Q(hip=(118, 178), lean=12, lead_hand=(166, 116), rear_hand=(148, 122))],
        'j_p': [A(), A(lead_hand=(204, 112), lean=16, arrow=((168, 84), (198, 108))), A()],
        'j_k': [A(), A(lead_foot=(214, 196), lean=-6, rear_foot=(104, 184), arrow=((156, 178), (208, 194))), A()],
        'fall': [P(lean=-34, hip=(108, 136), lead_foot=(150, 212), rear_foot=(84, 231),
                   lead_hand=(150, 52), rear_hand=(70, 70)),
                 P(lean=-74, hip=(124, 186), lead_foot=(186, 150), rear_foot=(176, 168),
                   lead_hand=(70, 140), rear_hand=(64, 168)),
                 P(lean=-90, hip=(140, 222), lead_foot=(214, 231), rear_foot=(206, 226),
                   lead_hand=(110, 232), rear_hand=(96, 228))],
        'getup': [Q(hip=(112, 196), lean=6, lead_foot=(150, 231), rear_foot=(66, 231), rear_knee=(104, 232),
                    rear_hand=(82, 232), lead_hand=(150, 150)),
                  Q(hip=(118, 160), lean=10, lead_hand=(162, 100), rear_hand=(146, 108))],
        'win': win,
    }


for _f in POSES:
    POSES[_f].update(crouch_attacks())
    POSES[_f].update(other_anims(_f))


def fwd_angle(a, b):
    """direction a -> b as an angle from straight down, positive towards the front (+x), degrees"""
    return math.degrees(math.atan2(b[0] - a[0], b[1] - a[1]))


def joint(root, target, l1, l2, leg):
    """two-bone IK with a human joint: a knee only bends so that the shin folds BACK behind the thigh
    (shin angle <= thigh angle), an elbow only so that the forearm folds FORWARD/UP (forearm angle >=
    upper-arm angle). Of the two IK solutions the anatomically possible one is taken."""
    best = None
    for bend in (1, -1):
        j, e = ik(root, target, l1, l2, bend)
        a1, a2 = fwd_angle(root, j), fwd_angle(j, e)
        d = (a1 - a2) if leg else (a2 - a1)
        d = (d + 180) % 360 - 180
        score = d if d >= -1 else -1000 + d
        if best is None or score > best[0]:
            best = (score, j, e)
    return best[1], best[2]


def ik(root, target, l1, l2, bend):
    """joint position of a two-bone limb; bend = +1 / -1 picks the side of the joint"""
    dx, dy = target[0] - root[0], target[1] - root[1]
    d = max(1e-6, min(math.hypot(dx, dy), l1 + l2 - 0.01))
    a = math.atan2(dy, dx)
    c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    b = math.acos(max(-1.0, min(1.0, c)))
    ang = a - bend * b
    j = (root[0] + l1 * math.cos(ang), root[1] + l1 * math.sin(ang))
    # the end point as reached (clamped to the limb length)
    e = (j[0] + l2 * math.cos(math.atan2(target[1] - j[1], target[0] - j[0])),
         j[1] + l2 * math.sin(math.atan2(target[1] - j[1], target[0] - j[0])))
    return j, e


def draw(pose, d, ox):
    def L(pts, col, w):
        d.line([((ox + x) * S, y * S) for x, y in pts], fill=col, width=int(w * S), joint='curve')

    def C(c, r, col):
        x, y = c
        d.ellipse([(ox + x - r) * S, (y - r) * S, (ox + x + r) * S, (y + r) * S], fill=col)

    hip = pose['hip']
    lean = math.radians(pose['lean'])
    neck = (hip[0] + TORSO * math.sin(lean), hip[1] - TORSO * math.cos(lean))
    ux, uy = math.sin(lean), -math.cos(lean)        # along the torso, hip -> neck
    px, py = -uy, ux                                 # across the torso (towards the front when upright)
    head = (neck[0] + (HEAD_R + 6) * ux + 4 * px, neck[1] + (HEAD_R + 6) * uy + 4 * py)
    sh_lead = (neck[0] + 8 * px - 8 * ux, neck[1] + 8 * py - 8 * uy)
    sh_rear = (neck[0] - 10 * px - 8 * ux, neck[1] - 10 * py - 8 * uy)

    def leg(foot_key, knee_key, cols, bend):
        foot = pose[foot_key]
        if knee_key in pose:                       # knee given (knee strike): shin hangs from it
            knee = pose[knee_key]
            dx, dy = foot[0] - knee[0], foot[1] - knee[1]
            n = math.hypot(dx, dy) or 1
            ank = (knee[0] + SHIN * dx / n, knee[1] + SHIN * dy / n)
        else:
            knee, ank = joint(hip, foot, THIGH, SHIN, leg=True)
        L([hip, knee, ank], cols[0], 15)
        on_floor = ank[1] > GROUND - 14
        if on_floor:
            L([(ank[0] - 5, GROUND - 3), (ank[0] + 20, GROUND - 3)], cols[1], 9)
        else:                                      # foot continues the shin
            dx, dy = ank[0] - knee[0], ank[1] - knee[1]
            n = math.hypot(dx, dy) or 1
            L([ank, (ank[0] + 16 * dx / n + 6, ank[1] + 16 * dy / n - 4)], cols[1], 9)

    def arm(sh, hand_key, elbow_key, cols, bend):
        hand = pose[hand_key]
        if elbow_key in pose:
            el = pose[elbow_key]
        else:
            el, hand = joint(sh, hand, UPPER, FORE, leg=False)
        L([sh, el, hand], cols[0], 12)
        C(hand, 8, cols[1])

    # rear leg behind the body; both arms in front of the (narrow, side-view) torso so they stay visible
    leg('rear_foot', 'rear_knee', REAR, 1)
    h0, n0 = (hip[0] - 6 * ux, hip[1] - 6 * uy), (neck[0] - 4 * ux, neck[1] - 4 * uy)
    d.polygon([((ox + h0[0] - 14 * px) * S, (h0[1] - 14 * py) * S), ((ox + h0[0] + 14 * px) * S, (h0[1] + 14 * py) * S),
               ((ox + n0[0] + 16 * px) * S, (n0[1] + 16 * py) * S), ((ox + n0[0] - 16 * px) * S, (n0[1] - 16 * py) * S)],
              fill=BODY)
    C(head, HEAD_R, HEADC)
    C((head[0] + 12 * px - 2 * ux, head[1] + 12 * py - 2 * uy), 4, (80, 80, 80))
    leg('lead_foot', 'lead_knee', LEAD, 1)
    arm(sh_rear, 'rear_hand', 'rear_elbow', REAR, -1)
    arm(sh_lead, 'lead_hand', 'lead_elbow', LEAD, -1)
    if 'arrow' in pose:                             # motion of the striking limb since the previous frame
        (x0, y0), (x1, y1) = pose['arrow']
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) // 8))
        for i in range(0, n, 2):                    # dashed
            a, b = i / n, min(1, (i + 1) / n)
            L([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)], (120, 120, 120), 3)
        ang = math.atan2(y1 - y0, x1 - x0)
        for da in (2.6, -2.6):
            L([(x1, y1), (x1 + 10 * math.cos(ang + da), y1 + 10 * math.sin(ang + da))], (120, 120, 120), 3)


def check_floor():
    bad = []
    for f, anims in POSES.items():
        for a, frames in anims.items():
            for k, p in enumerate(frames):
                for foot in ('lead_foot', 'rear_foot'):
                    kn = p.get(foot.replace('foot', 'knee')) or joint(p['hip'], p[foot], THIGH, SHIN, leg=True)[0]
                    if kn[1] > GROUND - 4:
                        bad.append(f'{f} {a} {k + 1} {foot[:4]} knee y {kn[1]:.0f}')
    return bad


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for b in check_floor():
        print('warning: knee below the floor:', b)
    for fighter, anims in POSES.items():
        for anim, frames in anims.items():
            n = len(frames)
            big = Image.new('RGB', (CELL * n * S, CELL * S), 'white')
            d = ImageDraw.Draw(big)
            for k, pose in enumerate(frames):
                d.line([(k * CELL * S, GROUND * S), ((k + 1) * CELL * S, GROUND * S)], fill=(0, 0, 0), width=S)
                if k:
                    d.line([(k * CELL * S, 0), (k * CELL * S, CELL * S)], fill=(200, 200, 200), width=S)
                draw(pose, d, k * CELL)
            sheet = big.resize((CELL * n, CELL), Image.LANCZOS)
            sheet.save(OUT / f'{fighter}_{anim}_guide.png')
            for k in range(n):
                sheet.crop((k * CELL, 0, (k + 1) * CELL, CELL)).resize((512, 512), Image.LANCZOS) \
                    .save(OUT / f'{fighter}_{anim}_{k + 1}.png')
            print(f'{fighter} {anim}: {n} frames')


if __name__ == '__main__':
    main()

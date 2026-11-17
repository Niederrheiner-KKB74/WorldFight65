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
        'hk': [P(rear_foot=(118, 170), lean=-6, hip=(126, 126)),                          # rear knee rises
               P(rear_foot=(228, 72), lean=-24, hip=(112, 124), lead_foot=(140, 231),
                 lead_hand=(150, 96), rear_hand=(100, 110)),                              # martelo, x 207-240 y 56-85
               P(rear_foot=(170, 150), lean=-12, hip=(120, 126), lead_foot=(140, 231)),
               P(rear_foot=(96, 231), lean=0)],
    },
    'konrad': {
        'lp': [P(lead_hand=(180, 78), lean=8),
               P(lead_hand=(198, 70), lean=12, hip=(126, 130)),          # jab, x 171-206 y 55-85
               P(lead_hand=(176, 82), lean=6)],
        'hp': [P(rear_hand=(110, 70), lead_hand=(160, 88), lean=-4, hip=(118, 130)),      # wind-up, arm high
               P(rear_hand=(200, 92), rear_elbow=(160, 92), lead_hand=(164, 84), lean=16,
                 hip=(130, 132), rear_foot=(92, 228)),                                    # forearm smash x 171-206 y 75-105
               P(rear_hand=(192, 100), rear_elbow=(156, 100), lead_hand=(162, 88), lean=14, hip=(128, 132)),
               P(rear_hand=(150, 90), lean=6)],
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
    head = (neck[0] + 6 * math.sin(lean) + 4, neck[1] - HEAD_R - 6)
    sh_lead = (neck[0] + 8, neck[1] + 8)
    sh_rear = (neck[0] - 10, neck[1] + 8)

    def leg(foot_key, knee_key, cols, bend):
        foot = pose[foot_key]
        if knee_key in pose:                       # knee given (knee strike): shin hangs from it
            knee = pose[knee_key]
            dx, dy = foot[0] - knee[0], foot[1] - knee[1]
            n = math.hypot(dx, dy) or 1
            ank = (knee[0] + SHIN * dx / n, knee[1] + SHIN * dy / n)
        else:
            knee, ank = ik(hip, foot, THIGH, SHIN, bend)
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
            el, hand = ik(sh, hand, UPPER, FORE, bend)
        L([sh, el, hand], cols[0], 12)
        C(hand, 8, cols[1])

    # rear limbs behind the body, lead limbs in front
    leg('rear_foot', 'rear_knee', REAR, 1)
    arm(sh_rear, 'rear_hand', 'rear_elbow', REAR, -1)
    d.polygon([((ox + hip[0] - 20) * S, (hip[1] + 6) * S), ((ox + hip[0] + 20) * S, (hip[1] + 6) * S),
               ((ox + neck[0] + 22) * S, (neck[1] + 4) * S), ((ox + neck[0] - 24) * S, (neck[1] + 4) * S)],
              fill=BODY)
    C(head, HEAD_R, HEADC)
    C((head[0] + 12, head[1] - 2), 4, (80, 80, 80))
    leg('lead_foot', 'lead_knee', LEAD, 1)
    arm(sh_lead, 'lead_hand', 'lead_elbow', LEAD, -1)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
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

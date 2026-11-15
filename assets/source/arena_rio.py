#!/usr/bin/env python3
"""Arena 1: beach promenade in Rio de Janeiro at sunset (drawn by Claude for WorldFight65).

320x200 RGB picture: evening sky, the Sugarloaf with its cable car, the sea, the beach with umbrellas,
palm trees and the black-and-white wave pavement of the promenade, on which the fight takes place.
draw() returns the picture as a PIL image; tools/make_assets.py converts it to full-colour glyphs.
Run it directly to write a preview PNG.
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

W, H = 320, 200
HORIZON = 104          # sea starts here
BEACH = 128            # sand starts here
WALL = 150             # promenade kerb
FLOOR = 154            # wave pavement starts here; fighters stand at about y 190


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def sky(img):
    top, mid, low = (28, 30, 82), (150, 70, 110), (255, 170, 80)
    px = img.load()
    for y in range(HORIZON):
        t = y / (HORIZON - 1)
        c = lerp(top, mid, t / 0.6) if t < 0.6 else lerp(mid, low, (t - 0.6) / 0.4)
        for x in range(W):
            px[x, y] = c
    d = ImageDraw.Draw(img)
    # sun, low over the sea
    d.ellipse((120, 80, 152, 112), fill=(255, 226, 140))
    d.ellipse((124, 84, 148, 108), fill=(255, 246, 200))
    # thin evening clouds
    rnd = random.Random(1)
    for cy, cx, ln, col in ((22, 40, 70, (90, 60, 120)), (30, 150, 90, (110, 64, 128)),
                            (48, 210, 60, (190, 96, 120)), (58, 20, 50, (215, 120, 110)),
                            (70, 120, 80, (240, 150, 100))):
        for k in range(3):
            d.line((cx + rnd.randint(-6, 6), cy + k, cx + ln + rnd.randint(-8, 8), cy + k), fill=col)
    # a few stars in the dark part
    for _ in range(18):
        x, y = rnd.randrange(W), rnd.randrange(0, 26)
        px[x, y] = (200, 200, 230)


def mountain(img):
    d = ImageDraw.Draw(img)
    rock, rock_l, green = (56, 46, 72), (92, 72, 96), (40, 56, 52)
    # Morro da Urca (small, left of the Sugarloaf)
    pts = [(196, HORIZON)]
    for x in range(196, 246):
        t = (x - 196) / 50
        pts.append((x, HORIZON - 14 - int(8 * math.sin(t * math.pi))))
    pts.append((246, HORIZON))
    d.polygon(pts, fill=green)
    # Sugarloaf: a steep, rounded granite cone
    def top(x):
        t = (x - 238) / 60
        return HORIZON - int(72 * (math.sin(t * math.pi) ** 0.35) * (1 - 0.3 * t))
    pts = [(238, HORIZON)] + [(x, top(x)) for x in range(238, 299)] + [(298, HORIZON)]
    d.polygon(pts, fill=rock)
    for x in range(240, 262):                 # light side facing the sun
        d.line((x, top(x) + 1, x, top(x) + 4 + (x - 240) // 2), fill=rock_l)
    d.polygon([(238, HORIZON), (250, HORIZON - 14), (266, HORIZON - 8), (276, HORIZON)], fill=green)
    # cable car from the small hill to the summit, with a cabin
    sx = min(range(238, 299), key=top)
    d.line((226, HORIZON - 22, sx, top(sx) + 1), fill=(20, 18, 30))
    cx = 226 + (sx - 226) * 6 // 10
    cy = HORIZON - 22 + (top(sx) + 1 - HORIZON + 22) * 6 // 10
    d.rectangle((cx - 1, cy + 1, cx + 2, cy + 4), fill=(230, 80, 60))
    # far coast on the left
    d.polygon([(0, HORIZON), (0, HORIZON - 8), (30, HORIZON - 12), (60, HORIZON - 6), (96, HORIZON)],
              fill=(70, 50, 90))


def sea(img):
    px = img.load()
    rnd = random.Random(2)
    for y in range(HORIZON, BEACH):
        t = (y - HORIZON) / (BEACH - HORIZON)
        base = lerp((60, 50, 110), (20, 70, 120), t)
        for x in range(W):
            px[x, y] = base
        # sun reflection below the sun (x 120..152), widening towards the beach
        half = 6 + int(14 * t)
        for x in range(136 - half, 136 + half):
            if rnd.random() < 0.55 and (y + x) % 2 == 0:
                px[x, y] = (255, 210, 130) if rnd.random() < 0.6 else (255, 240, 190)
        # wave crests
        if y % 4 == 1:
            for x in range(rnd.randrange(8), W, rnd.randint(14, 26)):
                for k in range(rnd.randint(3, 7)):
                    if x + k < W:
                        px[x + k, y] = lerp(base, (210, 220, 240), 0.55)
    d = ImageDraw.Draw(img)
    # surf line
    for x in range(0, W, 2):
        y = BEACH - 2 + int(1.5 * math.sin(x / 9))
        d.line((x, y, x + 1, y), fill=(235, 240, 245))


def beach(img):
    d = ImageDraw.Draw(img)
    px = img.load()
    rnd = random.Random(3)
    for y in range(BEACH, WALL):
        t = (y - BEACH) / (WALL - BEACH)
        base = lerp((200, 160, 110), (236, 196, 136), t)
        for x in range(W):
            c = base
            if rnd.random() < 0.08:
                c = lerp(base, (150, 110, 80), 0.4)
            px[x, y] = c
    # umbrellas with their shadows (y 128..150)
    for x, col in ((24, (220, 40, 50)), (112, (40, 150, 220)), (150, (250, 200, 40)),
                   (226, (60, 170, 80)), (288, (240, 120, 30))):
        d.line((x, 134, x, 148), fill=(80, 60, 50))
        d.pieslice((x - 13, 128, x + 13, 146), 180, 360, fill=col)
        for k in range(-12, 13, 6):
            d.line((x, 131, x + k, 136), fill=lerp(col, (255, 255, 255), 0.35))
        d.ellipse((x - 9, 146, x + 9, 150), fill=(180, 138, 96))
    # volleyball net
    d.line((182, 132, 182, 148), fill=(70, 50, 40))
    d.line((214, 132, 214, 148), fill=(70, 50, 40))
    for y in range(133, 140, 2):
        d.line((182, y, 214, y), fill=(230, 230, 230))
    for x in range(184, 214, 3):
        d.line((x, 133, x, 139), fill=(200, 200, 200))


def promenade(img):
    d = ImageDraw.Draw(img)
    # kerb between the beach and the pavement
    d.rectangle((0, WALL, W - 1, FLOOR - 1), fill=(170, 160, 150))
    d.line((0, WALL, W - 1, WALL), fill=(220, 214, 204))
    d.line((0, FLOOR - 1, W - 1, FLOOR - 1), fill=(90, 84, 80))
    # wave pavement: black waves on white, waves get taller towards the viewer (simple perspective)
    px = img.load()
    for y in range(FLOOR, H):
        t = (y - FLOOR) / (H - FLOOR)
        period = 12 + 18 * t                  # band height in pixels
        amp = 3 + 9 * t
        wl = 40 + 50 * t                      # wavelength
        for x in range(W):
            phase = (y - FLOOR + amp * math.sin(2 * math.pi * (x - 160) / wl)) / period
            dark = (phase % 1.0) < 0.5
            c = (58, 54, 60) if dark else (206, 200, 186)
            # warm evening light from the left, a little darker towards the right
            c = lerp(c, (250, 180, 120), 0.12 * (1 - x / W))
            px[x, y] = c


def palm(img, x0, flip):
    d = ImageDraw.Draw(img)
    s = -1 if flip else 1
    trunk = (96, 64, 40)
    pts = []
    for i in range(0, 120, 4):            # curved trunk from the ground (y 196) up to the crown
        t = i / 120
        pts.append((x0 + s * int(18 * t * t), 196 - i))
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        d.line((xa, ya, xb, yb), fill=trunk, width=6)
        d.line((xa - 2, ya, xb - 2, yb), fill=(130, 92, 58), width=1)
    cx, cy = pts[-1]
    for ang in (-160, -130, -100, -70, -40, -10, 20):
        a = math.radians(ang)
        for k in range(0, 34, 2):
            x = cx + int(k * math.cos(a))
            y = cy + int(k * math.sin(a)) + int(k * k / 70)
            d.ellipse((x - 3, y - 2, x + 3, y + 2), fill=(30, 90, 50) if k % 4 else (50, 120, 60))
    d.ellipse((cx - 5, cy - 2, cx + 5, cy + 6), fill=(80, 60, 30))


def kiosk(img):
    d = ImageDraw.Draw(img)
    # beach kiosk behind the kerb, partly covering the sand
    d.rectangle((40, 122, 82, 151), fill=(40, 120, 70))
    d.rectangle((44, 130, 78, 140), fill=(250, 220, 120))
    d.polygon([(34, 122), (88, 122), (80, 112), (42, 112)], fill=(240, 240, 230))
    for x in range(42, 82, 8):
        d.polygon([(x, 112), (x + 4, 112), (x + 5, 122), (x + 1, 122)], fill=(40, 150, 70))
    # coconuts on the counter
    for x in (50, 58, 66):
        d.ellipse((x, 141, x + 5, 146), fill=(90, 140, 60))


def draw():
    img = Image.new('RGB', (W, H))
    sky(img)
    mountain(img)
    sea(img)
    beach(img)
    kiosk(img)
    promenade(img)
    palm(img, 8, False)
    palm(img, 310, True)
    return img


if __name__ == '__main__':
    out = Path(sys.argv[1] if len(sys.argv) > 1 else 'arena_rio.png')
    draw().resize((W * 3, H * 3), Image.NEAREST).save(out)
    print(out)

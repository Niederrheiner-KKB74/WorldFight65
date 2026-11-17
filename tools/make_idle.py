#!/usr/bin/env python3
"""Make a fighter's idle (breathing) sheet from his master image.

  python3 tools/make_idle.py FIGHTER [--lift 0,3,5,3] [--out PATH]

Image generators either change too much between idle frames (the figure "pulses") or hardly anything
(no visible breathing). This draws the breathing from the master itself: the upper body above the hips
is stretched upwards a little, rising linearly from 0 at the hips to LIFT px at the top of the head, so the
legs and the feet stay exactly in place and nothing else changes. LIFT is in cell pixels (256 px cell);
in the game one pixel is about 2.3 cell pixels, so 0,3,5,3 moves the head by 0, 1, 2, 1 game pixels.
Output: assets/art/<fighter>/idle.png (4 cells of 256 x 256, magenta background).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import import_fighter as imf     # noqa: E402

KEY = (255, 0, 255)
HIP = 0.52                       # hip line as a share of the figure height, measured from the soles


def breathe(cell, lift):
    if lift == 0:
        return cell.copy()
    fg = imf.figure_mask(cell)
    ys = np.nonzero(fg.any(axis=1))[0]
    top, bot = int(ys[0]), int(ys[-1])
    hip = bot - HIP * (bot - top)
    out = np.empty_like(cell)
    out[:] = KEY
    # destination row y takes source row s(y): below the hip line s = y; above it the body is stretched,
    # so that the hip row stays and the top row moves up by lift (nearest row: crisp pixel art)
    for y in range(cell.shape[0]):
        if y >= hip:
            s = y
        else:
            # dst = hip - (hip - src) * k with k = (hip - top + lift) / (hip - top)
            k = (hip - top + lift) / (hip - top)
            s = hip - (hip - y) / k
        si = int(round(s))
        if 0 <= si < cell.shape[0]:
            out[y] = cell[si]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('fighter')
    ap.add_argument('--lift', default='0,3,5,3')
    ap.add_argument('--out')
    a = ap.parse_args()
    art = ROOT / 'assets' / 'art' / a.fighter
    master = imf.cells(art / 'master.png')[0]
    lifts = [int(v) for v in a.lift.split(',')]
    sheet = Image.new('RGB', (imf.CELL * len(lifts), imf.CELL), KEY)
    for k, lift in enumerate(lifts):
        sheet.paste(Image.fromarray(breathe(master, lift)), (k * imf.CELL, 0))
    dst = Path(a.out) if a.out else art / 'idle.png'
    sheet.save(dst)
    print(f'{dst}: {len(lifts)} frames, lift {lifts} cell px')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Bring a generator sprite sheet that misses the format of docs/art_import.md into it.

  python3 tools/normalize_sheet.py IN.png FRAMES OUT.png [--height 224]

The input holds FRAMES figures in one row on a magenta background, in any image size (generators like to
deliver 2172 x 724 instead of 1536 x 256). The row is split into FRAMES equal slots; the figures keep their
position inside their slot and their common foot line. The whole sheet is scaled once so that the tallest
figure is --height px high, then every slot is written as a 256 x 256 cell with the foot line at y = 239
and the slot centre at x = 128. The background is written as pure #FF00FF.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import import_fighter as imf    # noqa: E402

KEY = (255, 0, 255)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('frames', type=int)
    ap.add_argument('dst')
    ap.add_argument('--height', type=int, default=224)
    a = ap.parse_args()

    rgb = np.array(Image.open(a.src).convert('RGB'))
    H, W = rgb.shape[:2]
    bg = imf.background_mask(rgb)
    slot = W / a.frames
    tops, foot = [], 0
    for k in range(a.frames):
        x0, x1 = round(k * slot), round((k + 1) * slot)
        ys = np.nonzero((~bg[:, x0:x1]).any(axis=1))[0]
        tops.append(int(ys[0]))
        foot = max(foot, int(ys[-1]))
    scale = a.height / (foot - min(tops) + 1)
    out = Image.new('RGB', (imf.CELL * a.frames, imf.CELL), KEY)
    # colour: background replaced by the outline colour, resampled with LANCZOS (no aliasing on large
    # downscales of generator images); figure mask resampled separately, key colour put back outside it
    pad = int(imf.CELL / scale) + 1           # margin, so every cell window lies inside
    col = rgb.copy()
    col[bg] = imf.OUTLINE_RGB
    col = np.pad(col, ((pad, pad), (pad, pad), (0, 0)), mode='edge')
    msk = np.pad((~bg).astype(np.uint8) * 255, pad, mode='constant')
    src_c, src_m = Image.fromarray(col), Image.fromarray(msk)
    out = Image.new('RGB', (imf.CELL * a.frames, imf.CELL), KEY)
    for k in range(a.frames):
        cx = (k + 0.5) * slot
        # source window that maps onto the 256 x 256 cell
        sx0 = pad + cx - 128 / scale
        sy0 = pad + foot + 1 - (imf.BASELINE + 1) / scale
        box = (sx0, sy0, sx0 + imf.CELL / scale, sy0 + imf.CELL / scale)
        c = np.array(src_c.resize((imf.CELL, imf.CELL), Image.LANCZOS, box=box))
        m = np.array(src_m.resize((imf.CELL, imf.CELL), Image.BOX, box=box)) >= 128
        c[~m] = KEY
        out.paste(Image.fromarray(c), (k * imf.CELL, 0))
    out.save(a.dst)
    print(f'{a.src}: {W} x {H}, {a.frames} slots of {slot:.0f} px, figures {foot - min(tops) + 1} px high, '
          f'foot line y = {foot}, scale {scale:.3f} -> {a.dst}')


if __name__ == '__main__':
    main()

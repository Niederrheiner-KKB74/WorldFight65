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
    ap.add_argument('--scale', type=float, help='fixed scale instead of --height (e.g. the scale of the '
                    'master, for images drawn on the same canvas as the master: crouching figures stay small)')
    ap.add_argument('--area-match', metavar='MASTER', help='scale so that the median figure area equals the area '
                    'of the master cell - for poses whose height says nothing about the scale (crouching, '
                    'jumping, lying, raised fists)')
    ap.add_argument('--top', type=int, help='airborne sheets: place the highest figure pixel of the sheet at this '
                    'y instead of putting the lowest one on the foot line')
    ap.add_argument('--center', action='store_true', help='centre each figure in its cell instead of keeping its '
                    'place in the slot (wide poses such as lying on the floor would be cut at the cell edge)')
    ap.add_argument('--rear-foot', action='store_true', help='shift every cell so that the rear foot (the '
                    'leftmost figure pixel on the floor) stands where it stands in the first cell - for attacks '
                    'that keep the rear foot planted; generators centre each figure in its slot instead')
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
    scale = a.scale or a.height / (foot - min(tops) + 1)
    if a.area_match:
        from scipy import ndimage as ndi
        m = imf.cells(a.area_match)[0]
        m_area = imf.figure_mask(m).sum()
        lab0, n0 = ndi.label(~bg)
        areas = [0] * a.frames
        for i, sl in enumerate(ndi.find_objects(lab0), start=1):
            cx = (sl[1].start + sl[1].stop) / 2
            areas[min(a.frames - 1, int(cx // slot))] += int((lab0[sl] == i).sum())
        scale = float(np.sqrt(m_area / np.median(areas)))
    if a.top is not None:                      # move the sheet so that its highest pixel lands on --top
        foot = min(tops) - 1 + round((imf.BASELINE + 1 - a.top) / scale)
    out = Image.new('RGB', (imf.CELL * a.frames, imf.CELL), KEY)
    # colour: background replaced by the outline colour, resampled with LANCZOS (no aliasing on large
    # downscales of generator images); figure mask resampled separately, key colour put back outside it
    pad = int(imf.CELL / scale) + 1           # margin, so every cell window lies inside
    col = rgb.copy()
    col[bg] = imf.OUTLINE_RGB
    col = np.pad(col, ((pad, pad), (pad, pad), (0, 0)), mode='edge')
    msk = np.pad((~bg).astype(np.uint8) * 255, pad, mode='constant')
    # each connected part of the figures belongs to the slot of its centre: a kicking foot may reach into
    # the neighbouring slot and must neither be cut off nor appear in the neighbour's cell
    from scipy import ndimage
    lab, nlab = ndimage.label(msk > 0)
    owner = np.zeros(nlab + 1, int)
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        cx = (sl[1].start + sl[1].stop) / 2 - pad
        owner[i] = min(a.frames - 1, max(0, int(cx // slot)))
    src_c = Image.fromarray(col)
    out = Image.new('RGB', (imf.CELL * a.frames, imf.CELL), KEY)
    for k in range(a.frames):
        cx = (k + 0.5) * slot
        if a.center:
            cols = np.nonzero(((lab > 0) & (owner[lab] == k)).any(axis=0))[0] - pad
            cx = (cols.min() + cols.max() + 1) / 2
        # source window that maps onto the 256 x 256 cell
        sx0 = pad + cx - 128 / scale
        sy0 = pad + foot + 1 - (imf.BASELINE + 1) / scale
        box = (sx0, sy0, sx0 + imf.CELL / scale, sy0 + imf.CELL / scale)
        c = np.array(src_c.resize((imf.CELL, imf.CELL), Image.LANCZOS, box=box))
        # only this slot's figure: the cell window can reach into the neighbouring slots
        mk = np.where((lab > 0) & (owner[lab] == k), 255, 0).astype(np.uint8)
        m = np.array(Image.fromarray(mk).resize((imf.CELL, imf.CELL), Image.BOX, box=box)) >= 128
        c[~m] = KEY
        out.paste(Image.fromarray(c), (k * imf.CELL, 0))
    if a.rear_foot:
        arr = np.array(out)
        cellsl = [arr[:, k * imf.CELL:(k + 1) * imf.CELL] for k in range(a.frames)]

        def rear_x(c):
            fg = ~imf.background_mask(c)
            floor = fg[imf.BASELINE - 12:imf.BASELINE + 1]
            return int(np.nonzero(floor.any(axis=0))[0].min())
        ref = rear_x(cellsl[0])
        for k in range(1, a.frames):
            dx = ref - rear_x(cellsl[k])
            if dx:
                c = np.full_like(cellsl[k], KEY)
                if dx > 0:
                    c[:, dx:] = cellsl[k][:, :-dx]
                else:
                    c[:, :dx] = cellsl[k][:, -dx:]
                arr[:, k * imf.CELL:(k + 1) * imf.CELL] = c
                print(f'  cell {k + 1}: shifted {dx:+d} px (rear foot)')
        out = Image.fromarray(arr)
    out.save(a.dst)
    print(f'{a.src}: {W} x {H}, {a.frames} slots of {slot:.0f} px, figures {foot - min(tops) + 1} px high, '
          f'foot line y = {foot}, scale {scale:.3f} -> {a.dst}')


if __name__ == '__main__':
    main()

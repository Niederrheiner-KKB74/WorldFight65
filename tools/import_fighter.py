#!/usr/bin/env python3
"""Import fighter animations from pixel-art sprite sheets (e.g. from an image generator) for WorldFight65.

Sheet format (see docs/art_import.md): one PNG per animation, assets/art/<fighter>/<anim>.png, one row of
square cells (default 256 x 256 px), the figure facing right on a solid magenta (#FF00FF) background, the
soles on a common baseline 16 px above the cell bottom, the figure centred horizontally in its cell.

load_sheet() cuts the cells, removes the magenta background and the magenta-tinted fringe pixels, scales the
figure to the game size (the scale is chosen once per fighter, from his idle sheet, so that it matches the
height of the skeleton-drawn figure and therefore the hit boxes) and places it in the frame canvas of
tools/fighter_art.py with the baseline on the anchor. The result per frame is an RGB image and a mask;
quantise() turns all frames of a fighter into one 15-colour palette (+ transparent).
Run it directly to write a preview: python3 tools/import_fighter.py assets/art/konrad/idle.png
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fighter_art as fa      # noqa: E402

CELL = 256
BASELINE = 239                 # y of the lowest sole pixel inside a cell
OUTLINE_RGB = (24, 16, 20)     # the background is replaced by this before scaling, so edges darken


def background_mask(rgb):
    """magenta background and the magenta-tinted fringe around the figure"""
    r, g, b = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
    pure = (r > 200) & (g < 80) & (b > 200)
    fringe = (r > 140) & (b > 140) & (g < 120) & (np.minimum(r, b) - g > 70)
    return pure | fringe


HOLE_MIN = 40                  # enclosed key-colour areas from this size on are real holes (e.g. arm/body gap)


def split_key(rgb):
    """(background, specks): background = key colour connected to the cell border or forming a real hole;
    specks = small enclosed key-coloured areas inside the figure. Generators paint pink highlights and cord
    stripes in the key colour; those are not transparent but filled from the surrounding colours."""
    key = background_mask(rgb)
    lab, n = ndimage.label(key)
    border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    sizes = ndimage.sum(key, lab, range(n + 1))
    keep = np.zeros(n + 1, bool)
    keep[border] = True
    keep[sizes >= HOLE_MIN] = True
    keep[0] = False
    bg = keep[lab]
    return bg, key & ~bg


def figure_mask(rgb):
    return ~split_key(rgb)[0]


def cells(path, cell=CELL):
    im = Image.open(path).convert('RGB')
    n = im.width // cell
    if im.width % cell or im.height != cell:
        raise ValueError(f'{path}: expected one row of {cell} x {cell} cells, got {im.size}')
    return [np.array(im.crop((k * cell, 0, (k + 1) * cell, cell))) for k in range(n)]


def figure_height(cell_rgb):
    fg = figure_mask(cell_rgb)
    ys = np.nonzero(fg.any(axis=1))[0]
    return BASELINE - int(ys[0]) + 1


def upper_centre_x(fg, baseline=None):
    """mean x of the upper half of a figure mask (head and torso) - the horizontal reference point"""
    ys, xs = np.nonzero(fg)
    if baseline is None:
        baseline = int(ys.max())
    top = ys < ys.min() + 0.5 * (baseline - ys.min())
    return float(xs[top].mean())


def place(cell_rgb, scale, ref_x):
    """scaled figure in the frame canvas: (rgb uint8 [H, W, 3], mask bool [H, W], clipped pixels).
    ref_x is the cell column that lands on the canvas anchor; the baseline lands on the anchor row."""
    bg, specks = split_key(cell_rgb)
    fg = ~bg
    rgb = cell_rgb.copy()
    if specks.any():
        _, (iy, ix) = ndimage.distance_transform_edt(specks | bg, return_indices=True)
        rgb[specks] = cell_rgb[iy[specks], ix[specks]]
    rgb[bg] = OUTLINE_RGB
    size = max(1, round(CELL * scale))
    rgb_s = np.array(Image.fromarray(rgb).resize((size, size), Image.LANCZOS))
    a_s = np.array(Image.fromarray((fg * 255).astype(np.uint8)).resize((size, size), Image.BOX)) >= 128
    out_rgb = np.zeros((fa.FRAME_H, fa.FRAME_W, 3), np.uint8)
    out_m = np.zeros((fa.FRAME_H, fa.FRAME_W), bool)
    ox = fa.ANCHOR[0] - round(ref_x * scale)
    oy = fa.ANCHOR[1] - round(BASELINE * scale)
    for y in range(size):
        ty = oy + y
        if not 0 <= ty < fa.FRAME_H:
            continue
        x0, x1 = max(0, ox), min(fa.FRAME_W, ox + size)
        if x0 >= x1:
            continue
        out_rgb[ty, x0:x1] = rgb_s[y, x0 - ox:x1 - ox]
        out_m[ty, x0:x1] = a_s[y, x0 - ox:x1 - ox]
    clipped = a_s.sum() - out_m.sum()
    return out_rgb, out_m, int(clipped)


def fit(art_dir, ref_idle):
    """Scale and horizontal reference for a fighter, from his idle sheet and the skeleton-drawn idle frame
    ref_idle (index array): the imported figure gets the same height (soles to top of head) and the same
    head/torso position relative to the anchor, so the hit boxes of the fighter module still fit."""
    c0 = cells(art_dir / 'idle.png')[0]
    ref_fg = ref_idle > 0
    ref_h = fa.ANCHOR[1] - int(np.nonzero(ref_fg.any(axis=1))[0][0]) + 1
    scale = ref_h / figure_height(c0)
    ref_dx = upper_centre_x(ref_fg, fa.ANCHOR[1]) - fa.ANCHOR[0]
    ref_x = upper_centre_x(figure_mask(c0), BASELINE) - ref_dx / scale
    return scale, ref_x


def import_anims(art_dir, ref_idle, counts):
    """{anim: [(rgb, mask)]} for every assets/art/<fighter>/<anim>.png; counts = {anim: frames expected}"""
    art_dir = Path(art_dir)
    if not (art_dir / 'idle.png').exists():
        return {}
    scale, ref_x = fit(art_dir, ref_idle)
    out = {}
    for png in sorted(art_dir.glob('*.png')):
        a = png.stem
        if a not in counts:
            raise ValueError(f'{png}: unknown animation {a!r}')
        cs = cells(png)
        if len(cs) != counts[a]:
            raise ValueError(f'{png}: {len(cs)} frames, the fighter module has {counts[a]}')
        frames = []
        for k, c in enumerate(cs):
            rgb, m, clipped = place(c, scale, ref_x)
            if clipped > 20:
                print(f'  warning: {png.name} frame {k}: {clipped} pixels outside the frame canvas')
            frames.append((rgb, m))
        out[a] = frames
    print(f'  imported {", ".join(out)} from {art_dir} (scale {scale:.3f})')
    return out


def quantise(frames_rgbm, colours=15, weights=None):
    """frames_rgbm: [(rgb, mask)] -> (list of index frames (0 = transparent), palette of 16 RGB tuples).
    weights: optional repeat count per frame for the palette choice (imported frames count more than
    skeleton-drawn ones while both are mixed in one fighter)."""
    weights = weights or [1] * len(frames_rgbm)
    pix = np.concatenate([np.repeat(rgb[m], w, axis=0) for (rgb, m), w in zip(frames_rgbm, weights)], axis=0)
    strip = Image.fromarray(pix.reshape(1, -1, 3))
    q = strip.quantize(colors=colours, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    pal = q.getpalette()[:colours * 3]
    palette = [(0, 0, 0)] + [tuple(pal[i * 3:i * 3 + 3]) for i in range(colours)]
    out = []
    for rgb, m in frames_rgbm:
        qi = np.array(Image.fromarray(rgb).quantize(palette=q, dither=Image.Dither.NONE), np.uint8) + 1
        qi[~m] = 0
        out.append(qi)
    return out, palette


if __name__ == '__main__':
    path = Path(sys.argv[1])
    cs = cells(path)
    scale = 97 / figure_height(cs[0])
    ref_x = upper_centre_x(figure_mask(cs[0]), BASELINE)
    frames = [place(c, scale, ref_x) for c in cs]
    idx, pal = quantise([(r, m) for r, m, _ in frames])
    fa.sheet(idx, pal, scale=3, cols=len(idx)).save('/tmp/import_preview.png')
    print(f'{len(cs)} frames, scale {scale:.3f}, clipped {[c for _, _, c in frames]}')

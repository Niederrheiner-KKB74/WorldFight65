#!/usr/bin/env python3
"""Check generator sprite sheets against the fighter's master image before they are imported.

  python3 tools/check_sheets.py FIGHTER [SHEET.png ...]

FIGHTER is the folder name under assets/art (tiago, konrad, ...). The master is assets/art/<fighter>/master.png
(one 256 x 256 cell, the approved standing pose); without it, frame 1 of idle.png is used. Without SHEET
arguments all sheets of the fighter are checked; a SHEET may also be a new file that is not yet in the folder
(its animation is taken from the file name, e.g. konrad_walk_6x256.png -> walk).

Checks per frame (docs/art_import.md): format, frame count, foot line, height, torso width, colours compared
with the master (CIELAB distance), brightness, magenta on the figure; per sheet the jitter between frames of
idle. Prints a report and writes build/preview/check_<fighter>.png (master and all frames, same scale).
Exit code 1 when an error was found.
"""
import importlib
import re
import sys
from pathlib import Path

import warnings

import numpy as np
from PIL import Image, ImageDraw

warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', module='sklearn')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
sys.path.insert(0, str(ROOT / 'assets' / 'source'))
import import_fighter as imf     # noqa: E402

STANDING = {'idle', 'walk', 'block', 'hit', 'lp', 'hp', 'lk', 'hk', 'getup'}
CROUCHING = {'crouch', 'c_block', 'c_lp', 'c_lk', 'sweep'}
CALM = {'idle', 'walk', 'block'}                 # width limit 0.6 x height
AIR = {'jump', 'j_p', 'j_k', 'fall'}             # feet may leave the floor line
CROUCH_H = 150


class Report:
    def __init__(self):
        self.lines, self.errors, self.warnings = [], 0, 0

    def err(self, where, text):
        self.errors += 1
        self.lines.append(f'  FEHLER   {where}: {text}')

    def warn(self, where, text):
        self.warnings += 1
        self.lines.append(f'  Hinweis  {where}: {text}')

    def ok(self, where, text):
        self.lines.append(f'  ok       {where}: {text}')


def measure(cell):
    bg, specks = imf.split_key(cell)
    fg = ~bg
    ys, xs = np.nonzero(fg)
    if not len(ys):
        return None
    top, bot = int(ys.min()), int(ys.max())
    y30 = top + int(0.30 * (bot - top))
    row = np.nonzero(fg[y30])[0]
    lab = imf.to_lab(cell[fg & ~specks])
    return dict(fg=fg, top=top, bot=bot, h=bot - top + 1, w=int(xs.max() - xs.min() + 1),
                chest=int(row.max() - row.min() + 1) if len(row) else 0, area=int(fg.sum()),
                specks=int(specks.sum()), lab=lab, L=float(lab[:, 0].mean()))


def master_colours(m, k=14):
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=k, n_init=4, random_state=1).fit(m['lab'])
    return km.cluster_centers_


def colour_error(lab, centres):
    """mean CIELAB distance of the frame's pixels to the nearest master colour, and the share of pixels
    further away than 15 (colours the master does not have)"""
    d = np.sqrt(((lab[:, None, :] - centres[None]) ** 2).sum(2)).min(1)
    return float(d.mean()), float((d > 15).mean())


def anim_of(path, known):
    stem = path.stem.lower()
    for a in sorted(known, key=len, reverse=True):
        if re.search(rf'(^|_){re.escape(a)}(_|$)', stem):
            return a
    return None


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    fighter = sys.argv[1]
    art = ROOT / 'assets' / 'art' / fighter
    mod = importlib.import_module(f'fighter_{fighter}')
    counts = {a: len(v) for a, v in mod.anims().items()}
    sheets = [Path(p) for p in sys.argv[2:]] or sorted(art.glob('*.png'))
    sheets = [p for p in sheets if p.name != 'master.png']

    mpath = art / 'master.png'
    mcell = imf.cells(mpath)[0] if mpath.exists() else imf.cells(art / 'idle.png')[0]
    m = measure(mcell)
    centres = master_colours(m)
    r = Report()
    print(f'Master: {mpath if mpath.exists() else art / "idle.png (Frame 1)"} - Höhe {m["h"]} px, '
          f'Oberkörper {m["chest"]} px, Helligkeit L {m["L"]:.0f}')

    preview = [('master', mcell)]
    for path in sheets:
        a = anim_of(path, counts)
        name = path.name
        r.lines.append(f'{name} -> {a or "?"}')
        if a is None:
            r.err(name, 'Animation am Dateinamen nicht erkannt')
            continue
        im = Image.open(path).convert('RGB')
        n = counts[a]
        if im.size != (imf.CELL * n, imf.CELL):
            r.warn(name, f'Format {im.size[0]} x {im.size[1]} statt {imf.CELL * n} x {imf.CELL} - '
                         f'mit tools/normalize_sheet.py anpassen')
            continue
        cs = imf.cells(path)
        ms = []
        for k, c in enumerate(cs):
            where = f'{a} Frame {k + 1}'
            f = measure(c)
            if f is None:
                r.err(where, 'leer')
                continue
            ms.append(f)
            preview.append((f'{a}{k + 1}', c))
            if a not in AIR and abs(f['bot'] - imf.BASELINE) > 2:
                r.err(where, f'Fußlinie y = {f["bot"]} statt {imf.BASELINE}')
            if a in ('idle', 'walk', 'block') and abs(f['h'] - m['h']) > (12 if a == 'walk' else 6):
                r.err(where, f'Höhe {f["h"]} px, Master {m["h"]} px (Maßstab?)')
            if a in ('crouch', 'c_block') and abs(f['h'] - CROUCH_H) > 12:
                r.err(where, f'Höhe {f["h"]} px, geduckt etwa {CROUCH_H} px (Maßstab?)')
            if a in CALM:
                if f['w'] > 0.62 * m['h']:
                    r.err(where, f'Breite {f["w"]} px, höchstens {int(0.6 * m["h"])} px')
                dc = f['chest'] / m['chest'] - 1
                if abs(dc) > 0.08 and a in ('idle', 'walk'):     # same arm pose as the master
                    r.err(where, f'Oberkörper {f["chest"]} px, Master {m["chest"]} px ({dc:+.0%})')
            ce, far = colour_error(f['lab'], centres)
            dl = f['L'] - m['L']
            colours = (f'mittlerer Abstand {ce:.1f}, {far:.0%} der Pixel ohne passende Master-Farbe')
            if far > 0.20 or ce > 10:
                r.err(where, f'Farben weichen deutlich vom Master ab ({colours})')
            elif far > 0.08 or ce > 5:
                r.warn(where, f'Farbtöne leicht anders als im Master ({colours}) - kostet Palettenfarben')
            if abs(dl) > 5 and a in ('idle', 'walk'):   # same composition as the master
                r.err(where, f'Helligkeit {dl:+.0f} gegenüber dem Master')
            if f['specks'] > 150:
                r.warn(where, f'{f["specks"]} Magenta-Pixel in der Figur (werden aufgefüllt)')
        if a == 'idle' and len(ms) > 1:
            tops = [f['top'] for f in ms]
            areas = [f['area'] for f in ms]
            if max(tops) - min(tops) > 8:
                r.err(name, f'Kopf springt zwischen den Frames um {max(tops) - min(tops)} px (höchstens 8)')
            elif max(tops) - min(tops) < 3:
                r.warn(name, f'Kopf bewegt sich nur um {max(tops) - min(tops)} px - im Spiel kaum sichtbar '
                             f'(tools/make_idle.py erzeugt das Atmen aus dem Master)')
            if max(areas) / min(areas) - 1 > 0.05:
                r.err(name, f'Figurfläche schwankt um {max(areas) / min(areas) - 1:.0%} (Pulsieren)')
        if not any(l.startswith(('  FEHLER   ' + a + ' ', '  FEHLER   ' + name)) for l in r.lines):
            r.ok(name, f'{n} Frames')

    print('\n'.join(r.lines))
    print(f'{r.errors} Fehler, {r.warnings} Hinweise')

    # overview: all cells at half size, master first, with the foot line and the master's head line
    s = 128
    cols = 8
    rows = (len(preview) + cols - 1) // cols
    out = Image.new('RGB', (cols * s, rows * (s + 12)), (60, 70, 90))
    d = ImageDraw.Draw(out)
    for i, (label, c) in enumerate(preview):
        x, y = (i % cols) * s, (i // cols) * (s + 12)
        cell = c.copy()
        cell[imf.split_key(c)[0]] = (60, 70, 90)
        out.paste(Image.fromarray(cell).resize((s, s), Image.BOX), (x, y + 12))
        d.line((x, y + 12 + imf.BASELINE // 2, x + s - 1, y + 12 + imf.BASELINE // 2), fill=(120, 200, 120))
        d.line((x, y + 12 + m['top'] // 2, x + s - 1, y + 12 + m['top'] // 2), fill=(200, 120, 120))
        d.text((x + 3, y), label, fill=(230, 230, 230))
    dst = ROOT / 'build' / 'preview' / f'check_{fighter}.png'
    dst.parent.mkdir(parents=True, exist_ok=True)
    out.save(dst)
    print(f'Übersicht: {dst}')
    sys.exit(1 if r.errors else 0)


if __name__ == '__main__':
    main()

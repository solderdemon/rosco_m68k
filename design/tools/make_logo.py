"""Generate the SolderDemon logo footprint from images/solderdemon-logo.png, as on the busboard.

The logo is pixel art on a transparent background. The image is cropped to
its opaque pixels, sampled on a grid of CELL source pixels, and every run of
filled cells is merged into rectangles that become fp_poly items on silkscreen.

    python tools/make_logo.py [height_mm] [layer]
"""
import sys
import uuid
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]      # the repository
CELL = 4                      # source pixels per silkscreen cell
NS = uuid.UUID('5d0e7a1c-0000-4000-8000-50d3e7de0000')


def cells(path):
    im = Image.open(path).convert('RGBA')
    im = im.crop(im.getbbox())
    w, h = im.size
    gw, gh = (w + CELL - 1) // CELL, (h + CELL - 1) // CELL
    px = im.load()
    grid = []
    for gy in range(gh):
        row = []
        for gx in range(gw):
            n = on = 0
            for y in range(gy * CELL, min(h, gy * CELL + CELL)):
                for x in range(gx * CELL, min(w, gx * CELL + CELL)):
                    n += 1
                    on += px[x, y][3] >= 128
            row.append(on * 2 >= n)
        grid.append(row)
    return grid


def rects(grid):
    """Horizontal runs, merged downwards while the run below is identical."""
    open_, out = {}, []
    for y, row in enumerate(grid + [[False] * len(grid[0])]):
        runs, x = set(), 0
        while x < len(row):
            if row[x]:
                x0 = x
                while x < len(row) and row[x]:
                    x += 1
                runs.add((x0, x))
            x += 1
        for run in list(open_):
            if run not in runs:
                out.append((run[0], open_.pop(run), run[1], y))
        for run in runs:
            open_.setdefault(run, y)
    return out


def footprint(name, grid, height, layer):
    gh, gw = len(grid), len(grid[0])
    s = height / gh
    ox, oy = gw * s / 2, gh * s / 2
    u = lambda k: str(uuid.uuid5(NS, f'{name}/{k}'))
    lines = [
        f'(footprint "{name}"',
        '\t(version 20260206)',
        '\t(generator "make_logo.py")',
        f'\t(layer "F.Cu")',
        f'\t(descr "SolderDemon logo, {gw * s:.1f} x {height:.1f} mm, generated from logo.png")',
        '\t(tags "logo SolderDemon")',
        f'\t(property "Reference" "LOGO**" (at 0 {-oy - 1:.2f} 0) (layer "F.SilkS") (hide yes) (uuid "{u("ref")}")',
        '\t\t(effects (font (size 1 1) (thickness 0.15))))',
        f'\t(property "Value" "{name}" (at 0 {oy + 1:.2f} 0) (layer "F.Fab") (hide yes) (uuid "{u("val")}")',
        '\t\t(effects (font (size 1 1) (thickness 0.15))))',
        '\t(attr board_only exclude_from_pos_files exclude_from_bom)',
    ]
    for i, (x0, y0, x1, y1) in enumerate(sorted(rects(grid))):
        a, b = x0 * s - ox, y0 * s - oy
        c, d = x1 * s - ox, y1 * s - oy
        lines += [
            f'\t(fp_poly (pts (xy {a:.4f} {b:.4f}) (xy {c:.4f} {b:.4f}) (xy {c:.4f} {d:.4f}) (xy {a:.4f} {d:.4f}))',
            f'\t\t(stroke (width 0) (type solid)) (fill yes) (layer "{layer}") (uuid "{u(i)}"))',
        ]
    lines.append(')')
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    height = float(sys.argv[1]) if len(sys.argv) > 1 else 18.0
    layer = sys.argv[2] if len(sys.argv) > 2 else 'F.SilkS'
    name = 'SolderDemon_Logo'
    grid = cells(ROOT / 'images' / 'solderdemon-logo.png')
    out = ROOT / 'design' / 'kicad' / 'rosco_m68k.pretty' / f'{name}.kicad_mod'
    out.parent.mkdir(exist_ok=True)
    out.write_text(footprint(name, grid, height, layer), encoding='utf-8')
    print(out, f'{len(grid[0])}x{len(grid)} cells, {len(rects(grid))} rects')

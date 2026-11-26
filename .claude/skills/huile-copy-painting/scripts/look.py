"""Put pictures beside the reference, box by box, and measure them by region.

    look.py --ref R A.png [B.png ...] --box x0,y0,x1,y1 [--box ...] [--out O.png]
    look.py --ref R A.png [B.png ...] --regions regions.json

Boxes are in the reference's pixels. With ``--box``, each box of each
picture, cut from it at its own size, and of the reference, are put in a
row, all enlarged to ``--scale`` times the box (2 by default), and the rows
written to ``--out`` (default ``look.png``). With ``--regions`` (a JSON
object of name: [x0, y0, x1, y1]), every picture resized to the reference,
it prints for each region and picture the mean colour, the mean of its
darkest 15%, middle 20% and lightest 15% of pixels, and the spread of its
lightness, then the last picture's lightness minus the reference's on a
16 x 12 grid.
"""

import argparse
import json

import numpy as np
from PIL import Image


def as_array(path, size):
    im = Image.open(path).convert("RGB")
    return np.asarray(im.resize(size, Image.Resampling.LANCZOS), float)


def tones(px):
    """Mean, darks, mids, lights (RGB) and lightness spread of some pixels."""
    light = px.mean(1)
    lo, m0, m1, hi = np.percentile(light, (15, 40, 60, 85))
    return (
        px.mean(0),
        px[light <= lo].mean(0),
        px[(light >= m0) & (light <= m1)].mean(0),
        px[light >= hi].mean(0),
        light.std(),
    )


def rgb(v):
    return "[" + " ".join(f"{c:3.0f}" for c in v) + "]"


def regions(pictures, ref, boxes):
    for name, (x0, y0, x1, y1) in boxes.items():
        print(name)
        for label, im in [*pictures, ("reference", ref)]:
            mean, dark, mid, light, spread = tones(im[y0:y1, x0:x1].reshape(-1, 3))
            print(
                f"  {label:14.14s} mean {rgb(mean)}  dark {rgb(dark)}  "
                f"mid {rgb(mid)}  light {rgb(light)}  spread {spread:3.0f}"
            )
    grid = [
        np.asarray(
            Image.fromarray(im.astype("uint8")).resize((16, 12), Image.Resampling.BOX),
            float,
        ).mean(-1)
        for im in (pictures[-1][1], ref)
    ]
    print(f"lightness, {pictures[-1][0]} minus the reference:")
    for row in grid[0] - grid[1]:
        print(" ".join(f"{v:+4.0f}" for v in row))


def boxes_side_by_side(paths, ref, boxes, out, scale):
    """Each box cut from each picture at its own size, the reference's last,
    all enlarged to ``scale`` times the box."""
    images = [Image.open(p).convert("RGB") for p in paths] + [ref]
    rows = []
    for x0, y0, x1, y1 in boxes:
        size = (round((x1 - x0) * scale), round((y1 - y0) * scale))
        cells = []
        for im in images:
            f = im.width / ref.width  # (this picture's pixels per reference pixel)
            cut = im.crop((round(x0 * f), round(y0 * f), round(x1 * f), round(y1 * f)))
            cells.append(np.asarray(cut.resize(size, Image.Resampling.LANCZOS)))
        rows.append(np.concatenate(cells, axis=1))
    width = max(r.shape[1] for r in rows)
    rows = [np.pad(r, ((0, 4), (0, width - r.shape[1]), (0, 0))) for r in rows]
    Image.fromarray(np.concatenate(rows)).save(out)
    print(out)


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--ref", required=True, help="the reference picture")
    p.add_argument("pictures", nargs="+")
    p.add_argument("--box", action="append", default=[], help="x0,y0,x1,y1")
    p.add_argument("--out", default="look.png")
    p.add_argument("--scale", type=float, default=2.0, help="enlarge the boxes")
    p.add_argument("--regions", help="a JSON file of name: [x0, y0, x1, y1]")
    a = p.parse_args()
    ref_im = Image.open(a.ref).convert("RGB")
    ref = np.asarray(ref_im, float)
    if a.box:
        boxes = [tuple(int(v) for v in b.split(",")) for b in a.box]
        boxes_side_by_side(a.pictures, ref_im, boxes, a.out, a.scale)
    if a.regions:
        pictures = [(path, as_array(path, ref_im.size)) for path in a.pictures]
        with open(a.regions, encoding="utf-8") as f:
            regions(pictures, ref, json.load(f))


if __name__ == "__main__":
    main()

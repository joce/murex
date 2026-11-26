"""Paint thick swatches of an example's mixes and print their rendered RGB.

    swatch.py --script S NAME [NAME=EXPR ...] [--out swatch.png]

A bare NAME is one of the script's module globals (a paint, or a list of
paints, each painted). NAME=EXPR is a new mix, a Python expression over the
script's globals, for instance
``"olive=mix((SAP_GREEN, 2), (YELLOW_OCHRE, 1))"``. Each swatch is painted
three strokes thick on the script's canvas surface (``CANVAS``) and rendered
without relief or gloss, so its number is the paint's own colour.
"""

import argparse
import os

import numpy as np
from PIL import Image
from stages import load

from murex.huile import Canvas

SIZE = 70


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--script", required=True, help="the example painting's script")
    p.add_argument("paints", nargs="+")
    p.add_argument("--out", default="swatch.png")
    a = p.parse_args()
    module = load(a.script)
    names, paints = [], []
    for item in a.paints:
        name, _, expr = item.partition("=")
        value = eval(expr or name, vars(module))  # (the user's own expression)
        if isinstance(value, list | tuple):
            names += [f"{name}[{i}]" for i in range(len(value))]
            paints += list(value)
        else:
            names.append(name)
            paints.append(value)
    surface = getattr(module, "CANVAS", None)
    kw = {"surface": surface} if surface is not None else {}
    canvas = Canvas(SIZE * len(paints), SIZE, seed=1, **kw)
    for i, paint in enumerate(paints):
        for y in (20, 35, 50):
            pts = [(i * SIZE + 8, y), (i * SIZE + SIZE - 8, y)]
            canvas.stroke(pts, paint, width=20, amount=12, pressure=0.6)
    canvas.save(a.out, relief=0.0, gloss=0.0)
    px = np.asarray(Image.open(a.out).convert("RGB"), float)
    for i, name in enumerate(names):
        mean = px[25:45, i * SIZE + 20 : i * SIZE + 50].reshape(-1, 3).mean(0)
        print(f"{name:24s} {mean.round().astype(int)}")
    print(os.path.abspath(a.out))


if __name__ == "__main__":
    main()

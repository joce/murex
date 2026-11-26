"""Paint some stages of an example painting, saving the canvas after each.

    stages.py --script S --ref R --work WORK START END NAME

paints STAGES[START:END] of the example script S, starting from
WORK/snap/<START-1>.pkl (from a blank canvas when START is 0), saves the canvas
after each stage as WORK/snap/<i>.pkl, the picture as WORK/NAME.png and, beside
the reference R, as WORK/cmp_NAME.png. It prints the mean colour error over a
16 x 12 grid, and the grid itself: a guide, not a judge.

The script must keep its stages in a list ``STAGES`` and its canvas in a
module global ``canvas`` (and its random generator, if any, in ``rng``), and
may set ``RELIEF`` and ``GLOSS`` for how it is lit.
"""

import argparse
import importlib.util
import os
import pickle
import sys
import time

import numpy as np
from PIL import Image


def load(script):
    """Import an example script by its path."""
    path = os.path.abspath(script)
    sys.path.insert(0, os.path.dirname(path))
    name = os.path.splitext(os.path.basename(path))[0]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader, f"cannot import {path}"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def save(module, png):
    """The picture, lit as the example lights it."""
    module.canvas.save(
        png, relief=getattr(module, "RELIEF", 0.25), gloss=getattr(module, "GLOSS", 0.0)
    )


def compare(png, ref, out):
    """Write the picture beside the reference; print the 16 x 12 grid error."""
    b = Image.open(ref).convert("RGB")
    a = Image.open(png).convert("RGB").resize(b.size, Image.Resampling.LANCZOS)
    side = Image.new("RGB", (2 * b.width, b.height))
    side.paste(a, (0, 0))
    side.paste(b, (b.width, 0))
    side.save(out)
    sa = np.asarray(a.resize((16, 12), Image.Resampling.BOX), float)
    sb = np.asarray(b.resize((16, 12), Image.Resampling.BOX), float)
    err = np.abs(sa - sb).mean(-1)
    print(f"{out}  mean error {err.mean():.1f}")
    for row in err:
        print(" ".join(f"{v:3.0f}" for v in row))


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--script", required=True, help="the example painting's script")
    p.add_argument("--ref", required=True, help="the reference picture")
    p.add_argument("--work", default=".", help="where snapshots and pictures go")
    p.add_argument("start", type=int)
    p.add_argument("end", type=int)
    p.add_argument("name")
    a = p.parse_args()
    module = load(a.script)
    snap = os.path.join(a.work, "snap")
    os.makedirs(snap, exist_ok=True)
    if a.start > 0:
        with open(os.path.join(snap, f"{a.start - 1}.pkl"), "rb") as f:
            module.canvas, rng = pickle.load(f)
        if rng is not None:
            module.rng = rng
    t0 = time.time()
    for i in range(a.start, a.end):
        module.STAGES[i]()
        tmp = os.path.join(snap, f"{i}.pkl.tmp")
        with open(tmp, "wb") as f:
            pickle.dump((module.canvas, getattr(module, "rng", None)), f)
        os.replace(tmp, os.path.join(snap, f"{i}.pkl"))
    png = os.path.join(a.work, f"{a.name}.png")
    save(module, png)
    print(f"{png}: {time.time() - t0:.0f}s")
    compare(png, a.ref, os.path.join(a.work, f"cmp_{a.name}.png"))


if __name__ == "__main__":
    main()

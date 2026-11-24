"""Measure three things a painting knife does over wet paint, for the issues on them.

    python tools/huile/knife_probe.py ribs           # the ribs a dragging knife leaves
    python tools/huile/knife_probe.py skim           # what a knife barely touching lays
    python tools/huile/knife_probe.py lumps          # lumps dropped along a ridge
    python tools/huile/knife_probe.py lumps --step 2    # its pulls in steps of 2 px
    python tools/huile/knife_probe.py ribs --save DIR   # also keep the pictures
    python tools/huile/knife_probe.py ribs --finer 2    # in steps half as long
    python tools/huile/knife_probe.py skim --base 1     # over a thinner dark base
    python tools/huile/knife_probe.py skim --step 2     # white cut into steps of 2 px

``ribs`` (murex-sdz, murex-bja): white knifed across a thick wet dark at
pressure 0.25 leaves ribs parallel to the blade. The table gives how thick
the wet paint lies under the stroke, the ripple of that thickness along the
stroke (root mean square about its running mean) and the ripple's strongest
period, for a runny, a tube and a stiff dark, and again with the stage that
drags the film under the blade (``_knife._drag_film``) switched off. The
period was the step of the stroke: 8 px for a blade this long (``spacing`` in
``murex/huile/stroke.py``). A stroke must not show how it is cut into steps:
``--finer K`` cuts the white pull into steps K times shorter, and the table
should stay much as it is (the ripple left is the base's own, and the slow
waver of the blade, half a blade apart). ``--step S`` cuts it instead into
steps of S px at most, as a stroke would with ``_MAX_STEP`` of
``murex/huile/stroke.py`` at S rather than 8. Either way the pull has the
textures it has in its own steps (the wobble of its width, the tilt of its
blade, its bands and its nicks: they are drawn against the distance along
the path, as many random numbers as the stroke in its own steps calls for,
murex-9t4).

``skim`` (murex-iaa, murex-dnj): white knifed over a wet dark at a light
touch, for some pressures and loads. The table gives the volume each stroke
left on the canvas: at a given touch it rises with the load, then levels
off once the bead is full. (At the
lightest touch, more paint on the blade left less of a mark, down to nothing
at loads 1 and 3: its bead hung from the level the blade's whole film held
it up at, murex-iaa.) The dark base of the default (``--base 5``) covers the
canvas; a thin one (``--base 1``) runs out below the first row of pulls,
which lie over the bare canvas.

``lumps`` (murex-6fa): the dark ground the other two paint on, alone. Each
of its pulls (a knife 160 px long loaded with ``--base``, at pressure 0.7)
runs along the ridge the one before left at its blade's end, and bulldozes
it. The table gives, for a runny and a stiff dark on a small canvas and on a
larger one, how many pixels hold more than 8 units of wet paint (the ground
is 2 to 3.5 thick, the beads along the pulls' edges up to 8), the thickest,
and the peaks: how many pixels stand more than 3 units above all that lies
on a ring 8 px around them, and the tallest (see ``standing_alone``: a ridge
is no peak). There were lumps up to 13 units thick, where a pull dropped the heap
it was pushing; there should be none. ``--step S`` cuts the ground's pulls
into steps of S px at most (their textures are the same at every cut).

All three paint with fixed seeds, so the same code prints the same numbers.
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from murex import spline
from murex.huile import Brush, Canvas, Paint, _knife, brushes, stroke
from murex.huile import palette as P

DARK = "#1c1a24"
BASE_KNIFE = brushes.knife("straight", 160, flex=0.5)
SNOW_KNIFE = brushes.knife("straight", 110, flex=0.5)
# the blade lies across the pull, as snow is laid: the pulls below run down
# and to the right, about 36 degrees under the horizontal
ACROSS = -54


def dark_base(canvas: Canvas, load: float, body: float | None = None) -> None:
    """A wet dark ground: vertical pulls of a wide knife, side by side."""
    paint = Paint(DARK, body=body)
    for x in range(60, canvas.width + 120, 120):
        knife = Brush(BASE_KNIFE).load(paint, load)
        canvas.stroke(
            [(x, 10), (x, canvas.height - 10)],
            None,
            brush=knife,
            angle=0,
            follow_path=False,
            pressure=0.7,
            lift=0.0,
        )


class Finer(spline.Path):
    """A path sampled ``k`` times as finely as a stroke asks."""

    def __init__(self, points, k: int):
        self.path, self.k = spline.as_path(points), k
        self.n_knots = self.path.n_knots

    def _dense(self):
        return self.path._dense()

    def sample(self, spacing):
        return self.path.sample(spacing / self.k)


def pull(
    canvas: Canvas,
    start,
    load: float,
    pressure: float,
    finer: int = 1,
    step: float | None = None,
) -> None:
    """One pull of white, 270 px long, the blade across it (cut into steps
    ``finer`` times shorter than a stroke's, and of ``step`` px at most)."""
    x, y = start
    knife = Brush(SNOW_KNIFE).load(P.TITANIUM_WHITE, load)
    path = [(x, y), (x + 110, y + 80), (x + 220, y + 160)]
    longest = stroke._MAX_STEP
    if step is not None:
        stroke._MAX_STEP = step
    try:
        canvas.stroke(
            Finer(path, finer) if finer > 1 else path,
            None,
            brush=knife,
            angle=ACROSS,
            follow_path=False,
            pressure=pressure,
            lift=0.0,
        )
    finally:
        stroke._MAX_STEP = longest


def along_the_pull(thickness: np.ndarray, start, band: int = 14) -> np.ndarray:
    """``thickness`` along a pull from ``start``, averaged over a band along
    the blade (the ribs run that way), a sample per pixel of its middle part."""
    d = np.array([110.0, 80.0])
    d /= np.linalg.norm(d)
    n = np.array([-d[1], d[0]])
    values = []
    for t in np.arange(60.0, 230.0):
        centre = np.asarray(start, float) + t * d + 15.0 * n
        across = [centre + o * n for o in np.arange(-band, band + 1.0)]
        values.append(
            np.mean([thickness[int(round(y)), int(round(x))] for x, y in across])
        )
    return np.array(values)


def ripple(values: np.ndarray) -> tuple[float, float]:
    """The ripple of ``values`` about their 17 px running mean: its root mean
    square and its strongest period (px)."""
    wave = (values - np.convolve(values, np.ones(17) / 17, "same"))[20:-20]
    spectrum = np.abs(np.fft.rfft(wave * np.hamming(len(wave))))
    k = int(spectrum[2:].argmax()) + 2
    return float(wave.std()), len(wave) / k


def ribs(args: argparse.Namespace) -> None:
    print(f"{'dark body':>9}  {'film drag':>9}  {'wet':>5}  {'ripple':>6}  period")
    drag_film = _knife._drag_film
    try:
        for body in (0.2, 0.7, 1.0):
            for drag in (True, False):
                _knife._drag_film = drag_film if drag else lambda *_a, **_k: None
                canvas = Canvas(420, 300, seed=1)
                dark_base(canvas, args.base, body)
                pull(canvas, (90, 50), 0.3, 0.25, args.finer, args.step)
                values = along_the_pull(canvas.wet_thickness, (90, 50))
                rms, period = ripple(values)
                print(
                    f"{body:9.1f}  {'on' if drag else 'off':>9}  "
                    f"{values.mean():5.2f}  {rms:6.3f}  {period:4.1f} px"
                )
                if args.save:
                    name = f"ribs_body{body}_{'drag' if drag else 'plain'}.png"
                    canvas.save(os.path.join(args.save, name))
    finally:
        _knife._drag_film = drag_film


def skim(args: argparse.Namespace) -> None:
    pressures = (0.03, 0.08, 0.15, 0.25)
    loads = (0.3, 1.0, 3.0, 8.0)
    canvas = Canvas(1400, 900, seed=1)
    dark_base(canvas, args.base)
    print("volume left on the canvas by each pull")
    print(f"{'pressure':>8}  " + "  ".join(f"load {a:<4}" for a in loads))
    for i, pressure in enumerate(pressures):
        row = []
        for j, load in enumerate(loads):
            before = float(canvas.wet_thickness.sum())
            pull(
                canvas,
                (60 + j * 340, 40 + i * 215),
                load,
                pressure,
                args.finer,
                args.step,
            )
            row.append(float(canvas.wet_thickness.sum()) - before)
        print(f"{pressure:8.2f}  " + "  ".join(f"{v:9.1f}" for v in row))
    if args.save:
        canvas.save(os.path.join(args.save, "skim.png"))


def standing_alone(thickness: np.ndarray, r: int = 8) -> np.ndarray:
    """How far each pixel of ``thickness`` stands above the highest of the
    pixels on a ring ``r`` px around it (32 of them, a pixel apart or so):
    next to nothing along a ridge, whichever way it runs, the height of a
    peak that stands alone."""
    h, w = thickness.shape
    padded = np.pad(thickness, r, mode="edge")
    high = np.full(thickness.shape, -np.inf)
    turns = 2.0 * np.pi * np.arange(32) / 32
    ring = {(int(round(r * np.sin(a))), int(round(r * np.cos(a)))) for a in turns}
    for dy, dx in sorted(ring):
        high = np.maximum(high, padded[r + dy :, r + dx :][:h, :w])
    return thickness - high


def lumps(args: argparse.Namespace) -> None:
    print(f"{'canvas':>8}  {'dark body':>9}  {'over 8':>6}  {'thickest':>8}  peaks")
    longest = stroke._MAX_STEP
    if args.step is not None:
        stroke._MAX_STEP = args.step
    try:
        for width, height in ((420, 300), (900, 500)):
            for body in (0.2, 0.7):
                canvas = Canvas(width, height, seed=1)
                dark_base(canvas, args.base, body)
                wet = canvas.wet_thickness
                alone = standing_alone(wet)
                size, over = f"{width}x{height}", int((wet > 8).sum())
                print(
                    f"{size:>8}  {body:9.1f}  {over:6d}  {wet.max():8.2f}  "
                    f"{int((alone > 3).sum())} px, the tallest {alone.max():.2f} "
                    "above what lies around it"
                )
                if args.save:
                    name = f"lumps_{width}x{height}_body{body}.png"
                    canvas.save(os.path.join(args.save, name))
    finally:
        stroke._MAX_STEP = longest


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("probe", choices=("ribs", "skim", "lumps"))
    parser.add_argument(
        "--base",
        type=float,
        default=5.0,
        help="the load of each pull of the dark base (5: 2 to 3 units thick)",
    )
    parser.add_argument(
        "--finer",
        type=int,
        default=1,
        metavar="K",
        help="cut each white pull into steps K times shorter",
    )
    parser.add_argument(
        "--step",
        type=float,
        metavar="S",
        help="cut each white pull (lumps: each pull of the ground) into "
        "steps of S px at most (a stroke's: 8)",
    )
    parser.add_argument("--save", metavar="DIR", help="keep the pictures in DIR")
    args = parser.parse_args()
    if args.save:
        os.makedirs(args.save, exist_ok=True)
    {"ribs": ribs, "skim": skim, "lumps": lumps}[args.probe](args)


if __name__ == "__main__":
    main()

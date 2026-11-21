"""Measure two things a painting knife does over wet paint, for the issues on them.

    python tools/huile/knife_probe.py ribs           # the ribs a dragging knife leaves
    python tools/huile/knife_probe.py skim           # what a knife barely touching lays
    python tools/huile/knife_probe.py ribs --save DIR   # also keep the pictures
    python tools/huile/knife_probe.py skim --base 1     # over a thinner dark base

``ribs`` (murex-sdz, murex-bja): white knifed across a thick wet dark at
pressure 0.25 leaves ribs parallel to the blade. The table gives how thick
the wet paint lies under the stroke, the ripple of that thickness along the
stroke (root mean square about its running mean) and the ripple's strongest
period, for a runny, a tube and a stiff dark, and again with the stage that
drags the film under the blade (``_knife._drag_film``) switched off. The
period is the step of the stroke: 8 px for a blade this long (``spacing`` in
``murex/huile/stroke.py``). To see the ribs follow the step, halve that cap
there and run this again.

``skim`` (murex-iaa, murex-dnj): white knifed over a wet dark at a light
touch, for some pressures and loads. The table gives the volume each stroke
left on the canvas: at a given touch it rises with the load, then levels
off once the bead is full. (At the
lightest touch, more paint on the blade left less of a mark, down to nothing
at loads 1 and 3: its bead hung from the level the blade's whole film held
it up at, murex-iaa.) The dark base of the default (``--base 5``) covers the
canvas; a thin one (``--base 1``) runs out below the first row of pulls,
which lie over the bare canvas.

Both paint with fixed seeds, so the same code prints the same numbers.
"""

from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from murex.huile import Brush, Canvas, Paint, _knife, brushes
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


def pull(canvas: Canvas, start, load: float, pressure: float) -> None:
    """One pull of white, 270 px long, the blade across it."""
    x, y = start
    knife = Brush(SNOW_KNIFE).load(P.TITANIUM_WHITE, load)
    canvas.stroke(
        [(x, y), (x + 110, y + 80), (x + 220, y + 160)],
        None,
        brush=knife,
        angle=ACROSS,
        follow_path=False,
        pressure=pressure,
        lift=0.0,
    )


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
                pull(canvas, (90, 50), 0.3, 0.25)
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
            pull(canvas, (60 + j * 340, 40 + i * 215), load, pressure)
            row.append(float(canvas.wet_thickness.sum()) - before)
        print(f"{pressure:8.2f}  " + "  ".join(f"{v:9.1f}" for v in row))
    if args.save:
        canvas.save(os.path.join(args.save, "skim.png"))


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("probe", choices=("ribs", "skim"))
    parser.add_argument(
        "--base",
        type=float,
        default=5.0,
        help="the load of each pull of the dark base (5: 2 to 3 units thick)",
    )
    parser.add_argument("--save", metavar="DIR", help="keep the pictures in DIR")
    args = parser.parse_args()
    if args.save:
        os.makedirs(args.save, exist_ok=True)
    {"ribs": ribs, "skim": skim}[args.probe](args)


if __name__ == "__main__":
    main()

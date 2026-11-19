"""Verify the installed wheel: it is imported from the environment (not the
source checkout), it knows its version, its compiled colour science mixes,
fusain's compiled engine draws and huile's paints.

Run through ``uv run tox -e wheel``.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import numpy as np

import murex
from murex import CatmullRom, mix_colors
from murex.spectral import N_BANDS, km_layer, parse_color

assert Path(murex.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
assert not Path.cwd().joinpath("pyproject.toml").exists()
assert murex.__version__ != "0.0.0+unknown", murex.__version__
for name in murex.__all__:
    assert getattr(murex, name) is not None, name

# blue and yellow make green: the spectra mix
r, g, b = parse_color(mix_colors(["#1b3fa0", "#f5d000"]))
assert g > r and g > b, (r, g, b)

# the numba kernels compile: a batch of layers, and a path sampled
empty = km_layer(np.zeros((3, N_BANDS)), np.zeros(3), np.full((3, N_BANDS), 0.5))
assert (empty == 0.5).all(), empty
points, tangents, u, _ = CatmullRom([(0, 0), (30, 40)]).sample(1.0)
assert len(points) == 51 and u[-1] == 1.0, (len(points), u[-1])

# importing murex has loaded no medium
assert not any(name.startswith(("murex.fusain", "murex.huile")) for name in sys.modules)

fusain = importlib.import_module("murex.fusain")

for name in fusain.__all__:
    assert getattr(fusain, name) is not None, name

# a pencil line across a small sheet: the numba engine compiles and draws
sheet = fusain.Sheet(120, 80, seed=1)
laid = sheet.stroke([(10, 40), (110, 40)], fusain.pencils.B2, pressure=0.8, width=4)
image = sheet.render(lighting=False)
assert laid > 0 and image.shape == (80, 120, 3), (laid, image.shape)
assert image[38:42, 20:100].mean() < image[:20].mean() - 0.1

huile = importlib.import_module("murex.huile")
for name in huile.__all__:
    assert getattr(huile, name) is not None, name

# a red stroke across a small canvas: the numba engine compiles and paints
canvas = huile.Canvas(120, 80, seed=1)
red = huile.palette.CADMIUM_RED
canvas.stroke([(10, 40), (110, 40)], paint=red, amount=6, width=20)
image = canvas.render()
assert image.shape == (80, 120, 3), image.shape
r, g, b = image[40, 60]
assert r > g + 0.2 and r > b + 0.2, (r, g, b)
print(f"murex {murex.__version__}: the wheel imports, mixes, draws and paints.")

"""Verify the installed wheel: it is imported from the environment (not the
source checkout), it knows its version, and its compiled colour science
mixes.

Run through ``uv run tox -e wheel``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import murex
from murex import mix_colors
from murex.spectral import parse_color

assert Path(murex.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
assert not Path.cwd().joinpath("pyproject.toml").exists()
assert murex.__version__ != "0.0.0+unknown", murex.__version__
for name in murex.__all__:
    assert getattr(murex, name) is not None, name

# blue and yellow make green: the numba kernels compile and the spectra mix
r, g, b = parse_color(mix_colors(["#1b3fa0", "#f5d000"]))
assert g > r and g > b, (r, g, b)
print(f"murex {murex.__version__}: the installed wheel imports and mixes.")

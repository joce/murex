# murex

[![CI](https://github.com/joce/murex/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/joce/murex/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/joce/murex/graph/badge.svg)](https://codecov.io/gh/joce/murex)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![GitHub License](https://img.shields.io/github/license/joce/murex)](https://github.com/joce/murex/blob/main/LICENSE)

What simulations of artists' media share. The murex is the sea snail Tyrian
purple was made from; this is where [oilpaint](https://github.com/joce/oilpaint)
and [fusain](https://github.com/joce/fusain) get their colour.

- `Pigment` and `murex.spectral`: colours as pigments that mix like the real
  thing (blue and yellow give green, not grey), using spectral Kubelka-Munk
  theory over 24 bands.
- `Bezier`, `CatmullRom`, `Polyline`: stroke paths resampled by arc length,
  and values that vary along a stroke.
- `murex.noise`: textures (paper, weaves, wood grain).
- `Reference`: a reference image, asked for its colour, direction and detail
  at the scale of the tool in hand.
- `write_png` and `murex.filters`: output and small image filters.

```python
from murex import Pigment, mix_colors

mix_colors(["#1b3fa0", "#f5d000"])        # a green
glaze = Pigment("#8e1b2c", opacity=0.3)   # a transparent crimson
glaze.appearance(thickness=1.0, over="#f2c80f")
```

A picture is many layers at once. `murex.spectral.km_layer` works out a batch
of them in compiled code, each over one ground or over a ground of its own
(what is already seen at that pixel), and gives to the last bit what numpy
gives for the same layers one by one:

```python
from murex import spectral as sp

# kappa (pixels, bands) and sigma (pixels,): K and S times the thickness there
seen = sp.km_layer(kappa, sigma, paper)       # over one ground, (bands,)
seen = sp.km_layer(kappa, sigma, seen)        # over what is seen at each pixel
sp.km_layer(kappa, sigma, seen, out=seen)     # the same, in place
```

A path works out its dense points once, however often it is sampled and asked
its length, and again if its control points are changed:

```python
from murex import CatmullRom

path = CatmullRom([(10, 10), (60, 40), (120, 20)])
points, tangents, u, knot = path.sample(0.5)  # every half pixel along it
path.length
```

## Development

```bash
uv sync --group dev --frozen   # install the package and the development tools
uv run pytest                  # run the tests
make pre-push                  # lint, types, the tests under coverage, spelling
make tox                       # every Python version and the built wheel, as CI runs them
```

## License

[MIT](LICENSE)

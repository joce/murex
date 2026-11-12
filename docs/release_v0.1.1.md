## Overview

murex 0.1.1 is the first release: what simulations of artists' media share, taken out of [oilpaint](https://github.com/joce/oilpaint) so that [fusain](https://github.com/joce/fusain) (drawing with dry media) can be built on the same ground.

## Highlights

- **Pigments that mix like the real thing.** `Pigment` and `murex.spectral`: spectral Kubelka-Munk optics over 24 bands. Blue and yellow make green, glazes stay transparent, white tints and black shades.
- **Stroke paths.** `Bezier`, `CatmullRom` and `Polyline`, resampled by arc length, and values that vary along a stroke.
- **Textures.** `murex.noise`: paper, weaves, wood grain, value and fractal noise, all repeatable from a seed.
- **Reference images.** `Reference` reads colour, value and the direction of the forms from an image at any scale.
- **Output.** `write_png`, and small image filters in `murex.filters`.

The numbers are the same as oilpaint's: these modules are its own, unchanged.

Python 3.11 to 3.15. Install with `pip install murex`.

There is no 0.1.0: an unrelated project that once had this name on PyPI used that version number in 2017, and PyPI never lets a file name be used twice.

**Full Changelog:** https://github.com/joce/murex/commits/v0.1.1

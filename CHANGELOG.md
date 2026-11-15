# Changelog

All notable changes to this project are documented in this file.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- **Breaking, for anyone on NumPy 1.x:** NumPy 1.x is no longer supported. The
  requirement is `numpy>=2.0`, and numba's floor rises with it, from
  `numba>=0.57` to `numba>=0.60` (numba 0.57 to 0.59 do not support NumPy 2).
  The reason: `spectral.srgb_to_reflectance` returned different numbers under
  NumPy 1.26.4 and under NumPy 2.5.5 (same Python 3.12, numba 0.68.1 and
  murex 0.2.0; the reflectance of a colour hashed differently), and two
  libraries depend on these numbers, one of which checks its pictures byte for
  byte. CI and the lock only ever ran NumPy 2. No result under NumPy 2
  changes.

## [0.2.0] - 2026-11-15

Faster, with every result as it was: nothing here is a breaking change. What
`spectral` and `spline` return is the same to the last bit as in 0.1.1 for the
same arguments, which `tests/test_exact.py` checks against the code of 0.1.1.

### Added

- `spectral.km_layer` works out a batch of layers in compiled code: `kappa`
  (..., bands) and `sigma` (...) float64 arrays of two dimensions or more,
  over one ground (bands,) or over a ground for each layer (..., bands), as
  when every pixel of a picture has its own layer over what is already seen
  there. Five to six times as fast as numpy for a sheet of 1120 by 820
  pixels. Any other arguments are worked out by numpy, as before.
- `spectral.km_layer(..., out=)`: an array to put the result in, which may be
  the ground itself (a layer laid over what is seen, in place).

### Changed

- A `Path` works out its dense points once, at the first `sample()` or
  `length`, and keeps them; they were worked out at every call. It works
  them out again if its control points (or `alpha`, or `closed`) change, in
  place or not; a path whose `alpha` is an array keeps nothing. A subclass
  that implements `_dense` in its own way says what
  its dense points depend on in `_state`, or they are worked out at every
  call, as before.
- The dense points of a `CatmullRom`, the lengths along a path and the
  tangents of `sample()` are worked out in compiled code. Sampling the path
  of a short stroke and asking its length takes a tenth of the time.
- Where numpy warned of a result that is not a number (layers that are not
  finite, a Catmull-Rom path whose knots run into each other), the compiled
  code gives the same result without the warning.

## [0.1.1] - 2026-11-12

The first release. There is no 0.1.0: an unrelated project that once had this
name on PyPI used that version number in 2017, and PyPI never lets a file name
be used twice.

### Added

- The modules oilpaint and fusain share, taken from oilpaint as they are:
  `spectral` (colour science and Kubelka-Munk mixing), `spline` (stroke paths
  and profiles), `noise` (textures), `reference` (reference images), `png`
  and `filters` (oilpaint's `_filters`, with public names).
- `Pigment`: oilpaint's `Paint` without what is particular to oil paint
  (its body).

[Unreleased]: https://github.com/joce/murex/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/joce/murex/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/joce/murex/releases/tag/v0.1.1

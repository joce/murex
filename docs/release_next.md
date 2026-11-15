# Release notes (next)

Draft the notes of the next release here; see `RELEASING.md`.

## Faster layers and paths, the numbers unchanged

fusain had made its drawings faster by working round murex in two places.
Both now belong to murex, so that oilpaint gets them too. Nothing murex
returns has changed: for the same arguments, `spectral` and `spline` give the
same results as 0.1.1 to the last bit, and `tests/test_exact.py` holds them
to it against the code of 0.1.1.

- **A layer over a ground for each pixel, compiled.** `spectral.km_layer`
  works out a batch of layers (`kappa` (..., bands), `sigma` (...), float64)
  in compiled code, over one ground or over a ground for each layer: what a
  render does when it lays the pigment of every pixel over what is already
  seen there. Five to six times as fast as numpy on a sheet of 1120 by 820
  pixels. `out=` puts the result in an array that is given, which may be the
  ground itself.
- **A path works out its dense points once.** `sample()` and `length` each
  worked them out; a stroke asks for both. They are now kept, and worked out
  again if the control points change. The dense points of a `CatmullRom`,
  the lengths along the path and the tangents are compiled as well: the
  path of a short stroke is sampled in a tenth of the time.

fusain can drop its own compiled Kubelka-Munk (`km_depth`, `km_over`) and its
`_Dense` path once it requires this release.

# Release notes (next)

Draft the notes of the next release here; see `RELEASING.md`.

## murex.fusain: drawing with dry media

murex is becoming one package for every medium. The first to arrive is
fusain, until now a library of its own built on murex (and never released):
graphite and coloured pencils, charcoal, pastels, wax crayons and ballpoint
pens on a paper with tooth, with stumps, erasers, a knife and fixative.
`from murex.fusain import Sheet, papers, pencils`; see
`docs/fusain/README.md`. `import murex` alone does not load it.

## Breaking: NumPy 2 is required

NumPy 1.x is no longer supported: murex requires `numpy>=2.0` and
`numba>=0.60` (the first numba that supports NumPy 2). Under NumPy 1.26.4 and
NumPy 2.5.5, `spectral.srgb_to_reflectance` returned different numbers, and
the numbers must not depend on which NumPy is installed. No result under
NumPy 2 changes.

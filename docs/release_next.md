# Release notes (next)

Draft the notes of the next release here; see `RELEASING.md`.

## murex.fusain: drawing with dry media

murex is becoming one package for every medium. The first to arrive is
fusain, until now a library of its own built on murex (and never released):
graphite and coloured pencils, charcoal, pastels, wax crayons and ballpoint
pens on a paper with tooth, with stumps, erasers, a knife and fixative.
`from murex.fusain import Sheet, papers, pencils`; see
`docs/fusain/README.md`. `import murex` alone does not load it.

## murex.huile: oil painting

oilpaint moves in too, as `murex.huile`: `from murex.huile import Canvas,
Paint`; see `docs/huile/README.md`. It is oilpaint 0.1.0 and everything
oilpaint gained since, which was never released under that name:
`docs/huile/release_since_0.1.0.md` has those notes (impasto with the
structure of oil paint, new lighting, stippling and spatter, reverse glass
painting, strokes off the edge, clear errors, speed). `pip install oilpaint`
still gives 0.1.0, which is not updated any more.

## Breaking, in the last bits: the colours are the same on every machine

The colour science no longer depends on how NumPy, the BLAS or the processor
rounds: its powers, roots, `exp` and `tanh` are murex's own, made of plain
arithmetic, and its sums are taken in a fixed order. Every result moves in its
last bits (at most 2e-12 relative); no colour changes on the 0..255 scale.
Drawings come out the same image for image; of the oil paintings, 9 images
change, in at most 7 pixels each, by 1/255.

## Breaking, in the last bits: every picture is the same on every machine

Not only the colours: the strokes, the noise of papers and canvases, the
random choices of a shading or a spatter, and the lighting of a painting no
longer depend on the C library, NumPy or the processor. murex computes its
sines, logarithms, powers and arc tangents itself, with plain arithmetic,
and draws its normal numbers by NumPy's own algorithm, so the random
choices are those NumPy made. Every result moves in its last bits; of the
39 example images, 34 come out byte for byte as they were, and the other 5
in specks (at most 0.14% of the pixels of one). CI now checks the pictures
to the bit on ARM and on Windows.

## Breaking, in fusain's drawings: a path's points no longer hang on a last bit

How many points a path is cut into, and how many numbers a noise draws, were
worked out from ratios that rounding leaves a hair either side of a whole
number: a line 1500 px long sampled every 2.5 px could come out as 601 points
or as 602. A ratio within 1e-6 of a whole number now counts as that number
(oilpaint's fix, now shared). Oil paintings are unchanged. Drawings change
where a stroke's length was a whole number of steps: of fusain's 16 example
images, 4 change, by less than half a percent of their pixels.

## Breaking: NumPy 2 is required

NumPy 1.x is no longer supported: murex requires `numpy>=2.0` and
`numba>=0.60` (the first numba that supports NumPy 2). Under NumPy 1.26.4 and
NumPy 2.5.5, `spectral.srgb_to_reflectance` returned different numbers, and
the numbers must not depend on which NumPy is installed. No result under
NumPy 2 changes.

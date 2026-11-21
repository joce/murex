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

## Breaking, in fusain's drawings: a path's points no longer hang on a last bit

How many points a path is cut into, and how many numbers a noise draws, were
worked out from ratios that rounding leaves a hair either side of a whole
number: a line 1500 px long sampled every 2.5 px could come out as 601 points
or as 602. A ratio within 1e-6 of a whole number now counts as that number
(oilpaint's fix, now shared). Oil paintings are unchanged. Drawings change
where a stroke's length was a whole number of steps: of fusain's 16 example
images, 4 change, by less than half a percent of their pixels.

## Breaking, in oil paintings: a knife's stroke no longer shows its steps

A knife dragged across thick wet paint left a fine rib at every step of its
stroke (every 8 px for a wide blade), both in the paint it dragged and in the
film it laid over it. It no longer does: the wet paint under the blade moves
the same whichever of its two layers holds it, and the blade lays its paint
in the gap it meets as it goes, not in the one left when a step ends. Knife
work over wet paint changes; everything else is painted as before.

## Breaking, in oil paintings: a knife barely touching no longer lays more in shorter steps

A knife skimming the canvas (pressure under 0.3) lays paint from the bead on
its blade's edge. How much it laid depended on how its stroke was cut into
steps: in steps of 2 px rather than 8, up to 1.7 times as much. It no longer
does (within 1% over the bare canvas, 3.4% over thick wet paint): the bead's
reach is measured in a length of the blade's own, and it touches the surface
under the paint it has just laid, not that paint. A heavily loaded knife at
the lightest touch now lays a fifth to a third less than it did; at pressure
0.15 and above, what a knife lays is as it was.

## Breaking: NumPy 2 is required

NumPy 1.x is no longer supported: murex requires `numpy>=2.0` and
`numba>=0.60` (the first numba that supports NumPy 2). Under NumPy 1.26.4 and
NumPy 2.5.5, `spectral.srgb_to_reflectance` returned different numbers, and
the numbers must not depend on which NumPy is installed. No result under
NumPy 2 changes.

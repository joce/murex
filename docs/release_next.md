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
does over the bare canvas and thin wet paint (within 1%): the bead's reach is
measured in a length of the blade's own, and it touches the surface under the
paint it has just laid, not that paint. Over thicker wet paint a lightly
loaded pull left up to a tenth less in short steps, for another reason, put
right by the next change. A heavily loaded knife at the lightest touch now
lays a fifth to a third less than it did, and knives shorter than 32 px a
little less again; at pressure 0.15 and above, what a knife lays is as it
was.

## Breaking, in oil paintings: a knife drags wet paint as far in long steps as in short

How far a knife dragged wet paint, the heap it left where it stopped and how
much of its own paint it laid depended on the steps its stroke was cut into:
at a stroke's own steps a wide blade carried a fifth further than in short
steps, a narrow one nearly twice as far. The blade rides on the wave of
paint it pushes, and how high it rides was read once per step, a step ahead
of that wave. It is now worked out as the blade goes, and for a lightly
loaded knife a stroke's own steps give what short ones give within a few
percent, mostly within one (skimming thick wet paint, within 3%). Knife work
over wet paint changes again (it drags less, and lays its paint more
evenly), and takes 12 to 14% longer; everything else is painted as before.

Still depending on the step: a heavily loaded knife at a light pressure,
which carries wet paint 7 to 15% further in its own steps than in short
ones; a heavily loaded knife skimming over two wet layers, the upper one of
its own paint, which lays up to a quarter less in short steps (it comes to
rest on its own fresh paint, which the earlier layer has taken in); and a
pull down a slant of 45 degrees at a middling pressure, which wavers twice
as much in its own steps as in short ones.

Not fixed, and in some cases more dependent on the step than it was: a knife
partly past the edge of the canvas over wet paint. The paint it drags flows
out past the edge and none flows in, so the edge is drained, and past the
edge the blade fills that hollow with paint that is then lost, in short
steps more than in long ones. Set down across the edge, a knife leaves a
sixth to a quarter more of its paint on the canvas in its own steps than in
short ones (a twentieth to a tenth more before); coming onto the canvas over
wet paint, up to twice as much, as before. This is left for a separate
issue.

## Breaking, in oil paintings: a loaded knife no longer drops lumps along an earlier ridge

A loaded knife pulled along the ridge an earlier pull left at its blade's
end gathered the ridge into a heap and dropped it part of the way, as a lump
two to three times as thick as the paint around it: the heap stopped
wherever it came under the knife's own fresh paint, on which the blade
glides. The blade now pushes on what is in its way under its own paint too,
and takes the heap with it or lays it out as it goes: on a ground of such
pulls there were up to 112 pixels more than 8 units thick (the paint is 2 to
3.5 thick), and there are none, at a stroke's own steps and in shorter ones.

Knife work over wet paint changes, the more the more the knife is loaded and
the harder it is pressed. A lightly loaded knife paints much as it did
(within 1% for what it carries and lays; barely touching, it carries the wet
paint 2 to 5% further). A heavily loaded one carries the
wet paint further, a tenth further at a firm pressure, where it used to drop
lumps of its own; pressed nearly down to the canvas it leaves a bigger heap
where it stops (a third to a half bigger for a short blade) and lays up to a
tenth more of its own paint at its own steps, which is what it laid in short
steps. Loaded pulls across the ridges of earlier ones lay about a twentieth
less of their own paint, the room being taken by what they gather. A picture
built of loaded knife pulls over one another changes all over, in the detail
of its relief (`knives.png`: a fifth of its pixels by more than 1/255). Brush
strokes, and knife strokes on the bare canvas or over dry paint, are painted
as before, to the bit.

Still as it was: what a blade carries to the end of its pull it leaves
there (and more of it gets there), and a heap gathered from a narrow ridge
stays narrow (the paint under a blade moves along the pull, not along the
blade).

## Breaking, in oil paintings: a knife at the edge of the canvas

A knife coming onto the canvas over its edge, or set down across it, found
the wet paint there drained away and laid its own in its place: up to four
times the paint that the same stroke leaves in the same place on a larger
canvas, and more or less of it as the stroke was cut into steps. The flow
under a blade let wet paint out over the edge and none in, and what a blade
pushed off the canvas was lost without being counted.

The part of a knife's stroke that reaches past the edge is now painted on
the canvas going on there as its own mirror image (wet paint, dried paint
and weave, up to 128 px past each edge). A blade coming on brings with it
the wet paint it has pushed along out there, one leaving takes some with
it, and what lands on the canvas is what the same stroke leaves on a larger
canvas: within 1.2% set down across the edge or leaving, 1.4% along the
edge and 6% coming on at pressures 0.25 and above, at every step length,
where it was 55% under to 310% over. `canvas.edge_loss` (new) is what the
canvas and its knives have lost over the edge, less what they have gained
there: a difference, which the canvas, the knife and it keep every pigment
by; it is below nothing where knives have brought more on than they pushed
off, and no store of paint.

Knife strokes wholly on the canvas are unchanged, and so are brushes. Of
the benchmark's 16 scenes, `edges` changes and `knife` barely (two
strokes). Four of the README's images change: `knives.png` in 5.1% of its
pixels, `knife_drag.png` in 1.1%, `dirty_brush.png` in 0.39% and
`bob_ross_style.png` in 0.56%. The steps of a knife stroke past the edge
take as long as steps on the canvas now, where they took a quarter (the
three knife strokes of `edges`: 1.5 to 2.0 s for 0.8 to 1.1); memory is
0.25 KB for each pixel those steps can reach, not for the whole stroke.

Limits: nothing is kept past the edge between strokes, so a knife pulled
onto the canvas again and again over one track keeps bringing paint on;
paint that is uneven near the edge is mirrored as it is (a band of colour
along the edge is twice as wide to a knife coming on); and a knife that
starts further out than 128 px lays its paint out there as before and
drags none until it is that near.

## Breaking: NumPy 2 is required

NumPy 1.x is no longer supported: murex requires `numpy>=2.0` and
`numba>=0.60` (the first numba that supports NumPy 2). Under NumPy 1.26.4 and
NumPy 2.5.5, `spectral.srgb_to_reflectance` returned different numbers, and
the numbers must not depend on which NumPy is installed. No result under
NumPy 2 changes.

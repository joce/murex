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
wet paint, up to twice as much, as before. (Put right since: the canvas
past its edge, below.)

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

## Breaking, in oil paintings: the canvas goes on past its edge

A stroke that ran over the edge of the canvas met nothing real out there. A
knife coming onto the canvas over its edge, or set down across it, found
the wet paint at the edge drained away and laid its own in its place: up to
four times the paint that the same stroke leaves in the same place on a
larger canvas, and more or less of it as the stroke was cut into steps. The
flow under a blade let wet paint out over the edge and none in; what a
blade pushed off the canvas was lost without being counted; thick paint
left at the edge piled against it as against a wall; and the part of a
brush past the edge laid nothing anywhere.

The canvas now goes on past its edge: bare at first (its ground, and its
weave over again), then holding whatever strokes leave there, up to 128 px
out. The part of a stroke that reaches past the edge, a brush's as well as
a knife's, is painted out there as on the canvas; a knife is painted all
its way, however far out it starts; after the stroke the paint settles
across the edge; and when the paint dries, what lies out there dries too,
and a later blade rests on it. So strokes at the edge, one after another,
leave on the canvas what the same strokes leave on a larger canvas. Eight
pulls of a clean knife onto the canvas over a brushed ground bring on 5,950
units of wet paint where a larger canvas gets 5,980. Over a ground brushed
only up to the edge they bring on nothing, as there is nothing out there. A
knife pulled on from 300 px out at pressure 0.9, four times, brings on
4,372, 1,224, 320 and 227 units where the larger canvas gets 4,371, 1,225,
319 and 225. A loaded knife stopped 6 px short of the edge leaves 1,698
units on the canvas where the larger canvas has 1,695 to 1,711: the rest
has slumped over the edge. On a larger canvas whose weave is the canvas's
own over again, the paint lies the same pixel by pixel after every stroke,
to rounding.

What lies past the edge is not shown. It is copied and pickled with the
canvas (a canvas pickled before loads with nothing out there) and takes
0.23 KB a pixel where there is paint; a canvas no stroke is taken past the
edge of keeps nothing. Paint written into a canvas's arrays by hand is on
the canvas only.

`canvas.edge_loss` (new) is what the canvas and its knives have lost over
the edge, less what they have gained there: a difference, which the
canvas, the knife and it keep every pigment by. It rises when a knife
pushes paint off the canvas and falls when one brings paint on, below
nothing where knives have brought on paint that brushes laid out there. It
is no store of paint: what is out there is what the canvas keeps past its
edge. What crosses the edge under a brush is not counted.

Strokes that stay clear of the edges paint as before, to the bit. Every
stroke that runs over an edge paints differently near that edge, and later
strokes working over it carry the change inwards. Of the benchmark's 16
scenes, four paint as before to the bit (`round-small`, `dabs`, `stipple`
and `knife-lift`, where nothing reaches past an edge); in eight, 4 to 7% of
the pixels change, nearly all of them within 100 px of an edge and hardly
any by more than 1/255 in the picture, and in `knife` a few dozen pixels;
`edges`, whose strokes all run off the canvas, changes in 12% of its
pixels; and in `glass` and `painting`, where strokes work over one
another, the change is carried all over. In `glass` the wet paint differs
at a third of the pixels, by less than a hundredth of a unit away from the
edges. `painting` lets its ground dry and paints over it: its wet paint
differs at 60% of the pixels and its dried paint at 88%, by up to 0.40
units within 32 px of an edge and 0.13 units further in than 96 px, where
one pixel in a thousand differs by more than a hundredth of a unit. Every
image of the README is regenerated. The one that shows it is
`bob_ross_style.png`, whose sky is brushed from outside the canvas: 44% of
its pixels change, 10% by more than 2 of 255.

A stroke at the edge is painted past the edge too, so it costs what the
same stroke costs on a canvas that much larger, and a little more. Along
the whole top edge of a canvas 2,000 px square, a flat brush takes about
10% longer than on the larger canvas (5 to 13% over the runs), which is 1.6
times what it took when its half past the edge was skipped, and a knife 15%
longer, which is what it took. Strokes that stay on the canvas take what they took, within a few
percent.

The limit: what a stroke leaves further out than 128 px is gone when the
stroke is over. (Within the stroke a knife still drags it along, all the
way; a brush that far out uses its paint up as before.) So strokes that
work further out than that, one after another, do not find what the
earlier ones left there: over a ground brushed 250 px over the edge, two
knife pulls onto the canvas from 300 px out at pressure 0.9 bring on 9,682
and 5,126 units where larger canvases get 11,820 and 10,045.

## Breaking: NumPy 2 is required

NumPy 1.x is no longer supported: murex requires `numpy>=2.0` and
`numba>=0.60` (the first numba that supports NumPy 2). Under NumPy 1.26.4 and
NumPy 2.5.5, `spectral.srgb_to_reflectance` returned different numbers, and
the numbers must not depend on which NumPy is installed. No result under
NumPy 2 changes.

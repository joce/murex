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
as much in its own steps as in short ones. (Put right since: a knife's stroke at
every cut, below.)

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
blade). (The heap is the same at every cut since: a knife's stroke at
every cut, below.)

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

## Breaking, in oil paintings: a knife's stroke is the same stroke however it is cut

A stroke is painted in steps, a quarter of the tool's width long and 8 px at
most. What a knife did still depended on them in four ways, which had one
cause: a step read once something that changes while it lasts. A heavily
loaded knife carried wet paint 7 to 15% further in its own steps than in
short ones, and laid a slab up to 18% thinner on the bare canvas; a loaded
knife skimming over wet paint of its own colour laid up to a third more; a
pull down a slant rippled the surface more; what a blade left beside its
mark was up to 44% less; and over dried ridges a skimming knife laid 2 to
4% more or less as its steps fell on them.

Now the same pull of a blade in its own steps and in steps of 4, 2, 1 and
half a pixel carries the wet paint as far and lays as much within 1% as a
rule: loaded and clean knives, skimming to pressed hard, 60 to 160 px wide,
over knifed and brushed wet paint, dried paint and the bare canvas, lifted
off or not (2 to 4% for a blade pulled along its own length, or leaving
over the edge of the canvas; the furthest found: 10% for a 160 px blade
leaving over the edge, where it was 33%, and 13% for a blade over thin
paint that covers the canvas in patches, where it was up to 34%). The
blade is set down in a step of its own
before it moves, and lifted off in another; under a blade that rides on wet
paint, its level, what it spills at its ends, what it drags and what it
lays are worked out every 0.7 px of the paint's way, wherever the stroke is
cut; a stroke knows its own paint from an earlier stroke's where the two
have joined; and over dried paint with no wet paint on it thick enough
to hold the blade up, a knife's steps are 2 px at most. Combs are not
covered: what a comb's teeth carry depends on the cut as before.

Two things a blade does are new:

- **It comes to glide on its own fresh paint little by little,** between
  0.15 and 0.45 units of it, where it switched at 0.3.
- **What it spills past its ends is the paint that lay there,** not the
  top layer, which under a loaded blade is the blade's own fresh film (85
  to 89% of what such a blade spilt was its own white). The model says
  the lips are paint that was lying there; it does not force the order,
  and this is one reading of it. For a blade square to its way it changes
  little (what it moves of the paint under it: up to 4% more; what a
  loaded blade at a light pressure leaves beside its mark: 19 to 31%
  more). For a loaded blade pulled along its own length, where every
  pixel under it is near an end, it is most of what the pull does, and
  how much hangs on the ground: it moves 16% more of the paint under it
  over knifed paint, about half as much again over thick brushed paint,
  80% more over wet paint on dried ridges and twice as much over thin
  paint in patches, and carries it from 4% less far to twice as far (13%
  further over knifed paint, 37 to 46% over brushed).

Otherwise knife work is what it was in short steps: over brushed paint a
clean blade square to its way carries and moves what it did within 1%, and
a loaded one carries as far within 2% as a rule. (A clean scraper pulled
along its own length carries a quarter less far than it did in short
steps, and 8% less far than it did at a stroke's own steps.)

What a blade carries to the end of its pull it still leaves where it
stops, as a knife stopped under pressure does: but the heap no longer
depends on how the stroke is cut. Where loaded pulls across the ridges of
earlier ones stop, its tallest point stood 10.8, 8.2 and 5.7 units above
the paint around it in steps of 8, 2 and 1 px with the same textures; it
now stands 6.8, 6.7 and 6.6. (With each stroke's own textures, at a
stroke's own steps: 7.7 where it was 6.0.) And the surface behind a blade
pulled down a slant ripples the same at every cut, by what sub-steps of
0.7 px give: at a stroke's own steps a sixth to a quarter more than it
did, in short steps four times as much; halving the sub-steps would
smooth it further, and cost 30% more time on knife work. Brush strokes
are painted as before, to the bit: of the benchmark's 16 scenes the 12
without a knife are unchanged. Knife strokes take about as long as they
did: no difference could be measured on the benchmark's knife scenes
within the machine's noise (7%), except perhaps a few percent more where
strokes run over the edge of the canvas. The exception is a knife over
dried paint with no wet paint on it to ride on: its steps are 2 px at
most there, and such a pull takes about two and a half times as long
loaded or skimming, and up to 1.6 times clean.

A knife's stroke is also the same stroke, to the bit, wherever on the
canvas it is painted: its path is taken on a grid of a millionth of a
pixel. And it no longer hangs on a last bit of its path in the one way that
was traced: a stroke whose end moved by a million-millionth of a pixel had
changed over thousands of pixels.

## Breaking, in oil paintings: a stroke has the same textures however it is cut

Every stroke wavers at random along its length: its width wobbles a little,
a knife's blade chatters and is tilted to one side, its colours wander in
bands, and the hair of a brush or the nicks of a blade score their lanes.
The wobble of the width was counted in steps of the stroke, so a stroke cut
into other steps drew more or fewer random numbers for it, and everything
drawn after it (the tilt, the bands, the hair) came out as another seed
would give it: a stroke showed how it was cut through its textures. The
hair also covered a length and a width that were measured on the points of
the cut.

Now every texture is drawn against the distance along the path, as many
random numbers as the length of the path calls for, and read where each
point of the stroke lies; what the hair covers and the width a load is
measured in are taken from the stroke in its own steps, whatever steps it
is painted in. The same stroke in steps of 8, 4, 2 and 1 px (and half a
pixel, a knife's) draws the same numbers, and has the same wobble, tilt,
bands and hair along its length. (A stroke already drew from numbers of its
own: one stroke's cut never changed the next stroke's textures.)

Every oil painting changes a little. For most strokes the wobble is what
it was: as strong, and one turn every 0.8 widths, which is what a stroke's
own steps gave it. Of the 2251 strokes and marks of the benchmark's 16
scenes, 2101 draw as many numbers as they did, and keep their tilt and
their bands, with a wobble stretched by a few percent at most (most keep
their hair too; a few dozen have another, where the stretched wobble makes
the brush a hair wider at its widest); the other 150 come out as another
seed would have made them. The strokes that do change in character are
those of a flat, a filbert, a fan or a knife where they turn: they are cut
finer there, and their width then wobbled as many times faster as they
were cut finer (a 60 px knife's on a gentle curve crossed its mean every
4.5 px, and does every 100 px now, as any stroke's does). Painting takes
as long as it did: setting a stroke
going costs what it cost (0.3 to 1.4 ms, the same within 3%), and a stroke
painted in its own steps is not sampled twice.

What the cut still changes can now be measured stroke by stroke, where it
took the average of several seeds. A knife's pull does the same at every
cut within 1% as a rule, and within 2 to 3% where it was known to be
furthest (the slab a wide, heavily loaded blade lays on the bare canvas is
0.8 to 2.5% thinner in its own steps than in steps of half a pixel, from
one pull to another). A brush lays as much paint at every cut (within 1%;
2.4 to 4.5% more for a hog flat over a knifed slab), but what it lifts and
carries off still depends on its steps, as it did: that is not changed
here, see the changelog.

## Breaking: NumPy 2 is required

NumPy 1.x is no longer supported: murex requires `numpy>=2.0` and
`numba>=0.60` (the first numba that supports NumPy 2). Under NumPy 1.26.4 and
NumPy 2.5.5, `spectral.srgb_to_reflectance` returned different numbers, and
the numbers must not depend on which NumPy is installed. No result under
NumPy 2 changes.

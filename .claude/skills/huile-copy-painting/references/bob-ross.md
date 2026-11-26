# Bob Ross in huile

How each of his techniques is painted in `examples/huile/towering_peaks.py`
(The Joy of Painting, series 10, episode 1), what made it look like his, and
what did not. Sizes are for a 1200 x 900 px canvas (50 px an inch, `K` = 1.875
px per pixel of the 640 x 480 reference frame). Read the function in the
script for the full code; this page says why it is so.

## Sky and water

Liquid White first (`liquid_white`), then the two-inch brush with a little
blue in criss-crosses from the top down, reloaded less as it comes down, so
it lightens towards a band across the middle; the water pulled in from the
sides; a clean brush over both. Nothing here needed changing for likeness.

## Clouds (`cloud`, `crown`)

- He scrubs the crowns with a one-inch brush, then blends the bottoms with
  a clean two-inch brush in tiny circles and lifts. The crown is an
  irregular line of lumps of different widths, never a row of circles.
- What worked: `scrub_along` the crown with `SOFT_ROUND.sized(64)` (a
  feathered round the width of his brush), circles of radius 14, loaded by
  path length; the body in rows 0.4 brush widths apart, less paint lower
  down, stopping 0.3 of the height above the base; the crown's edge barely
  touched with the mist brush (`pressure=0.3`, `mixing=1.0`); the bottoms
  blended in four passes, pressure falling as they rise.
- What did not: dabs of 18 to 30 px (rows of little puffs, "comically
  cartoonish"); a crown band following the outline down both ends (an
  outlined sausage); the body scrubbed to the base (a hard flat bottom).
- Colour: his clouds are thin (the sky shows through) and lavender, pink
  on the crowns, and they fill most of the sky. Cerulean in the white turns
  them cyan; ultramarine and alizarin keep them lavender. Their lights are
  set by the mix, not the load: less titanium in it (25 to 35 parts to 2 or
  3 of colour) brought them down to his; halving the load hardly did. The crown is scrubbed with `mixing=0.15`, so
  its pink is not lost in the wet blue; the body with 0.4.
- The blending rows wander (a smoothed noise of 0.12 of the height): run
  level, each left a bright streak at its lower rim.

## Mountain (`mountain`, `knife_in`, `snow`)

- The dark is cut in with the knife from the ridge down
  (`knife_in(RIDGE, MOUNTAIN_BASE - 15 * K, ROCK)`), scraped lightly
  (`pressure` 0.15; firmer scraping cut light columns into it) with the
  blade below the ridge along its whole length, then pulled down with the
  two-inch brush.
- Snow, from the frames: the knife held *across* the ridge, its tip just
  under it, pulled down *along* the ridge with no pressure (`SKIM`), in short
  pulls (about 60 px), each reaching its own way into the face (0.3 to 0.7
  of the blade), the blade turned 15 to 45 degrees, `follow_path=True`; two
  rows on lit faces, five in the shade colour on shadowed ones. The breaks
  run down the slope and the lower edge frays.
- His lit snow lies in narrow bands just under the ridges, the ridges
  within a face included (read them off an enlarged frame), with blue rock
  between the bands. Whole faces covered in white measured 40 too light.
  Colours, read off swatches against his lights and darks: the snow white
  with ultramarine and alizarin (lights about [201 202 228]), the rock
  mostly ultramarine and cerulean with a little white (his darks about
  [84 109 135]), no Van Dyke brown to speak of: it turned the rock lilac.
- The two-inch pull-downs every 20 px, lightly (0.15): every 34 px and
  firmer they showed as vertical columns.
- What did not: one long stroke a face along the ridge (blocky ends); pulls
  straight into the face, square to the ridge (dashes the wrong way); snow
  over a ground that stopped short (the snow seemed to stop too).
- Mist: horizontal scrubs of a little white and blue with the mist brush,
  pressure growing towards the base. Clean-brush blending over the whole
  base swallowed the mountain; dabs of the mist brush printed speckles.

## Tall evergreens (`conifer`, `branch`)

- His: the big brush loaded to a chisel edge, a touch at the top, then the
  corner, back and forth down the tree, pressed so the bristles bend
  downward; sap green on the edge, lightly, for highlights.
- What worked: a dark spine (`CORNER`, `angle=90`, widening to 0.06 of the
  height); then each side on its own, tufts of 1 to several arms, the tuft
  0.015 to 0.065 of the height thick, the next one lower by its thickness
  plus a gap that shrinks to nothing at 0.6 of the height, so sky shows
  between the tufts near the top only; an arm is a few overlapping touches
  of the corner, 10 to 34 px wide, its tip bent down a little; reach
  `0.28 * h * t**0.55`, so the tree is broad soon below the top; highlights
  with `SOFT_ROUND`, `mixing=0.4`, on the tufts' tops, mostly on the light's
  side.
- What did not: one long stroke an arm (fern fronds); both sides in step
  (pagodas); arms tapering to a point (fish bones); thick, wide touches
  (stacked pillows, every edge lit); thin paint (the sky shows through).

## Leaf trees and bushes (`block_in`, `leaves`)

- He blocks in the dark, then taps with the one-inch brush, darker colours
  first, lighter on the tops, the dark left in the hollows.
- What worked: `canvas.stipple` with `LEAF_TAP` (a hog round tapped lightly
  prints its bristle tips), forms half the size of the tree, about twice as
  many taps as first tried, more of the lighter colours than the darker,
  `mixing=0.05`; yellower greens (sap green with cadmium yellow).
- Colour: tap with `pickup=0.0`. With the default, each tap picked up the
  wet blue ground and the leaves came out blue-grey (mids [88 113 63]
  against his [75 89 28]) whatever the mix; with it, they render as their
  swatches do. His greens are darker than they look on the show: his
  lightest leaves measure [116 119 51]. Taps spread past the form's edge
  (a half-normal radius, cut at 1.1) soften it; spread further, lone taps
  print as rings.
- Order: each colour over every form of the tree, darkest first, then the
  next. Form by form (dark to light on one, then the next), the next form's
  dark taps landed on the last one's lights as dark rings all over it.
- What did not: small forms with dark between them (polka dots); mixing
  0.3 with the dark (muddy grey-green); forms placed so high they cover the
  evergreens behind.

## Path (`path`)

A Van Dyke brown band with the knife, then grey (brown, white, a little
Prussian blue) knifed across in short strokes for stones, then bushes pushed
over it. Stones at low pressure printed the canvas weave as a checker;
0.45 to 0.6 lays them solid.

## Signature (`sign`)

His signature is red, with the liner, lower left. The copy signs "Claude"
the same way, a stroke a letter, through `hand()` so it wavers.

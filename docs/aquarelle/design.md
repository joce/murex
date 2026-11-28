# Wet media: design proposal

Status: draft (issue `murex-cjx.1`, under the epic `murex-cjx`), for the
owner to accept, change or refuse. Nothing of it is built. The questions the
owner decides are gathered at the end.

`murex.aquarelle` simulates the wet media: watercolour, gouache, ink laid
with a brush, pens with liquid ink, and felt-tip markers. It is also the
first medium built on the one surface that every medium will read and write,
which `murex-9r5` left to be designed with the wet engine. So this document
designs two things: the shared surface, and the wet media on it.

## What aquarelle has to get right

A wet medium is pigment (or dye) carried by water, or by alcohol, that keeps
moving until the solvent has gone. The mark is wherever the pigment was
when it stopped: it is decided as much by the paper and by time as by the
brush. These are the behaviours the model is judged on. Each one can be
measured, so each becomes a test. There are no swatches painted for murex
to compare with: what each is judged against instead is in "References
without swatches" below.

1. **A wet edge stays where it was painted.** On dry paper, a wash stops
   where the brush stopped, with a hard edge. On damp paper it spreads with
   a soft edge, the further the wetter the paper.
2. **Edge darkening.** A wash dries darker at its rim. Water evaporates
   faster where the film is thin, at the edge, and the water flowing out to
   replace it carries pigment there. Measured as the ratio of the density at
   the rim to the density in the middle of a flat wash.
3. **Wet-in-wet.** Colour dropped into a wet wash blooms out with a soft
   edge. How far it goes depends on how wet the wash and the brush are, and
   on how long the wash has been drying.
4. **Backruns (blooms).** A brush wetter than the paper under it pushes
   water into a wash that is half dry. The water carries the pigment out
   ahead of it and leaves a pale centre with a dark, branching edge (a
   "cauliflower"). This does not happen when the paper is wetter than the
   brush. Measured by whether the edge appears, and how long it reaches.
5. **Granulation and flocculation.** Heavy pigments (ultramarine, cerulean,
   the earths) settle in the hollows of the paper's tooth. Ultramarine
   clumps even on smooth paper. A pigment that stains (phthalo, alizarin)
   does neither. In a mixture they separate: the granulating colour gathers
   in the hollows, and the other lies evenly. Measured as how closely the
   density of a dried wash follows the tooth.
6. **Staining and lifting.** Once dry, some of the pigment is in the fibres
   and some is on them. A damp brush or a tissue lifts what lies on them
   back to the paper's tone, and leaves the stain. Gouache and watercolour
   soften again under water. India ink and acrylic do not, once they have
   dried.
7. **Glazing.** A dried wash is transparent. A wash laid over it once it is
   dry mixes with it as layers do (yellow over blue reads green, deeper
   than the mixture of the two). Laid over it while it is wet, it mixes as
   paint does. A wet brush passed over a dry wash that does not stain
   disturbs it a little.
8. **Wet is darker, and shines.** Water fills the air between the grains of
   pigment, so a wet wash looks darker and more saturated than it will dry.
   While water stands on the paper it shines under a lamp. A wash dries
   lighter: measured as the lightness of the same wash, wet and dry.
9. **The paper drinks.** A hard-sized paper lets the water stand and move
   on its surface. An unsized one (xuan, blotting paper) drinks it at once:
   lines feather, and ink spreads in halos. The water runs further along the
   fibres than across them.
10. **Dry brush.** A brush with little water on rough paper touches only the
    peaks of the tooth. The valleys stay white, as under a light pencil.
11. **Lines of ink.** A pen's line stays crisp on a sized paper and feathers
    on an unsized one. A flexible nib widens with pressure. When the ink
    cannot keep up with the spread of its tines it leaves two thin lines
    ("railroading"), and it runs dry until it is dipped again.
12. **Markers streak.** A stroke of a water-based marker that crosses one
    that has already dried leaves a darker overlap. Where the first is still
    wet the two merge. An alcohol marker stays wet for less time, but spreads
    further into the paper, and blends while it is wet.
13. **Gouache covers.** A light gouache covers a dark one. It dries matte,
    flat and lighter than it went on, and laid thick it hardly flows.
14. **Conservation.** Water and pigment are both conserved. What leaves a
    brush or a tip is on the paper, on a tool that took it back, or (for
    water only) evaporated. Tests check this as they do for fusain and
    huile.

Not modelled, at first or at all: the paper cockling as it swells, ink seen
through the back of the sheet, how the paper was stretched, the colour of the
water in the jar.

## The surface: one for every medium

`murex-9r5` laid the package out in layers, with imports pointing only
downward: (1) colour, (2) the kit (paths, noise, filters), (3) supports,
(4) the state of the surface and its render, (5) the media, which never
import each other and meet only through the surface. Layers 3 and 4 do not
exist yet: fusain's `Paper` and `Sheet` and huile's `Surface` and `Canvas`
each hold them for one medium. Aquarelle is where they are made.

### Supports (layer 3)

`murex/paper.py` holds the `Paper` that fusain's `paper.py` holds now, moved
as it is. `murex.fusain.Paper` stays as a name that points to it, so no
drawing changes. It gains what water needs, all with defaults that leave a
dry drawing as it was:

- `sizing`, 0..1: how far the gelatine or starch size keeps water on the
  surface. 1 for a hard-sized watercolour paper, 0 for xuan or blotting
  paper.
- `holds`: how much water the fibres take before they are full. A heavy
  sheet (640 g/m²) holds several times what a light one (190 g/m²) does.
- `fibres`, an angle and how strongly they run that way: the direction the
  water wicks fastest along.
- Presets for hot-pressed, cold-pressed and rough watercolour papers, and
  for xuan. The `"rough"` texture is there already.

The tooth's random draws must not move: a new random map (sizing that
varies across the sheet, the fibres) is drawn from a generator of its own,
seeded from the sheet's seed. So fusain's fingerprints stay as they are, and
every image is regenerated byte for byte. That makes this move a change that
does not alter the picture, and checks it as one.

huile's `Surface` stays in huile until oil moves, which comes last.

### The state of the surface (layer 4)

One object holds everything that lies on a support, whichever medium laid
it. Its name is an open question (see the end): it is called "the surface"
here. Three kinds of thing are stored, per pixel, all `float32`.

**The paper's own state.** This is what a tool does to the paper, not what
lies on it. Every medium reads it: `tooth` (set from the paper), `crush`,
`rough` and `dent` (fusain's now), and now `wet`, the water in the fibres.
It belongs to the surface, not to the medium that made it. A stylus's
groove (`dent`) is skipped by a pencil, but a wash fills it and dries dark
there: the "impressed line" of watercolourists. A patch scraped by a knife
or a sand eraser (`rough`) has lost its sizing, drinks a wash and stains
darker.

**Strata: what has been laid and stays.** A stratum is a mixture packed as
huile's and fusain's are: K over the 24 bands, S, volume, then volumes for
the kinds of matter that later tools ask about. For example:

| Volume | Who asks |
| --- | --- |
| `soluble` (in water) | a wet brush, which takes it up again: watercolour, gouache, water-soluble pencil |
| `soluble_alcohol` | an alcohol marker or a blender |
| `wax` | water, which runs off it (a resist); a tip, which slides on it (fusain) |
| `loose` | a stump, a finger, an eraser (fusain's dust) |
| `stain` | nothing: it is in the fibres |

Everything stored is extensive, summed over what lies there. So any mix of
media composes at a fixed cost per pixel, as the 24-band sums do already.
Properties of a medium are written as volumes of the kinds of matter it is
made of, never as a flag on the pixel.

The strata are a fixed small number, ordered from the paper up:

1. **In the paper:** stains, dyes, the part of a watercolour that sinks
   into the fibres, fusain's ballpoint ink. Nothing reaches it but a blade
   or grit that cuts the paper.
2. Two or three **strata on the paper**, as in fusain: a new stratum goes
   on top, and the one at the bottom is buried when there is no room.
3. **What is buried** is baked into the reflectance it is seen over, as
   huile's `dry()` bakes its dried paint into its ground today. It is
   still seen, and no tool reaches it any more.

Whether three strata on the paper are enough is a question to measure, not
to decide: a glaze over a glaze over a glaze, then lifted, shows whether the
fourth layer down still needed to be reachable.

**The wet layer: what is still moving.** It is held only where there is
water, and allocated when a wet medium first touches the sheet, as fusain's
`ink` is now. It holds:

- the depth of water standing on the paper and its velocity (on a grid
  offset by half a pixel, as shallow-water models are);
- the pigment suspended in it, in a fixed number of **classes of
  particle**. Each class is a packed mixture of its own: dissolved dye, fine
  pigment, and heavy (granulating) pigment. A pigment belongs to one class,
  or is split across them. With one mixture, ultramarine and alizarin could
  not separate as they settle. With three, they do, at three times the cost
  and no more however many pigments are mixed.
- the pigment that has settled on the paper but is still wet, in the same
  classes. It can still lift into the water until it dries, and then it
  joins the top stratum.

That is about 160 numbers a pixel while it is wet, on top of the strata and
the paper's state. Fusain holds 157 today.

### Time

In fusain and huile a stroke is finished when it ends. Wet paint is not: it
keeps flowing until it has dried. So the surface has a clock:

- A stroke takes time: its length over the speed of the hand (a parameter
  of the stroke, with a default). The water flows as the stroke is laid,
  so that the start of a long wash has had time to spread before its end
  is laid.
- `surface.wait(seconds)` lets the water move and evaporate. `surface.dry()`
  waits until no water is left. Huile's `Canvas.dry()` keeps its own
  meaning when oil moves.
- How fast water evaporates is a property of the air on the surface: a dry
  room, a damp one, a hair dryer.
- A dry medium takes no time, and does not touch the clock. Drawing on a
  wet sheet is another matter, and a later one: graphite or pastel on damp
  paper.

### Scale

The water's behaviour is physical: how far it wicks in a second, how thick a
film is. Huile has no scale (about 2 px/mm, set by eye). Fusain's is the
paper's grain. Aquarelle needs a real one: the surface carries `px_per_mm`,
and the paper's grain is a size in millimetres turned into pixels. What the
default should be is an open question.

### Rendering

There is one renderer for everything on the surface, from the paper up:

- the paper's reflectance, under the stain in its fibres, under each
  stratum by Kubelka-Munk, as fusain's `_reflectance_rows` does now; then
  what is buried, baked into the reflectance at the bottom;
- the wet layer on top, with the scattering of its pigment lowered while
  water fills the air between its grains (wet is darker), and a gloss where
  water stands, lit by the lamp and the relief as fusain and huile light
  theirs;
- gouache's chalk scatters strongly, and dries matte.

Fusain's films and dust, and later huile's two wet layers, become kinds of
strata when they move. Each medium still decides how its own matter behaves
under a tool. Only the surface decides the order things lie in and how they
are seen.

## The fluid model

The model starts from Curtis, Anderson, Seims, Fleischer and Salesin,
"Computer-Generated Watercolor" (SIGGRAPH 1997). It mixes pigments with
Kubelka-Munk, as murex does, and has three layers that map onto the surface
above:

1. **The water on the surface** is shallow water. It flows down the slope of
   the paper's relief (and down the board if it is tilted, which is how a
   graded wash is laid). It is held back by the paper's drag and kept
   inside the wet area: water does not run onto dry paper. That is what
   makes a hard edge.
2. **Pigment** is suspended in the water and moves with it. Each class
   settles at its own rate, and lifts back up at its own rate. Heavy pigment
   settles in the valleys of the tooth: that is granulation. Dye sinks into
   the fibres: that is staining.
3. **Water in the fibres** spreads from wet fibres to dry ones, faster along
   the fibres than across them. It takes up what stands on an unsized paper
   at once, and gives backruns their cauliflower edge where a wetter patch
   pushes into a drier one.

Evaporation takes water from the surface first, then from the fibres. It is
faster at the edge of the wet area, where the film is thinnest, so the water
flows outward to the edge and darkens it (behaviour 2), rather than being
painted on.

The rules of murex hold:

- **Bit for bit.** A kernel is `@njit(cache=True, error_model="numpy")`
  without `fastmath`. The rules forbid `parallel`, and a whole-sheet flow is
  far heavier than a stroke. Each step of the flow can be written so that a
  pixel reads only the previous step's values, and nothing is summed across
  pixels inside a parallel loop. Written that way, the results are the same
  to the bit however many threads run it. Whether to allow `parallel` on
  those kernels only, with a test that one thread and many give the same
  bits, is the owner's decision.
- **Only where it is wet.** The flow runs on the bounding box of the wet
  pixels and a margin, not the whole sheet.
- **Counts from ratios.** The number of steps in a wait (the time over the
  step that keeps the flow stable) is a count from a ratio, so it uses
  `whole_ceil`. A test nudges the inputs by an ulp.
- **Conservation.** Water laid equals water standing plus water in the
  fibres plus water evaporated plus water taken back. Pigment laid equals
  pigment suspended plus pigment settled plus pigment in the strata plus
  pigment on tools. Both are tested after every kind of stroke.
- **Switches.** Wet and dry are where values cluster. Whether the paper is
  wet enough to let water onto it is a ramp over a range of wetness, not a
  threshold, or the edge of a wash would hang on the last bit of the water
  in one pixel.

## The wet brush

A brush holds water and pigment in its belly, and gives them up:

- by pressure: the belly is squeezed;
- by the difference between how wet it is and how wet the paper is. A
  loaded brush on dry paper gives a lot. A damp brush on a wet wash takes
  water and pigment back: that is how a highlight is lifted, and it is why
  a thirsty brush makes a backrun only when it is wetter than the paper.

What it takes up is in the brush, counted, and laid again further on, as
fusain's `HeldPen` keeps the ink on its ball. The brush's shapes are a
pointed round, a flat, a mop and a rigger. Its hairs are sable or synthetic,
which hold different amounts of water.

Huile's brush has the geometry of a footprint and of a hair field
(`_geometry.py`, `_hair.py`) that a watercolour brush needs too: a dry
brush shows the lanes of its hair. Under the rule that what two media need
goes in the shared modules, they move to the kit when aquarelle's brush is
written, checked by `tools/huile/bench.py --compare` staying identical.
Whether to move them, or to write aquarelle's own first and move the common
part once the difference is known, is an open question.

## The media on the engine

Every medium is the engine with its own matter and its own tip.

| Medium | What it lays | What sets it apart |
| --- | --- | --- |
| Watercolour | pigment in gum arabic: classes by pigment | soluble once dry; granulation and staining by pigment |
| Gouache | the same with chalk | high scattering, matte, thick (it hardly flows), dries lighter, soluble |
| India ink | carbon in shellac | very dark, a little granulation, waterproof once dry |
| Sumi | carbon in glue | washes, halos and feathering on unsized paper, slightly soluble |
| Dye ink (fountain pen ink) | dye, no particles | stains the fibres, rides the wet front; a mixed black separates into its dyes as it travels |
| Acrylic ink, fluid acrylic | pigment in acrylic polymer | waterproof once dry, does not lift |
| Dip pen and nib | any of the inks | width with pressure (tines), railroading, a reservoir that empties |
| Fountain pen | dye ink | a feed with a steady rate; feathers on soft paper |
| Fineliner, technical pen | pigment ink | fixed width, little ink, dries fast |
| Brush pen | dye or pigment ink | the wet brush, fed from a cartridge |
| Rollerball | liquid dye ink | a ball like fusain's ballpoint, but its ink wets and feathers |
| Gel pen | pigmented gel | opaque, sits on top, hardly spreads; white and metallic inks |
| Water-based marker | dye in water, from a porous tip | streaks over a dried stroke, merges with a wet one |
| Alcohol marker | dye in alcohol | dries fast, wicks wide, blends wet; water does not move it |
| Tools | masking fluid, salt, alcohol, a spray, a tissue | a resist; water drunk in stars; pigment pushed away; drops; lifting |

Alcohol is a second solvent. Keeping two fluid fields doubles the cost of
the wet layer. In practice alcohol markers hardly ever stand on the paper:
they live in the fibres. So the proposal is one field of water on the
surface, and the fibres' wetness split into water and alcohol, each
evaporating at its own rate and dissolving its own `soluble` volume. A
drop of alcohol in a watercolour wash is then the one case where the two
meet on the surface. That is an open question.

The ballpoint stays in fusain: its ink is a paste that stains the paper and
does not spread.

## Crossing media

These cases are why the surface is shared. Each reads something another
medium wrote.

- **Water-soluble pencils, graphite and Inktense.** Fusain lays dust with a
  `soluble` volume. A wet brush passed over it takes that share into the
  water, and leaves the rest as dust.
- **Wax resist.** A crayon or a candle (fusain's wax) keeps the water off.
  Wetting reads the `wax` volume of the top stratum.
- **Wash over a pencil drawing.** Graphite does not dissolve. Loose dust is
  sealed by the gum as it dries, or a little of it is moved by a wet brush.
- **Ink over pencil, pencil over ink.** These are common in drawing.
- **The impressed line,** and **scraped paper:** see "The paper's own
  state" above.
- **Coloured pencil and pastel over a dried wash.** The wash fills hardly any
  of the tooth, so fusain draws on it as on the paper, over the stratum.
- **Sgraffito.** Fusain's knife scrapes a dried wash off with the surface of
  the paper.

Until fusain moves onto the shared surface, these cannot be built. So the
step that moves fusain comes before them, and only the media that are
aquarelle's alone come before it.

## Build order

Each step is accepted on its own measurements, as fusain's were.

| # | Step | Judged by |
| --- | --- | --- |
| 0 | This design, accepted | the owner |
| 1 | Paper in the shared supports; the surface with water, the clock and drying | fusain to the bit; water conserved; a wet sheet dries in the time its paper and air say |
| 2 | The fluid engine and the wet brush; watercolour | behaviours 1 to 10 and 14, against the laws, ratings and photographs below |
| 3 | Ink with a brush | waterproofing, feathering on unsized paper, dyes separating |
| 4 | Pens | width with pressure, railroading, running dry, feathering |
| 5 | Markers | streaks, merging while wet, alcohol's spread |
| 6 | Gouache | covering power, matte, drying lighter, softening under water |
| 7 | Tools and tricks | each present and of the right sign (no reference) |
| 8 | Fusain onto the shared surface | fusain's fingerprints and every image to the bit |
| 9 | Crossing media | the cases above |

## References without swatches

The owner has no wet media to paint with, so no swatch will be painted for
murex. What the wet media are judged against is what can be had without
them, in three kinds, the strongest first. Gathering them, and checking
each source named here before it is relied on, is `murex-cjx.11`, and comes
before step 2 is judged.

**Laws, with numbers.** These make tests that need no picture:

- Water wicks into paper as far as the square root of the time
  (Lucas-Washburn): the wet front of a drop on unsized paper is twice as far
  out at four times the time.
- A drying drop whose edge stays where it is lays its particles at the rim
  (Deegan and others, Nature 1997, the coffee ring). The rim darkens the more
  the longer the edge holds, and the less the faster the particles settle
  before they get there: a heavy pigment rings less than a fine one, in the
  model as on paper.
- Particles settle at a speed that goes as the square of their size and as
  how much denser than water they are (Stokes). The order in which pigments
  granulate follows from their sizes and densities, which are published.
- Wet is darker for a reason that can be computed: water (refractive index
  1.33) in place of air (1) between the grains lowers how much light they
  scatter. How much lighter a wash dries then comes from the indices of the
  pigment and of gum arabic, not from a number tuned to look right.
- The invariants of the other media hold: water and pigment conserved, a
  wash moved by whole pixels the same to the bit, and the same wash at 2 and
  4 px/mm the same when measured in millimetres.

**Published ratings.** Makers of watercolour (Winsor & Newton, Daniel
Smith, Schmincke) publish, for each paint, whether it granulates, stains and
covers. Bruce MacEvoy's handprint.com rates many pigments on the same scales
from tests of his own. The model is judged on the order these give
(ultramarine and the earths granulate, phthalocyanines and quinacridones
stain), as a rank correlation, not on the ratings themselves. Reflectance
spectra of paint-outs, where conservation science has measured them, check
murex's pigments.

**Photographs.** Openly licensed photographs (Wikimedia Commons and the
like) of washes, blooms, granulation, feathering and marker streaks. They
are not calibrated: an unknown camera under an unknown light. So they judge
shapes, not tones: where the pigment gathers, the profile across an edge,
how a bloom branches, how far a line feathers for its width. Only those
whose licence lets them be kept go into the repository (in Git LFS). Figures
in papers, such as Curtis's photographs of real watercolour beside his
renders, are read and measured, never copied in.

**Where they are kept.** Everything gathered is kept in the repository, so
that any session, and any agent, works from the same references and not
from what one session read:

- `docs/aquarelle/references.md` is the register. Each source has its full
  citation, its address and an archived copy's address (the Wayback
  Machine), the date it was read, its licence, the numbers taken from it
  (with the page, table or figure they come from), what behaviour they
  settle, and the test that uses them. Where sources disagree, both are
  written down, and which one the test follows and why.
- The numbers themselves go into the code, each constant with a comment
  naming its entry in the register, and into the tests that check them.
  CI does not fetch images, and no test may need one, so a test never reads
  a photograph: it checks the numbers measured from it.
- A photograph whose licence allows it is kept in Git LFS, in
  `docs/aquarelle/references/`, with its licence and author beside it, and
  the tool that measured it (`tools/aquarelle/`) with the numbers it gave.
  A photograph or figure that may not be kept is cited, and only what was
  measured from it is written down.
- No paper or book is copied in. A short quotation where a number needs its
  context is enough.

What none of these settle is left alone: absolute tones, absolute times,
how a given brand of paper behaves. A behaviour with no reference is built
to be there and to go the right way, then left. The rule of the other media
holds: don't polish what has no reference to be judged against.

The speed is measured from step 2 on (a benchmark of washes, as
`tools/fusain/benchmark.py` measures strokes), since the flow is where the
time will go.

## Open questions for the owner

1. **The names.** What the shared surface is called, and its module.
   `murex.Surface` clashes with huile's `Surface` (which describes a
   support); `murex.Sheet` with fusain's. Since one person uses murex, names
   are free to change. A proposal: `murex.Surface` for the shared state, with
   huile's `Surface` renamed `Priming` when oil moves.
2. **`parallel` for the flow.** Allow it on the flow's kernels only, with
   the result checked identical across thread counts, or keep the rule and
   pay the time?
3. **The brush's geometry.** Move huile's footprint and hair field to the
   shared modules when the watercolour brush is written, or let aquarelle
   write its own first?
4. **Strokes and the flow.** Should the water flow while a stroke is laid
   (in slices of the stroke's time, as proposed), or only after it ends,
   which is simpler and cheaper but wrong for long washes?
5. **How many strata,** and whether a buried one is baked into the
   reflectance (huile's way) or kept as matter.
6. **Alcohol.** Should it be a second wetness in the fibres only, as
   proposed, or a second fluid on the surface too?
7. **The scale.** What the default `px_per_mm` is (huile is set at about 2),
   and whether fusain's grain is restated in millimetres when it moves.

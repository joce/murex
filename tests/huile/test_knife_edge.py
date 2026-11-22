"""A knife at the edge of the canvas (murex-duo).

The flow under a dragging blade let wet paint out over the edge of the
canvas, uncounted, and none in; what lay past the edge was the edge pixel,
still, whatever the blade did there. So the paint under a blade coming onto
the canvas, or set down across its edge, drained away from the edge, and
the blade laid its own in its place, more or less of it as its stroke was
cut into steps.

The steps of a knife's stroke that reach past the edge are now painted on a
stage (_knife._Stage, _Edge): the part of the canvas under them, and the
canvas going on past its edge as its mirror image. There a step is a step
like any other, so:

- what the stroke leaves on the canvas, and on the blade, is what the same
  stroke leaves on a larger canvas that goes on so, to rounding, whatever
  its steps;
- what the canvas and the knife lose over the edge, less what they gain
  there, is counted (``Canvas.edge_loss``), for every knife stroke.
"""

import pickle

import numpy as np
import pytest

import murex.huile.stroke as stm
from murex.huile import Brush, Canvas, Paint, _knife, brushes
from murex.huile import palette as P
from murex.huile._engine import IV, PACKED

DARK = Paint("#1c1a24")
S = 180  # the canvas, square: its four edges are one edge, turned
M = 110  # how much larger all round the canvas the strokes are compared on is
PLANES = ("top", "und", "top_a", "und_a", "top_id")
_PIGMENTS = np.stack(
    [np.concatenate([p.K, [p.S, 1.0]]) for p in (DARK, P.TITANIUM_WHITE)], axis=1
)
_SCALE = 1.0 / np.abs(_PIGMENTS).max(axis=1)
_GROUND: dict = {}

# The strokes, on a canvas turned so that the edge they meet is its top one
# (path, angle of the blade): a blade set down across the edge and pulled
# in; one coming on over the edge, its own edge along the canvas's and 5
# degrees off it; one pulled along the edge, half of it past it; one leaving
# over the edge; one coming on over a corner.
STROKES = {
    "down": ([(60, 6), (90, 36), (120, 66)], -45.0),
    "onto": ([(90, -40), (90, 20), (90, 80)], 0.0),
    "onto5": ([(90, -40), (90, 20), (90, 80)], 5.0),
    "along": ([(30, 0), (90, 0), (150, 0)], -90.0),
    "off": ([(90, 110), (90, 50), (90, -40)], 0.0),
    "corner": ([(-30, -30), (20, 20), (70, 70)], -45.0),
}


def _ground(kind):
    """A canvas S px square: ``"wet"``, with wet dark all over it as two
    pulls of a wide knife left it, 2.6 units thick on average, ragged where
    they end; ``"even"``, with the paint of its middle pixel everywhere;
    ``"bare"``, with none."""
    if kind not in _GROUND:
        c = Canvas(S, S, seed=1)
        if kind != "bare":
            for x in (45, 135):
                knife = Brush(brushes.knife("straight", 120, flex=0.5)).load(DARK, 5.0)
                c.stroke(
                    [(x, 8), (x, S - 8)],
                    None,
                    brush=knife,
                    angle=0,
                    follow_path=False,
                    pressure=0.7,
                    lift=0.0,
                    seed=1,
                )
        if kind == "even":
            for name in PLANES:
                plane = getattr(c, name)
                plane[...] = plane[S // 2, S // 2 + 3]
        _GROUND[kind] = c
    return _GROUND[kind].copy()


def _going_on(canvas):
    """A canvas M px larger all round than ``canvas``, which goes on past
    where that one ends as its mirror image: its paint, its weave and the
    maps of its relief."""
    big = Canvas(canvas.width + 2 * M, canvas.height + 2 * M, seed=1)
    for name in (*PLANES, "dry_height", "grain"):
        plane = getattr(canvas, name)
        pads = ((M, M), (M, M)) + ((0, 0),) * (plane.ndim - 2)
        getattr(big, name)[...] = np.pad(plane, pads, mode="symmetric")
    relief = canvas._relief()
    big._relief_maps = type(relief)(*(np.pad(m, M, mode="symmetric") for m in relief))
    big._stroke_counter = canvas._stroke_counter
    return big


def _turned(point, turns):
    x, y = point
    for _ in range(turns):
        x, y = S - y, x
    return float(x), float(y)


def _knifed(canvas, name, turns=0, step=8.0, pressure=0.5, shift=0.0, blade=60):
    """White knifed on ``canvas`` along the stroke ``name``, the canvas
    turned ``turns`` quarter turns under it, its steps ``step`` px at most
    (a stroke's: 8), every point ``shift`` px further right and down.
    Returns the blade."""
    path, angle = STROKES[name]
    knife = Brush(brushes.knife("straight", blade, flex=0.5))
    knife = knife.load(P.TITANIUM_WHITE, 0.3)
    longest = stm._MAX_STEP
    stm._MAX_STEP = step
    try:
        canvas.stroke(
            [tuple(np.add(_turned(p, turns), shift)) for p in path],
            None,
            brush=knife,
            angle=angle + 90.0 * turns,
            follow_path=False,
            pressure=pressure,
            lift=0.0,
            seed=3,
        )
    finally:
        stm._MAX_STEP = longest
    return knife


def _volumes(canvas):
    """The volume of dark and of white at each pixel, the two wet layers
    together."""
    a = (canvas.top.astype(np.float64) + canvas.und)[..., : IV + 1] * _SCALE
    sol, *_ = np.linalg.lstsq(
        _PIGMENTS * _SCALE[:, None], a.reshape(-1, IV + 1).T, rcond=None
    )
    sol = sol.T.reshape(a.shape[:2] + (2,))
    return sol[..., 0], sol[..., 1]


def _totals(canvas, brush):
    """Every channel: on the canvas and on the blade, and with them what
    has gone past the canvas's edge."""
    on = canvas.top.sum(axis=(0, 1), dtype=np.float64)
    on += canvas.und.sum(axis=(0, 1), dtype=np.float64)
    on += (brush.tip.astype(np.float64) + brush.reservoir + brush.heel).sum(0)
    return on, on + getattr(canvas, "edge_loss", 0.0)


CASES = [
    *(("wet", name, turns, 0.5) for name in ("down", "onto5") for turns in range(4)),
    *(("wet", name, 1, 0.5) for name in ("onto", "along", "off", "corner")),
    ("wet", "onto", 2, 0.9),
    ("wet", "off", 3, 0.25),
    ("bare", "onto", 0, 0.5),
    ("bare", "down", 3, 0.25),
]


@pytest.mark.parametrize("kind, name, turns, pressure", CASES)
def test_a_knife_at_the_edge_paints_as_on_a_canvas_that_goes_on(
    kind, name, turns, pressure
):
    """A knife set down across an edge of the canvas, coming on over it,
    pulled along it, leaving over it, or coming on over a corner, over wet
    paint and over bare canvas, at each of the four edges, in a stroke's
    own steps and in steps of 2 px: it leaves the paint as thick, pixel by
    pixel, as on a canvas 110 px larger all round that goes on past where
    this one ends as its mirror image, and as much on the blade.

    As thick to rounding, that is: every plane of the canvas is within 7e-4
    at its worst value in 31 of the 32 strokes here (the same to the bit in
    6). The other one, leaving over the right edge, is 0.14 off at its
    worst value (0.009 units of thickness), as the same stroke is on two
    larger canvases that differ by 2 px in how much larger they are: some
    decision of a knife's step hangs on a last bit of where the stroke
    lies, before the stage as with it.

    (It was not so by far. In their own steps the strokes here over wet
    paint laid 0.91 to 4.2 times the white that the larger canvas gets in
    the same window, coming on over an edge 3.2 to 4.2 times, and left the
    paint 0.36 to 4.9 units thicker or thinner at the worst pixel, 7e-4 to
    0.11 on average over the canvas; over bare canvas 0.12 to 0.51, and
    1e-4 to 2e-3.)"""
    for step in (8.0, 2.0):
        canvas = _ground(kind)
        larger = _going_on(canvas)
        blade = _knifed(canvas, name, turns, step, pressure)
        other = _knifed(larger, name, turns, step, pressure, shift=M)
        window = (slice(M, M + S), slice(M, M + S))
        off = np.abs(
            canvas.wet_thickness.astype(np.float64) - larger.wet_thickness[window]
        )
        assert off.max() < 0.05, (step, float(off.max()))
        assert off.mean() < 2e-5, (step, float(off.mean()))
        assert abs(blade.volume - other.volume) < 0.02
        np.testing.assert_array_equal(
            canvas.top_id == canvas._stroke_counter,
            larger.top_id[window] == larger._stroke_counter,
        )


def test_a_knife_wholly_on_the_canvas_is_painted_on_it(monkeypatch):
    """Only steps whose window reaches past the edge are painted on a stage:
    a stroke whose windows stay on the canvas is painted on the canvas
    itself, as ever (and so comes out the same to the bit as before there
    was a stage: tools/huile/bench.py --compare), and of a stroke that
    comes on over the edge, the stage holds what its steps reach until
    their windows are on the canvas, no more."""
    made = []
    stage = _knife._Stage

    def spy(*args):
        made.append(args[1:])
        return stage(*args)

    monkeypatch.setattr(_knife, "_Stage", spy)
    c = _ground("wet")
    made.clear()  # (the pulls that laid the ground, if this test is the first)
    path = [(60.0, 90.0), (120.0, 90.0)]
    knife = Brush(brushes.knife("straight", 60, flex=0.5)).load(P.TITANIUM_WHITE, 0.3)
    gone = c.edge_loss.copy()  # (by the pulls that laid the ground)
    c.stroke(path, None, brush=knife, angle=-90.0, follow_path=False, seed=3)
    assert not made
    np.testing.assert_array_equal(c.edge_loss, gone)
    _knifed(c, "onto")
    # (what its steps reach, and lay outside their windows, from 40 px past
    # the top edge until all they reach is on the canvas, 60 px in: the
    # stroke goes on to 80 px in, on the canvas)
    assert len(made) == 1
    y0, y1, x0, x1 = made[0]
    assert -128 < y0 < -90 and 90 < y1 < 140 and 0 < x0 < 40 and 140 < x1 < S
    assert c.edge_loss[IV] != gone[IV]


def test_paint_that_crosses_the_edge_under_a_knife_is_counted(same_textures):
    """Nothing is made or lost by a knife at the edge: the canvas, the
    blade and what the canvas counts as gone past its edge
    (``Canvas.edge_loss``) keep every channel, to 3e-8 of the largest. A
    blade leaving over the edge pushes wet paint off the canvas (1,630
    units here, of the 106,000 on the canvas, 30 of them its own); one
    coming on brings wet paint with it from past the edge, more than it
    lays out there of its own: the canvas and the blade end with 670 units
    more than they had, and the count is as much below nothing.

    (The flow let the paint out and counted none, and let none in: the
    blade leaving lost 1,790 units, and the canvas and the blade coming on
    110, the blade's own.)"""
    _ground("even")
    same_textures()
    gone = {}
    for name in ("off", "onto", "along", "corner", "down"):
        canvas = _ground("even")
        blade = Brush(brushes.knife("straight", 60, flex=0.5))
        # (with what the pulls that laid the ground moved past the edge)
        before, kept_before = _totals(canvas, blade.load(P.TITANIUM_WHITE, 0.3))
        blade = _knifed(canvas, name)
        after, kept = _totals(canvas, blade)
        np.testing.assert_allclose(kept, kept_before, rtol=0, atol=1e-6 * before.max())
        assert canvas.top.min() >= 0 and canvas.und.min() >= 0
        gone[name] = float((before - after)[IV])
    assert 1000 < gone["off"] < 2500
    assert -1100 < gone["onto"] < -300


def test_what_a_knife_loses_over_the_edge_is_counted_whatever_it_is_painted_on(
    monkeypatch, same_textures
):
    """``Canvas.edge_loss`` is what the canvas and the knife lost over a
    stroke, so the three keep every channel whichever way the paint left:

    - a blade leaving over the edge and going on 140 px, and 400 px, past
      it, further than a stage reaches (128 px): out there it lays its
      paint and drags none, and what it pushed that far is gone over the
      stage's own edge. The count is above nothing by what was pushed off
      (1,640 units at pressure 0.5, 6,760 at 0.9, of 106,000);
    - a blade pulled along the edge from 200 px before the canvas to 200 px
      after it;
    - a knife pulled along the top edge with every window on the canvas, so
      on no stage, whose end presses paint out over the edge (44 units).

    (The first count was what a stage held past the edge at the end, less
    before: a stroke that went beyond the stage, or was on none, lost paint
    it did not count, and the blade going 140 px out, which scrapes the
    stage's band past the edge clean on its way, counted 1,900 units
    brought on at pressure 0.5 while it pushed 7,600 off, on 240 px square
    and 3.6 units.)"""
    made = []
    stage = _knife._Stage

    def spy(*args):
        made.append(args[1:])
        return stage(*args)

    monkeypatch.setattr(_knife, "_Stage", spy)
    _ground("even")
    same_textures()
    off = {
        "to 140": ([(90.0, 120.0), (90.0, 0.0), (90.0, -140.0)], 0.0),
        "to 400": ([(90.0, 120.0), (90.0, 0.0), (90.0, -400.0)], 0.0),
        "along": ([(-200.0, 5.0), (90.0, 5.0), (380.0, 5.0)], -90.0),
    }
    lost = {}
    for name, (path, angle) in off.items():
        for pressure in (0.5, 0.9):
            canvas = _ground("even")
            blade = Brush(brushes.knife("straight", 60, flex=0.5))
            before, kept_before = _totals(canvas, blade.load(P.TITANIUM_WHITE, 0.3))
            made.clear()
            canvas.stroke(
                path,
                None,
                brush=blade,
                angle=angle,
                follow_path=False,
                pressure=pressure,
                lift=0.0,
                seed=3,
            )
            after, kept = _totals(canvas, blade)
            np.testing.assert_allclose(
                kept, kept_before, rtol=0, atol=1e-6 * before.max()
            )
            assert len(made) == 1 and -128 in made[0]  # (as far as a stage goes)
            lost[name, pressure] = float((before - after)[IV])
    assert 1000 < lost["to 140", 0.5] < 2500 and 4500 < lost["to 140", 0.9] < 9000
    assert 1000 < lost["to 400", 0.5] < 2500 and 600 < lost["along", 0.5] < 1400
    # (near the edge, on no stage)
    canvas = _ground("even")
    blade = Brush(brushes.KNIFE_STRAIGHT).load(P.TITANIUM_WHITE, 4.0)
    before, kept_before = _totals(canvas, blade)
    made.clear()
    canvas.stroke(
        [(50.0, 42.0), (130.0, 42.0)],
        None,
        brush=blade,
        angle=-90.0,
        follow_path=False,
        pressure=0.9,
        seed=4,
    )
    after, kept = _totals(canvas, blade)
    assert not made
    assert 15 < float((before - after)[IV]) < 120
    np.testing.assert_allclose(kept, kept_before, rtol=0, atol=1e-6 * before.max())


def test_a_long_knife_stroke_takes_the_memory_of_its_part_near_the_edge():
    """A knife pulled 890 px across a canvas 800 by 500 px, from well inside
    it to 60 px past its right edge, peaks at 20 MB: the stage for its last
    steps, whose windows reach past the edge (9 MB for all they reach, at
    0.25 KB a pixel), and the copies made of it. The steps before those are
    painted on the canvas. (One stage for the whole stroke held its
    bounding box, 104 MB here, and 4 GB for such a stroke across 4,000 by
    4,000 px.) A stroke of the same shape
    is painted first, on another canvas, so that no kernel is compiled in
    the measurement."""
    import tracemalloc

    def pull(canvas):
        knife = Brush(brushes.knife("straight", 60, flex=0.5))
        canvas.stroke(
            [(60.0, 60.0), (860.0, 440.0)],
            None,
            brush=knife.load(P.TITANIUM_WHITE, 3.0),
            angle=20.0,
            pressure=0.5,
            seed=3,
        )

    pull(Canvas(800, 500, seed=1))
    c = Canvas(800, 500, seed=1)
    tracemalloc.start()
    pull(c)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    assert c.edge_loss[IV] > 1.0
    assert peak < 30e6


def test_a_knife_coming_on_lays_what_it_lays_on_a_larger_canvas_of_its_own():
    """Against canvases that owe the stage nothing: white knifed onto the
    canvas over its top edge with a blade 110 px long at pressure 0.5, over
    3.3 units of even wet dark, on four canvases each with its own weave,
    and on four canvases 110 px larger all round, each with its own weave
    too and the same wet dark all over. The white that lands on the canvas
    is, on average, what lands in the same window of the larger ones
    (1.01 times), as nearly as one weave or another moves either (by up to
    1.1%). It was 1.19 times as much."""
    even = _ground("even")

    def white(size, seed, shift):
        c = Canvas(size, size, seed=seed)
        for name in PLANES:
            getattr(c, name)[...] = getattr(even, name)[0, 0]
        _knifed(c, "onto", shift=shift, blade=110)
        w = (slice(shift, shift + S), slice(shift, shift + S))
        return float(_volumes(c)[1][w].sum())

    here = [white(S, seed, 0) for seed in (11, 12, 13, 14)]
    there = [white(S + 2 * M, seed, M) for seed in (21, 22, 23, 24)]
    assert max(there) / min(there) < 1.04 and max(here) / min(here) < 1.04
    assert 0.97 < np.mean(here) / np.mean(there) < 1.03


def test_a_knife_coming_onto_the_canvas_leaves_the_paint_at_the_edge(same_textures):
    """White knifed onto the canvas over its top edge, over 3.3 units of
    wet dark, the blade's edge 5 degrees off the canvas's, with the same
    textures, in a stroke's own steps and in steps of 2 px and of 1 px: the
    wet dark it leaves in the first 8 px of the canvas, under its middle,
    is as thick as 30 px further in (0.98 to 1.01 times), and what it lays
    on the canvas is what it lays in the same window of a larger canvas
    (see _going_on), so it hangs on its steps as it does there and no more
    (in its own steps 1.16 times what it lays in steps of 1 px at pressure
    0.5, and 0.81 times at 0.25: what is left on a blade that has laid five
    sixths of its paint before it reaches the canvas).

    (It left the dark at the edge 0.55 to 0.70 times as thick as further
    in: what it dragged away from the edge, nothing came to replace. And it
    laid its own in its place: at pressure 0.5, 4.1, 1.9 and 2.6 times what
    the larger canvas gets, in steps of 8, 2 and 1 px, 1.8 times as much in
    its own steps as in steps of 1 px.)"""
    _ground("even")
    same_textures()
    window = (slice(M, M + S), slice(M, M + S))
    for pressure in (0.5, 0.25):
        white = {}
        for step in (8.0, 2.0, 1.0):
            canvas = _ground("even")
            larger = _going_on(canvas)
            _knifed(canvas, "onto5", 0, step, pressure)
            _knifed(larger, "onto5", 0, step, pressure, shift=M)
            dark, laid = _volumes(canvas)
            white[step] = float(laid.sum())
            there = float(_volumes(larger)[1][window].sum())
            assert 0.98 < white[step] / there < 1.02, (pressure, step)
            edge = float(dark[:8, 75:105].mean() / dark[30:38, 75:105].mean())
            assert 0.93 < edge < 1.07, (pressure, step, edge)
        assert 0.6 < white[8.0] / white[1.0] < 1.45, (pressure, white)


def test_a_stage_reaches_no_further_than_it_may(monkeypatch):
    """A stroke from far out is painted on a stage that reaches 128 px past
    the edge at most (_knife._STAGE_FAR): further out the blade lays its
    paint as it did before there was a stage, and uses it up."""
    made = []
    stage = _knife._Stage

    def spy(*args):
        made.append(args[1:])
        return stage(*args)

    monkeypatch.setattr(_knife, "_Stage", spy)
    c = _ground("wet")
    made.clear()  # (the pulls that laid the ground, if this test is the first)
    knife = Brush(brushes.knife("straight", 60, flex=0.5)).load(P.TITANIUM_WHITE, 0.3)
    held = knife.volume
    c.stroke(
        [(90.0, -600.0), (90.0, -300.0)], None, brush=knife, angle=0.0, seed=3
    )  # (all off the canvas: no stage, and it uses its paint up all the same)
    assert not made and knife.volume < 0.9 * held
    knife = Brush(brushes.knife("straight", 60, flex=0.5)).load(P.TITANIUM_WHITE, 3.0)
    c.stroke([(90.0, -600.0), (90.0, 90.0)], None, brush=knife, angle=0.0, seed=3)
    assert len(made) == 1 and made[0][0] == -128 and 60 < made[0][1] < S
    assert _volumes(c)[1].sum() > 5.0  # (it had some left for the canvas)


def test_a_stage_is_the_canvas_going_on_as_its_mirror_image():
    """Every plane of a stage is the canvas's, and past the canvas's edge
    its mirror image, the edge pixel first (numpy.pad's "symmetric"), also
    where the stage reaches further past an edge than the canvas is large
    and the image is mirrored again; what it is given of the canvas's
    random numbers, stroke ids and weave is the canvas's own; and putting
    it back changes only its part of the canvas."""
    for size, box in ((40, (-100, 70, -50, 120)), (90, (-30, 60, 20, 110))):
        c = Canvas(size, size, seed=2)
        rng = np.random.default_rng(5)
        for name in PLANES:
            plane = getattr(c, name)
            plane[...] = rng.random(plane.shape) * 3
        c.dry_height[...] = rng.random((size, size))
        c._update_relief()
        y0, y1, x0, x1 = box
        stage = _knife._Stage(c, *box)
        assert (stage.height, stage.width) == (y1 - y0, x1 - x0)

        def there(plane, box=box, size=size):
            m = 200
            pads = ((m, m), (m, m)) + ((0, 0),) * (plane.ndim - 2)
            y0, y1, x0, x1 = box
            return np.pad(plane, pads, mode="symmetric")[
                m + y0 : m + y1, m + x0 : m + x1
            ]

        for name in (*PLANES, "dry_height"):
            got = getattr(stage, name)
            assert got.flags.c_contiguous and got.dtype == getattr(c, name).dtype
            np.testing.assert_array_equal(got, there(getattr(c, name)), name)
        for got, plane in zip(stage._relief(), c._relief(), strict=True):
            np.testing.assert_array_equal(got, there(plane))
        np.testing.assert_array_equal(stage._weave_hollows(), there(c._weave_hollows()))
        np.testing.assert_array_equal(stage.top_v + stage.und_v, there(c.wet_thickness))
        assert stage._beyond_weave() == c._beyond_weave() and stage.surface is c.surface
        assert stage._stroke_rng(7).random() == c._stroke_rng(7).random()
        assert stage._new_stroke_id() == c._stroke_counter
        # (the canvas changes before the stage's steps are painted: its part
        # of the canvas is brought up to date, what is past the edge stays
        # as it was before the stroke)
        part = (slice(max(y0, 0), min(y1, size)), slice(max(x0, 0), min(x1, size)))
        on = np.zeros((size, size), bool)
        on[part] = True
        here = np.zeros((y1 - y0, x1 - x0), bool)
        here[stage._here] = True
        before = c.copy()
        c.top[...] += np.float32(2.0)
        stage.take()
        np.testing.assert_array_equal(stage.top[stage._here], c.top[part])
        np.testing.assert_array_equal(stage.top[~here], there(before.top)[~here])
        np.testing.assert_array_equal(stage.wet_before, there(before.wet_thickness))
        # (painted on: its part of the canvas goes back, the rest stays)
        stage.top[...] += np.float32(1.0)
        stage.put_back()
        np.testing.assert_array_equal(c.top[part], before.top[part] + np.float32(3.0))
        np.testing.assert_array_equal(c.top[~on], before.top[~on] + np.float32(2.0))
        np.testing.assert_array_equal(c.und, before.und)
        # (a later stage of the stroke takes what the stroke left past the
        # edge on this one, where they share it, and the canvas as it is)
        later = _knife._Stage(before, y0 + 7, y1 + 9, x0 - 5, x1 + 3)
        later.take([stage])
        shared = (slice(0, y1 - y0 - 7), slice(5, 5 + x1 - x0))
        past = ~here[7:, :]
        np.testing.assert_array_equal(later.top[shared][past], stage.top[7:, :][past])
        np.testing.assert_array_equal(later.top[later._here], before.top[later._there])


def test_a_canvas_keeps_what_went_past_its_edge():
    """``Canvas.edge_loss`` is copied with the canvas and pickled with it;
    a canvas pickled before it was counted loads with nothing gone."""
    c = _ground("wet")
    _knifed(c, "off")
    assert c.edge_loss.shape == (PACKED,) and c.edge_loss[IV] > 100.0
    for other in (c.copy(), pickle.loads(pickle.dumps(c))):
        np.testing.assert_array_equal(other.edge_loss, c.edge_loss)
        assert other.edge_loss is not c.edge_loss
    state = c.__getstate__()
    del state["edge_loss"]
    old = Canvas.__new__(Canvas)
    old.__setstate__(state)
    np.testing.assert_array_equal(old.edge_loss, 0.0)

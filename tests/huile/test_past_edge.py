"""Past the edge of the canvas (murex-duo, murex-n6o, murex-6s6, murex-w8r,
murex-uwl).

A canvas goes on past its edge: bare at first, and holding whatever strokes
leave there (``Canvas._past_edge``). The steps of a stroke, a brush's or a
knife's, that reach past the edge are painted on a stage, the canvas and
what lies past its edge as one surface (_knife._Stage, _Edge), and the
paint settles across the edge. So:

- strokes at the edge, one after another, leave the paint on the canvas,
  pixel by pixel, as the same strokes do on a larger canvas whose weave
  goes on as this one's own, over again, to rounding;
- and what they bring onto the canvas, or take off it, is what they do on
  larger canvases with weaves of their own;
- what crosses the edge under a knife is counted, and is out there as far
  as the canvas keeps anything (_knife._KEPT_FAR);
- paint dried past the edge raises the canvas's relief beside it, as on
  that larger canvas, and nowhere else;
- a canvas nothing is taken past the edge of keeps nothing, and is painted
  as it was, to the bit (tools/huile/bench.py --compare).

(Before any of this the flow under a blade let paint out over the edge and
none in. Then, murex-duo, past the edge was the canvas's mirror image, made
anew for every knife stroke and gone after it: paint nobody had laid lay
out there, again and again; the paint settled against the edge as against
a wall; a blade from further out than 128 px dragged nothing till there;
and brushes laid nothing past the edge at all.)
"""

import pickle
import tracemalloc

import numpy as np
import pytest

from murex.huile import Brush, Canvas, Paint, _knife, brushes, surfaces
from murex.huile import palette as P
from murex.huile._engine import IV

DARK = Paint("#1c1a24")
RED = Paint("#c03020")
S = 180  # the canvas, square: its four edges are one edge, turned
M = 130  # how much larger all round the canvas the strokes are compared on is
PLANES = ("top", "und", "top_a", "und_a", "top_id")
ALL = (slice(None), slice(None))
_PAIRS: dict = {}

# Paths, on a canvas turned so that the edge they meet is its top one: onto
# the canvas over the edge and off it again, through a corner, along the
# edge with half the tool past it, and set down across the edge.
ONTO = [(90.0, -40.0), (90.0, 20.0), (90.0, 80.0)]
OFF = ONTO[::-1]
CORNER = [(-30.0, -30.0), (20.0, 20.0), (70.0, 70.0)]
ALONG = [(30.0, 0.0), (90.0, 0.0), (150.0, 0.0)]
DOWN = [(60.0, 6.0), (90.0, 36.0), (120.0, 66.0)]
FAR = [(90.0, -300.0), (90.0, -40.0), (90.0, 80.0)]


def _going_on(canvas, margin=M):
    """A canvas ``margin`` px larger all round than the bare ``canvas``,
    whose weave goes on past where that one ends as its own, over again: its
    weave and the maps of its relief."""
    big = Canvas(canvas.width + 2 * margin, canvas.height + 2 * margin, seed=1)
    big.grain[...] = np.pad(canvas.grain, margin, mode="wrap")
    relief = canvas._relief()
    big._relief_maps = type(relief)(*(np.pad(m, margin, mode="wrap") for m in relief))
    big.__dict__.pop("_weave_hollows_map", None)
    return big


def _turned(point, turns):
    x, y = point
    for _ in range(turns):
        x, y = S - y, x
    return float(x), float(y)


def _knife_pull(path, angle=0.0, load=0.0, blade=60, paint=P.TITANIUM_WHITE, **options):
    """A knife pulled along ``path``, clean or loaded: what paints it on a
    canvas turned ``turns`` quarter turns under it, every point ``shift`` px
    further right and down, and returns the tool."""
    options.setdefault("pressure", 0.5)
    options.setdefault("seed", 3)

    def paint_on(canvas, shift=0.0, turns=0):
        knife = Brush(brushes.knife("straight", blade, flex=0.5))
        if load > 0:
            knife = knife.load(paint, load)
        return canvas.stroke(
            [tuple(np.add(_turned(p, turns), shift)) for p in path],
            None,
            brush=knife,
            angle=angle + 90.0 * turns,
            follow_path=False,
            lift=0.0,
            **options,
        )

    return paint_on


def _brush_pull(path, paint=RED, amount=8.0, tool=None, **options):
    """A brush pulled along ``path`` (see :func:`_knife_pull`)."""
    options.setdefault("seed", 5)

    def paint_on(canvas, shift=0.0, turns=0):
        return canvas.stroke(
            [tuple(np.add(_turned(p, turns), shift)) for p in path],
            paint,
            amount=amount,
            brush=brushes.FLAT_HOG.sized(50) if tool is None else tool,
            **options,
        )

    return paint_on


def _taps(points, **options):
    def paint_on(canvas, shift=0.0, turns=0):
        at = [tuple(np.add(_turned(p, turns), shift)) for p in points]
        return canvas.stipple(at, RED, seed=7, **options)

    return paint_on


def _dry(canvas, shift=0.0, turns=0):
    """The paint dries (in a series of strokes: see SERIES)."""
    canvas.dry()
    return Brush(brushes.ROUND_HOG)  # (a clean tool: nothing to compare)


# The grounds, laid by strokes: three pulls of a flat brush down the canvas
# that run 30 px over its top and bottom edges; two pulls of a wide knife
# that stop 8 px inside them; none.
GROUNDS = {
    "brushed": [
        _brush_pull(
            [(x, -30.0), (x, S + 30.0)],
            DARK,
            14.0,
            brushes.FLAT_HOG.sized(70),
            pressure=0.6,
            seed=1 + i,
        )
        for i, x in enumerate((30.0, 90.0, 150.0))
    ],
    "knifed": [
        _knife_pull(
            [(x, 8.0), (x, S - 8.0)],
            load=5.0,
            blade=120,
            paint=DARK,
            pressure=0.7,
            seed=1,
        )
        for x in (45.0, 135.0)
    ],
    "bare": [],
}
# Strokes one after another at an edge.
SERIES = {
    "knife on": [_knife_pull(ONTO, seed=10 + i) for i in range(3)],
    "knife on, wide and light": [
        _knife_pull(ONTO, blade=110, pressure=0.25, seed=10 + i) for i in range(2)
    ],
    "knife on, loaded": [_knife_pull(ONTO, load=3.0, seed=10 + i) for i in range(2)],
    "knife off and on": [
        _knife_pull((OFF, ONTO)[i % 2], pressure=0.9, seed=10 + i) for i in range(4)
    ],
    "knife through a corner": [
        _knife_pull((CORNER[::-1], CORNER)[i % 2], -45.0, seed=10 + i) for i in range(3)
    ],
    "knife along": [
        _knife_pull((ALONG, ALONG[::-1])[i % 2], -90.0, load=0.3, seed=10 + i)
        for i in range(2)
    ],
    "knife set down": [
        _knife_pull(DOWN, -45.0, load=0.3, seed=10 + i) for i in range(2)
    ],
    "knife side by side": [
        _knife_pull([(x + dx, y) for x, y in (OFF, ONTO)[i % 2]], seed=10 + i)
        for i, dx in enumerate((-30, -10, 10, 30))
    ],
    # (barely touching: the roll of the blade's edge reads the surface as it
    # lay before the stroke, past the edge too; murex-dnj)
    "skim on and off": [
        _knife_pull((ONTO, OFF)[i % 2], load=3.0, pressure=0.03, seed=10 + i)
        for i in range(3)
    ],
    "skim through a corner": [
        _knife_pull(
            (CORNER[::-1], CORNER)[i % 2], -45.0, load=3.0, pressure=0.03, seed=10 + i
        )
        for i in range(2)
    ],
    "skim along": [
        _knife_pull(
            (ALONG, ALONG[::-1])[i % 2],
            -90.0,
            load=3.0,
            pressure=[0.02, 0.06],
            seed=10 + i,
        )
        for i in range(2)
    ],
    "knife stopped at the edge": [
        _knife_pull([(90.0, 120.0), (90.0, 50.0), (90.0, 6.0)], load=4.0, pressure=0.9),
        _knife_pull(
            [(60.0, 120.0), (60.0, 50.0), (60.0, -3.0)], load=4.0, pressure=0.9
        ),
    ],
    "brush off and on": [
        _brush_pull([(90.0, 70.0), (90.0, -50.0)]),
        _brush_pull([(70.0, -50.0), (75.0, 60.0)], P.TITANIUM_WHITE, seed=6),
    ],
    "brush along": [
        _brush_pull([(20.0, 0.0), (160.0, 0.0)]),
        _brush_pull([(160.0, 12.0), (20.0, 12.0)], P.TITANIUM_WHITE, seed=6),
    ],
    "brushes at a corner": [
        _brush_pull([(60.0, 60.0), (-20.0, -25.0)], tool=brushes.ROUND_HOG),
        _brush_pull([(-15.0, 40.0), (50.0, -10.0)], tool=brushes.FILBERT_HOG, seed=6),
        _taps([(2.0, 60.0), (-3.0, 80.0), (5.0, 100.0), (90.0, -2.0)]),
    ],
    "knife off, dry, knife on": [
        _knife_pull(OFF, blade=110, pressure=0.9, seed=10),
        _knife_pull(OFF, blade=110, pressure=0.9, seed=11),
        _dry,
        _knife_pull(ONTO, load=0.3, blade=110, pressure=0.9, seed=12),
        _brush_pull(
            [(60.0, -40.0), (70.0, 60.0)], P.TITANIUM_WHITE, amount=3.0, seed=6
        ),
    ],
    "knife off, brush along, knife on": [
        _knife_pull(OFF, pressure=0.9, seed=10),
        _brush_pull([(30.0, 0.0), (150.0, 0.0)]),
        _knife_pull(ONTO, pressure=0.9, seed=12),
    ],
}
CASES = [
    *(("brushed", name, 0) for name in SERIES),
    ("knifed", "knife on", 1),
    ("knifed", "skim on and off", 1),
    ("bare", "skim on and off", 3),
    ("knifed", "knife off and on", 2),
    ("knifed", "brush off and on", 3),
    ("bare", "knife on, loaded", 0),
    ("bare", "brushes at a corner", 2),
    ("brushed", "knife through a corner", 1),
]


def _pair(ground, turns=0, margin=M):
    """A canvas S px square and a canvas ``margin`` px larger all round
    whose weave goes on as the first one's own, over again (see
    :func:`_going_on`), both painted with the strokes of the ``ground``."""
    key = (ground, turns, margin)
    if key not in _PAIRS:
        canvas = Canvas(S, S, seed=1)
        larger = _going_on(canvas, margin)
        for stroke in GROUNDS[ground]:
            stroke(canvas, 0.0, turns)
            stroke(larger, float(margin), turns)
        _PAIRS[key] = (canvas, larger)
    canvas, larger = _PAIRS[key]
    return canvas.copy(), larger.copy()


def _same(canvas, larger, margin=M, loose=False):
    """Whether the paint lies on ``canvas`` as in its window of ``larger``:
    within 2e-3 units at the worst pixel and 1e-6 on average. (``loose``:
    within 0.05 and 2e-5. Two larger canvases that differ by 2 px in how
    much larger they are differ by up to 0.02 units at a few pixels after
    some knife strokes: some decision of a knife's step hangs on a last bit
    of where the stroke lies, murex-088, on any canvas.)"""
    window = (slice(margin, margin + S), slice(margin, margin + S))
    off = np.abs(canvas.wet_thickness.astype(np.float64) - larger.wet_thickness[window])
    np.testing.assert_array_equal(
        canvas.top_id == canvas._stroke_counter,
        larger.top_id[window] == larger._stroke_counter,
    )
    most, mean = (0.05, 2e-5) if loose else (2e-3, 1e-6)
    return off.max() < most and off.mean() < mean, float(off.max())


def _wet(canvas):
    """The wet paint on the canvas, channel by channel."""
    return canvas.top.sum(axis=(0, 1), dtype=np.float64) + canvas.und.sum(
        axis=(0, 1), dtype=np.float64
    )


def _volume(canvas, window=ALL):
    return float(canvas.wet_thickness[window].sum(dtype=np.float64))


def _held(brush):
    return (brush.tip.astype(np.float64) + brush.reservoir + brush.heel).sum(axis=0)


def _kept(canvas):
    """The wet paint the canvas keeps past its edge, channel by channel."""
    paint = np.zeros(canvas.top.shape[-1])
    for top, und, *_ in canvas._past_edge.values():
        paint += top.sum(axis=(0, 1), dtype=np.float64)
        paint += und.sum(axis=(0, 1), dtype=np.float64)
    return paint


@pytest.mark.parametrize("ground, name, turns", CASES)
def test_strokes_at_the_edge_paint_as_on_a_larger_canvas(ground, name, turns):
    """Strokes one after another at an edge of the canvas, over a ground
    that brushes laid running over the edges, one that knives laid inside
    them, or none: knife pulls onto the canvas and off it, through a
    corner, along the edge, set down across it, on tracks side by side,
    stopped at the edge with a heap of paint; brush strokes off the canvas
    and onto it, along the edge, round a corner, taps at the edge; knives
    and brushes in turn; and a knife and a brush coming on over paint that
    has dried past the edge. After the ground and after every stroke the
    paint lies as thick, pixel by pixel, as after the same strokes on a
    canvas 130 px larger all round whose weave goes on as this one's own,
    over again, the same paint lies on top, and the tool holds as much: to
    rounding (1e-5 units at the worst pixel; in one case here, a loaded
    knife pulled twice onto the bare canvas, 0.018 units, as between two
    larger canvases 2 px apart in size: see :func:`_same`).

    (On the mirror image of the canvas, kept for no longer than a stroke,
    with the paint settling on the canvas alone and brushes laying nothing
    past the edge, the paint was up to 6 units off at the worst pixel from
    the second stroke on.)"""
    # (the one case here where murex-088 shows: see _same)
    loose = (ground, name, turns) == ("bare", "knife on, loaded", 0)
    canvas, larger = _pair(ground, turns)
    same, off = _same(canvas, larger)
    assert same, ("ground", off)
    for i, stroke in enumerate(SERIES[name]):
        tool = stroke(canvas, 0.0, turns)
        other = stroke(larger, float(M), turns)
        same, off = _same(canvas, larger, loose=loose)
        assert same, (i, off)
        assert abs(tool.volume - other.volume) < 2e-3, i


def test_a_knife_from_far_out_paints_as_on_a_larger_canvas():
    """A knife pulled onto the canvas from 300 px out, where the canvas
    keeps nothing from one stroke to the next (_knife._KEPT_FAR), over a
    ground brushes laid: its whole way is painted, on stages one after
    another, and the paint on the canvas lies as on a canvas 420 px larger
    all round, pixel by pixel (within 2e-3), after the pull and after the
    same pull again. Afterwards the canvas keeps nothing further out than
    it keeps anything, and no stage was larger than a stage may be.

    (A stage reached 128 px at most, and further out the blade laid its
    paint and dragged none: from 300 px out it laid 53% less white on the
    canvas to 165% more, murex-uwl.)"""
    made = []
    stage = _knife._Stage

    def spy(*args, **kw):
        if kw.get("relief", True):
            made.append(args[1:])
        return stage(*args, **kw)

    canvas, larger = _pair("brushed", margin=420)
    try:
        _knife._Stage = spy
        for i, load in enumerate((0.3, 0.0)):
            pull = _knife_pull(FAR, load=load, blade=110, seed=30 + i)
            tool = pull(canvas)
            _knife._Stage = stage
            other = pull(larger, 420.0)
            _knife._Stage = spy
            same, off = _same(canvas, larger, 420)
            assert same, (i, off)
            assert abs(tool.volume - other.volume) < 2e-3
    finally:
        _knife._Stage = stage
    assert len(made) > 2
    areas = [(y1 - y0) * (x1 - x0) for y0, y1, x0, x1 in made]
    assert max(areas) <= 2.2 * min(areas) and max(areas) < 3 * _knife._STAGE_AREA
    assert canvas._past_edge
    assert not any(_knife._kept_far(key, S, S) for key in canvas._past_edge)


def _brushed(lo):
    """The strokes of a ground: three pulls of a flat brush down the canvas,
    from ``lo`` px inside its top edge (below 0: past it) to as far from its
    bottom edge."""
    return [
        _brush_pull(
            [(x, lo), (x, S - lo)],
            DARK,
            14.0,
            brushes.FLAT_HOG.sized(70),
            pressure=0.6,
            seed=1 + i,
        )
        for i, x in enumerate((30.0, 90.0, 150.0))
    ]


# Strokes on canvases of their own weave (the ground, the strokes, how much
# larger the larger canvas is, and how far apart the two may end, as a share
# of the most the strokes move): each of the ways the edge went wrong, and
# brushes.
OWN = {
    # the edge was a source of paint (murex-n6o)
    "knife pulls on": (
        -40.0,
        [_knife_pull(ONTO, blade=110, seed=10 + i) for i in range(5)],
        M,
    ),
    "knife off and on": (
        -40.0,
        [
            _knife_pull((OFF, ONTO)[i % 2], blade=110, pressure=0.9, seed=10 + i)
            for i in range(4)
        ],
        M,
    ),
    # paint nobody laid lay past the edge (murex-6s6)
    "ground inside the edges": (
        8.0,
        [_knife_pull(ONTO, blade=110, seed=10 + i) for i in range(2)],
        M,
    ),
    # the paint settled against the edge (murex-w8r)
    "knife stopped at the edge": (
        -40.0,
        [
            _knife_pull(
                [(90.0, 120.0), (90.0, 50.0), (90.0, 6.0)], load=4.0, pressure=0.9
            )
        ],
        M,
    ),
    # a knife from far out dragged nothing on its way (murex-uwl)
    "knife from far out": (
        -40.0,
        [
            _knife_pull(FAR, load=0.3 * (i == 0), blade=110, pressure=0.9, seed=30 + i)
            for i in range(2)
        ],
        420,
    ),
    # brushes laid nothing past the edge
    "brushes at the edge": (
        -40.0,
        [
            _brush_pull([(90.0, 70.0), (90.0, -50.0)]),
            _brush_pull([(20.0, 0.0), (160.0, 0.0)], P.TITANIUM_WHITE, seed=6),
            _knife_pull(ONTO, blade=110, pressure=0.9, seed=12),
        ],
        M,
    ),
    "brush from far out": (
        8.0,
        [
            _brush_pull([(90.0, -120.0), (90.0, 100.0)], amount=10.0, pressure=0.6),
            _knife_pull(ONTO, blade=110, pressure=0.9, seed=12),
        ],
        M + 60,
    ),
}


@pytest.mark.parametrize("name", list(OWN))
def test_strokes_bring_on_what_they_do_on_a_larger_canvas_of_its_own(name):
    """Against canvases that owe the canvas nothing, each with a weave of
    its own, painted with the same strokes from the bare canvas on. Over a
    ground that brushes laid running 40 px over the top and bottom edges
    (or stopping 8 px inside them), each of the ways the edge went wrong:
    a clean knife pulled onto the canvas five times over one track, and off
    it and on again; pulled on over the ground laid inside the edges, where
    there is nothing out there to bring on; a loaded knife stopped at the
    edge, whose heap slumps over it; a knife pulled on from 300 px out,
    twice; brushes pulled off the canvas and along its edge, and a knife on
    after them; a brush pulled on from 120 px out, and a knife after it.
    What the strokes bring onto the canvas, or take off it, stroke by
    stroke, is what they do in the same window of the larger canvas: within
    2% of the most any of them moves, or 30 units.

    (Past the edge lay the canvas's mirror image, anew for every knife
    stroke, and nothing a brush had laid: the five pulls brought on 1.8
    times the paint, the pulls over the ground laid inside 1,400 to 1,700
    units each for none, and the knife from far out 1.7 to 7 times the
    paint.)"""
    lo, strokes, margin = OWN[name]
    window = (slice(margin, margin + S), slice(margin, margin + S))
    here = Canvas(S, S, seed=11)
    there = Canvas(S + 2 * margin, S + 2 * margin, seed=21)
    for ground in _brushed(lo):
        ground(here)
        ground(there, float(margin))
    start, start_there = _volume(here), _volume(there, window)
    assert abs(start - start_there) < 0.01 * start
    on, larger = [start], [start_there]
    for stroke in strokes:
        stroke(here)
        stroke(there, float(margin))
        on.append(_volume(here))
        larger.append(_volume(there, window))
    on, larger = np.diff(on), np.diff(larger)
    slack = max(0.02 * np.abs(larger).max(), 30.0)
    np.testing.assert_allclose(on, larger, rtol=0, atol=slack)


def test_a_stroke_at_the_edge_paints_the_same_every_time():
    """A brush stroke that starts at the left edge of the canvas over thick
    wet paint, painted on forty copies of the canvas with other memory
    taken in between: the same every time, to the bit. (What a brush meets
    round its window was read where the stroke can reach, which goes on
    past the canvas and past the stage a step is painted on: memory that
    was not the canvas's, and six to eight different results in forty.)"""
    base = Canvas(160, 160, seed=1)
    for i, y in enumerate((20, 60, 100, 140)):
        base.stroke(
            [(-30, y), (190, y)],
            P.BURNT_UMBER,
            amount=20,
            brush=brushes.FLAT_HOG.sized(60),
            pressure=0.6,
            seed=i + 1,
        )
    rng = np.random.default_rng(0)
    junk, seen = [], set()
    for _ in range(40):
        junk.append(np.full(int(rng.integers(1, 5000)), 7.0, np.float32))
        c = base.copy()
        brush = Brush(brushes.FLAT_HOG.sized(28)).load(P.TITANIUM_WHITE, 6.0)
        c.stroke([(6.8, 40.0), (54.4, 91.0)], brush=brush, pressure=0.6, seed=9)
        seen.add(c.top.tobytes() + c.und.tobytes())
    assert len(seen) == 1


def test_what_crosses_the_edge_under_a_knife_is_counted_and_is_out_there():
    """Over knife strokes one after another at an edge, the canvas, the
    blade and the count of what crossed the edge (``Canvas.edge_loss``)
    keep every channel at every stroke, to 1e-6 of the largest; and so do
    the canvas, the blade and what the canvas keeps past its edge: what
    leaves the canvas is out there, and what comes on is taken from there.
    The canvas never keeps less than nothing of anything.

    A blade that goes further out than the canvas keeps anything loses what
    it leaves out there: the canvas, the blade and what is kept end with
    less, the count says how much left the canvas, and nothing is kept
    further out."""
    specs = [
        (OFF, 0.0, 0.0, 0.5),
        (ONTO, 0.0, 0.0, 0.5),
        (OFF, 0.0, 3.0, 0.9),
        (ONTO, 0.0, 0.0, 0.9),
        (ALONG, -90.0, 2.0, 0.5),
        (CORNER, -45.0, 0.0, 0.5),
    ]
    canvas, _ = _pair("brushed")
    most = 0.0
    for i, (path, angle, load, pressure) in enumerate(specs):
        knife = Brush(brushes.knife("straight", 60, flex=0.5))
        if load > 0:
            knife = knife.load(P.TITANIUM_WHITE, load)
        before = _wet(canvas) + _held(knife)
        count, kept = canvas.edge_loss.copy(), _kept(canvas)
        canvas.stroke(
            path,
            None,
            brush=knife,
            angle=angle,
            follow_path=False,
            pressure=pressure,
            lift=0.0,
            seed=10 + i,
        )
        scale = 1e-6 * before.max()
        lost = canvas.edge_loss - count
        after = _wet(canvas) + _held(knife)
        np.testing.assert_allclose(after + lost, before, rtol=0, atol=scale)
        np.testing.assert_allclose(_kept(canvas) - kept, lost, rtol=0, atol=scale)
        most = max(most, abs(lost[IV]))
        for tile in canvas._past_edge.values():
            assert tile[0].min() >= 0 and tile[1].min() >= 0
    assert most > 1000.0
    # (further out than is kept)
    count, kept = canvas.edge_loss.copy(), _kept(canvas)
    _knife_pull(FAR[::-1], load=3.0, pressure=0.9)(canvas)
    lost = (canvas.edge_loss - count)[IV]
    assert lost > 1000.0 and (_kept(canvas) - kept)[IV] < lost - 50.0
    assert not any(_knife._kept_far(key, S, S) for key in canvas._past_edge)


def test_a_knife_keeps_every_pigment_with_what_crosses_the_edge():
    """A loaded knife at the edge: what it held and what lay on the canvas
    is, afterwards, on the canvas, on the blade or counted as gone over the
    edge (``Canvas.edge_loss``), every channel, to 1e-6 of the largest."""
    for path, angle in ((OFF, 0.0), (ONTO, 0.0), (ALONG, -90.0), (CORNER, -45.0)):
        canvas, _ = _pair("brushed")
        knife = Brush(brushes.knife("straight", 60, flex=0.5))
        knife = knife.load(P.TITANIUM_WHITE, 2.0)
        before = _wet(canvas) + _held(knife) + canvas.edge_loss
        canvas.stroke(
            path, None, brush=knife, angle=angle, follow_path=False, lift=0.0, seed=3
        )
        after = _wet(canvas) + _held(knife) + canvas.edge_loss
        np.testing.assert_allclose(after, before, rtol=0, atol=1e-6 * before.max())
        assert canvas.top.min() >= 0 and canvas.und.min() >= 0


def test_paint_dries_past_the_edge_too():
    """When the paint dries, what the canvas keeps past its edge dries
    where it lies: it is no wet paint any more, and a knife coming on
    afterwards rests on it. Two pulls off the canvas at pressure 0.9 leave
    a heap past the edge; once dry, a loaded knife pulled on over it lays
    the white on the canvas that it lays on a larger canvas of its own
    weave painted, and dried, the same, within 4%: over six weaves the
    canvas gets 494 to 508 units, and over four weaves each a canvas 260 px
    larger all round 491 to 504, one 400 px larger 499 to 512 (and one 130
    px larger 521 to 551).

    (The paint past the edge was forgotten as it dried, and the dried paint
    out there was the mirror image of the canvas's, scraped thin: the knife
    laid a third to two thirds of what it lays on the larger canvas.)"""
    pigments = np.stack(
        [np.concatenate([p.K, [p.S, 1.0]]) for p in (DARK, P.TITANIUM_WHITE)], axis=1
    )
    scale = 1.0 / np.abs(pigments).max(axis=1)

    def white(canvas, window):
        a = (canvas.top.astype(np.float64) + canvas.und)[window][..., : IV + 1] * scale
        sol, *_ = np.linalg.lstsq(
            pigments * scale[:, None], a.reshape(-1, IV + 1).T, rcond=None
        )
        return float(sol[1].sum())

    laid = {}
    for where, size, shift, seed in (
        ("canvas", S, 0, 11),
        ("larger", S + 520, 260, 21),
    ):
        canvas = Canvas(size, size, seed=seed)
        for stroke in GROUNDS["brushed"]:
            stroke(canvas, float(shift))
        for i in range(2):
            _knife_pull(OFF, blade=110, pressure=0.9, seed=10 + i)(canvas, float(shift))
        if where == "canvas":
            assert _kept(canvas)[IV] > 1000.0
        canvas.dry()
        if where == "canvas":
            assert _kept(canvas)[IV] == 0.0
            assert sum(float(t[-1].sum()) for t in canvas._past_edge.values()) > 1000.0
        _knife_pull(ONTO, load=0.3, blade=110, pressure=0.9, seed=12)(
            canvas, float(shift)
        )
        laid[where] = white(canvas, (slice(shift, shift + S), slice(shift, shift + S)))
    assert laid["larger"] > 50.0
    assert abs(laid["canvas"] / laid["larger"] - 1.0) < 0.04, laid


def test_the_paint_settles_the_same_however_it_is_cut(monkeypatch):
    """The paint that settles across the edge after a stroke settles in
    pieces (_knife._settling_boxes): in strips along the edges, with the
    canvas settling alone besides, where the stroke reaches deep into the
    canvas, or all of it in one strip where it does not; each strip cut
    into pieces of about _knife._SETTLE_AREA px. What comes out is the
    same to the bit however it is cut: pieces of 64,000, 16,000 and 1,500
    px, and both ways forced wherever they are sound (the deep way takes
    80 px of canvas between two opposite strips, four times
    _knife._SETTLE_REACH, which _knife._SETTLE_DEEP may not go below).
    Thick strokes down from past the top edge, along it, through a corner
    with a knife and along the left edge with one, on 260 by 200 px."""
    assert _knife._SETTLE_DEEP >= 4 * _knife._SETTLE_REACH
    taken = []
    boxes = _knife._settling_boxes

    def spy(canvas, reach):
        found, deep = boxes(canvas, reach)
        taken.append((deep, len(found)))
        return found, deep

    monkeypatch.setattr(_knife, "_settling_boxes", spy)

    def painted(area, deep):
        monkeypatch.setattr(_knife, "_SETTLE_AREA", area)
        monkeypatch.setattr(_knife, "_SETTLE_DEEP", deep)
        taken.clear()
        c = Canvas(260, 200, seed=2)
        flat = brushes.FLAT_HOG
        c.stroke(
            [(60, -50), (60, 190)],
            DARK,
            amount=30,
            brush=flat.sized(50),
            pressure=0.9,
            seed=1,
        )
        c.stroke(
            [(-40, 8), (300, 10)],
            RED,
            amount=40,
            brush=flat.sized(60),
            pressure=0.9,
            seed=2,
        )
        knife = Brush(brushes.knife("straight", 60)).load(P.TITANIUM_WHITE, 6.0)
        c.stroke([(-30, -30), (70, 70)], brush=knife, pressure=0.9, seed=3)
        knife = Brush(brushes.knife("straight", 60)).load(P.TITANIUM_WHITE, 6.0)
        c.stroke([(6, 230), (9, -30)], brush=knife, pressure=0.8, seed=4)
        return c, list(taken)

    usual, ways = painted(64_000, 160)
    assert [deep for deep, _ in ways] == [True, False, False, False]
    assert _kept(usual)[IV] > 100.0
    seen = set(ways)
    for area, deep in (
        (16_000, 160),
        (1_500, 160),
        (64_000, 80),
        (1_500, 80),
        (64_000, 10**6),
        (1_500, 10**6),
    ):
        other, ways = painted(area, deep)
        seen.update(ways)
        # (the deep way for two of the strokes at 80 px, and for none)
        assert sum(way for way, _ in ways) == {160: 1, 80: 2, 10**6: 0}[deep]
        for name in PLANES:
            np.testing.assert_array_equal(getattr(other, name), getattr(usual, name))
        assert sorted(other._past_edge) == sorted(usual._past_edge)
        for key, tile in usual._past_edge.items():
            for mine, there in zip(other._past_edge[key], tile, strict=True):
                np.testing.assert_array_equal(mine, there)
        # (the count of what crossed the edge under the knives, to 1e-7 of
        # it: it takes in what the settling itself rounds off where a piece
        # is put back, and not where the canvas settles alone)
        most = float(np.abs(usual.edge_loss).max())
        np.testing.assert_allclose(
            other.edge_loss, usual.edge_loss, rtol=0, atol=1e-7 * most
        )
    # (and in several pieces: a strip that holds all a stroke reached, in
    # five; a strip of the deep way, in three)
    assert (False, 5) in seen and (True, 3) in seen


def test_paint_dried_past_one_edge_changes_nothing_away_from_it():
    """A dab over the left edge, dried: the maps of the canvas's relief are
    those of the same canvas with nothing past its edge, to the bit,
    everywhere but beside the dab (where they are not: the heap out there
    stands beside the canvas), and a dry brush pulled across the middle
    afterwards paints the same, to the bit.

    (The canvas's relief was worked out again all over, with what lies
    round the canvas, as soon as anything had dried past its edge: the
    tooth, measured against other bounds, changed at every pixel, the other
    maps along every edge, and that stroke in the middle with them.)"""
    with_speck = Canvas(300, 240, seed=3)
    with_speck.stroke(
        [(100, 120), (200, 120)],
        P.BURNT_UMBER,
        amount=10,
        brush=brushes.FLAT_HOG.sized(60),
        seed=1,
    )
    with_speck.stroke(
        [(2, 120), (3, 121)],
        P.CADMIUM_RED,
        amount=6,
        brush=brushes.ROUND_HOG.sized(12),
        seed=2,
    )
    assert _kept(with_speck)[IV] > 5.0
    without = with_speck.copy()
    without._past_edge.clear()
    for canvas in (with_speck, without):
        canvas.dry()
    assert sum(float(t[-1].sum()) for t in with_speck._past_edge.values()) > 5.0
    beside = np.zeros((240, 300), bool)
    beside[60:180, :60] = True
    differ = 0
    for mine, alone in zip(with_speck._relief(), without._relief(), strict=True):
        np.testing.assert_array_equal(mine[~beside], alone[~beside])
        differ += int((mine[beside] != alone[beside]).sum())
    assert differ > 20
    for canvas in (with_speck, without):
        canvas.stroke(
            [(120, 60), (240, 180)],
            P.TITANIUM_WHITE,
            amount=0.6,
            brush=brushes.FLAT_HOG.sized(40),
            pressure=0.25,
            seed=5,
        )
    assert with_speck.wet_thickness.sum() > 50.0
    for name in PLANES:
        np.testing.assert_array_equal(getattr(with_speck, name), getattr(without, name))


@pytest.mark.parametrize("scale, out", [(18.0, 0), (40.0, 40)])
def test_a_heap_dried_past_the_edge_raises_the_canvas_beside_it(scale, out):
    """Wherever a heap dried past the edge, ``out`` px from it, changes the
    relief of a larger canvas (its weave the canvas's own, going on; the
    tooth measured as the canvas's), the canvas has that relief: as far
    from the heap as the maps read the surface, which is further the
    larger the weave (32 and 65 px, with threads 18 and 40 px apart; a
    heap further out than 32 px was not seen, whatever the weave)."""
    H, W, m = 160, 200, 120
    canvas = Canvas(W, H, seed=3, surface=surfaces.GESSO_PANEL.with_(scale=scale))
    # (the heap, written in by hand: 8 px square, 3 units high)
    x0 = -out - 8
    key = (5, x0 // _knife._KEPT_TILE)
    tile = canvas._past_edge[key] = _knife._bare_tile(canvas)
    at = x0 - key[1] * _knife._KEPT_TILE
    tile[-1][4:12, at : at + 8] = 3.0
    canvas._update_relief()
    grain = np.pad(canvas.grain, m, mode="wrap")
    bare = np.zeros_like(grain)
    heap = bare.copy()
    heap[m + 84 : m + 92, m + x0 : m + x0 + 8] = 3.0
    span = canvas._tooth_range()
    with_heap, _ = canvas._relief_of(grain, heap, span)
    without, _ = canvas._relief_of(grain, bare, span)
    window = (slice(m, m + H), slice(m, m + W))
    reached = 0
    for mine, there, flat in zip(canvas._relief(), with_heap, without, strict=True):
        changed = np.abs(there[window].astype(np.float64) - flat[window]) > 1e-6
        np.testing.assert_allclose(mine[changed], there[window][changed], atol=2e-6)
        reached = max(reached, int(changed.any(axis=0).sum()))
    assert reached > 20


def test_a_canvas_nothing_is_taken_past_the_edge_of_keeps_nothing():
    """Strokes that stay clear of the edge are painted on the canvas alone:
    no stage is made, nothing is kept past the edge, and a knife's count of
    what crossed the edge stays as it was."""
    made = []
    stage = _knife._Stage

    def spy(*args, **kw):
        made.append(args[1:])
        return stage(*args, **kw)

    c = Canvas(S, S, seed=1)
    try:
        _knife._Stage = spy
        c.stroke([(60, 60), (120, 110)], RED, amount=8, brush=brushes.FLAT_HOG, seed=1)
        c.stroke([(70, 120), (120, 70)], RED, amount=4, brush=brushes.ROUND_HOG, seed=2)
        c.stipple([(80, 80), (100, 95)], RED, seed=3)
        _knife_pull([(70.0, 90.0), (110.0, 90.0)], -90.0, load=2.0, blade=40)(c)
    finally:
        _knife._Stage = stage
    assert not made and c._past_edge == {}
    np.testing.assert_array_equal(c.edge_loss, 0.0)


def test_what_lies_past_the_edge_is_kept_in_tiles_where_there_is_any():
    """The canvas keeps what a stage holds past its edge, pixel by pixel:
    in tiles made where there is paint, none on the canvas; a later stage
    there holds it again, and bare canvas where nothing is kept; and a tile
    that is left with nothing is dropped."""
    T = _knife._KEPT_TILE
    c = Canvas(70, 50, seed=2)
    rng = np.random.default_rng(5)
    for name in PLANES:
        plane = getattr(c, name)
        plane[...] = rng.random(plane.shape) * 3
    box = (-40, 30, -70, 20)  # (over the top left corner)
    stage = _knife._Stage(c, *box)
    on = np.zeros((stage.height, stage.width), bool)
    on[stage._here] = True
    np.testing.assert_array_equal(stage.top[stage._here], c.top[stage._there])
    assert not stage.top[~on].any() and not stage.dry_height[~on].any()
    for got, plane in zip(stage._relief(), c._relief(), strict=True):
        there = np.pad(plane, 100, mode="wrap")[60:130, 30:120]
        np.testing.assert_array_equal(got, there)
    assert not c._past_edge
    stage.keep()  # (nothing past the edge: nothing kept)
    assert not c._past_edge
    stage.top[:20, :30] = np.float32(2.0)
    stage.top[35:, 60:] = np.float32(5.0)  # (5 px past the top edge; and on it)
    stage.keep()
    assert c._past_edge
    assert all(ty < 0 or tx < 0 for ty, tx in c._past_edge)
    assert all(tile[0].shape[:2] == (T, T) for tile in c._past_edge.values())
    again = _knife._Stage(c, -50, 40, -80, 40)
    want = np.zeros_like(again.top)
    want[10:30, 10:40] = 2.0
    want[45:50, 70:100] = 5.0
    want[50:80, 70:80] = 5.0
    want[again._here] = c.top[again._there]
    np.testing.assert_array_equal(again.top, want)
    again.top[...] = 0
    again.keep()
    assert not c._past_edge


def test_the_canvas_takes_what_it_keeps_along_and_old_pickles_load():
    """What a canvas keeps past its edge goes with it: a copy and a pickle
    hold it, each its own, and paint on exactly as the canvas does. A
    canvas pickled before any was kept loads keeping nothing."""
    c, _ = _pair("brushed")
    _knife_pull(OFF, pressure=0.9)(c)
    assert _kept(c)[IV] > 1000.0
    pickled = pickle.dumps(c)
    copies = (c.copy(), pickle.loads(pickled))
    for other in copies:
        assert other._past_edge.keys() == c._past_edge.keys()
        for key, tile in c._past_edge.items():
            for mine, theirs in zip(tile, other._past_edge[key], strict=True):
                assert theirs is not mine
                np.testing.assert_array_equal(theirs, mine)
    _knife_pull(ONTO, seed=4)(c)
    for other in copies:
        _knife_pull(ONTO, seed=4)(other)
        for name in PLANES:
            np.testing.assert_array_equal(getattr(other, name), getattr(c, name))
        np.testing.assert_array_equal(other.edge_loss, c.edge_loss)
    state = pickle.loads(pickled).__getstate__()
    for name in ("_past_edge", "edge_loss"):
        del state[name]
    old = Canvas.__new__(Canvas)
    old.__setstate__(state)
    assert old._past_edge == {} and not old.edge_loss.any()
    _knife_pull(ONTO, seed=4)(old)  # (and it can be painted on)


def test_a_long_stroke_takes_the_memory_of_a_stage_and_keeps_a_bounded_band():
    """A knife pulled 890 px across a canvas 800 by 500 px, from well inside
    it to 60 px past its right edge, peaks at 22 MB: a stage for the steps
    that reach past the edge (0.25 KB a pixel, no more than about
    _knife._STAGE_AREA px at a time), what the canvas then keeps past its
    edge (4 MB) and the piece its paint settles on. And a knife pulled from
    2,000 px out through a corner of a canvas 200 px square and out again
    as far, twice: the canvas keeps what lies within 128 px of it, 2.6 MB
    after the first pull and 4.0 MB after the second, which spreads the
    paint the first left over more tiles (4.1 MB after a fourth), where
    all the two pulls passed over is 20 times that."""

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
    c = Canvas(200, 200, seed=1)
    sizes = []
    for seed in (1, 2):
        knife = Brush(brushes.PALETTE_KNIFE).load(P.CADMIUM_RED, 6)
        c.stroke([(-2000, -2000), (2200, 2200)], brush=knife, pressure=0.5, seed=seed)
        assert not any(_knife._kept_far(key, 200, 200) for key in c._past_edge)
        sizes.append(
            sum(a.size * a.itemsize for tile in c._past_edge.values() for a in tile)
        )
    assert 0 < sizes[0] < 3.0e6 and sizes[0] < sizes[1] < 4.5e6


def test_thick_paint_beside_what_settles_does_not_make_it_level():
    """Whether paint levels is asked of the paint in the boxes that settle,
    not of the whole tiles those boxes touch: thick paint kept past the edge
    in the same tile, but outside the box, is not what settles there."""
    canvas = Canvas(64, 64, seed=1)
    tile = canvas._past_edge[-1, 0] = _knife._bare_tile(canvas)
    tile[0][:, 0, IV] = 2.0  # thick, in column 0 of the tile only
    tile[0][:, 5:15, IV] = 0.1  # thin beside it
    edge = _knife._Edge.__new__(_knife._Edge)
    edge.canvas = canvas
    nowhere = (0, 0, 0, 0)
    assert not edge._thick(nowhere, [(-16, 0, 5, 15)])
    assert edge._thick(nowhere, [(-16, 0, 0, 15)])

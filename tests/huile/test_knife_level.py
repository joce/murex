"""How far a knife drags wet paint must not hang on how its stroke is cut
into steps (murex-kau).

A blade carries a wave of wet paint under it, as long as the blade is wide,
and rides on it. How high it rides was read once per step, from the paint
under where the step takes it, a step further on, where part of that wave is
missing: the longer the step next to the blade's width, the lower the blade,
and the more it dragged. And it laid its own paint in the mean of the gaps it
met over the step, which is less than it lays, step after step, in a gap
that opens as it passes.

- the flow under a blade riding on wet paint (_engine.flow_under_riding_blade)
  works its level out again as it goes, at every sub-step, from the paint
  under where it is then, and takes sub-steps of one length whatever the
  step, laid along the stroke (_engine.flow_sub_steps);
- the blade fills the gap under it sub-step by sub-step, the paint it has
  laid there in the step lying on the surface (_engine._lay_as_met).
"""

from typing import Any

import numpy as np

import murex.huile.stroke as stm
from murex.huile import Brush, Canvas, Paint, _knife, brushes
from murex.huile import _engine as eng
from murex.huile import palette as P
from murex.huile._engine import IB, IS, IV, PACKED

DARK = Paint("#1c1a24")

# --- the flow alone: a blade pushed along a flat bed -----------------------------
H, W = 24, 160
SID = 7  # the stroke's id
BED = 2.4  # how thick the earlier strokes' paint lies
DEPTH = 0.27  # how far into it the blade sinks (pressure 0.5)
RIDE = 0.085  # how high it rides on its own film
FILM = 0.17  # how thick that film is
# How thick the wet paint lay before the stroke, as the flow is told it (it
# reads it only under the stroke's own film, of which these beds have none:
# see tests/huile/test_knife_heaps.py).
_BEFORE = np.full((H, W), BED, np.float32)


def _packed(paint, volume):
    out = np.zeros(PACKED, np.float32)
    out[:IS] = paint.K * volume
    out[IS] = paint.S * volume
    out[IV] = volume
    out[IB] = paint.body * volume
    return out


def _bed(bump=None):
    """A flat bed of dark, BED thick (``bump``: (columns, height) of more of
    it there)."""
    top = np.zeros((H, W, PACKED), np.float32)
    top[:] = _packed(DARK, BED)
    if bump is not None:
        top[:, bump[0]] = _packed(DARK, BED + bump[1])
    und = np.zeros((H, W, PACKED), np.float32)
    one = np.ones((H, W), np.float32)
    ids = np.zeros((H, W), np.int32)
    return eng.Layers(top=top, und=und, top_a=one, und_a=one.copy(), top_id=ids)


def _old_paint(cv):
    """How thick the paint lies along the middle row."""
    return (cv.und[..., IV] + cv.top[..., IV]).astype(np.float64)[H // 2]


def _rest_under(cv, end, half):
    """Where a blade ``half`` px either way along its way rests with its
    middle at ``end``, as _knife._blade_rest reads it for a step: on the
    high points (the highest within a pixel) of the paint it mostly covers,
    sunk DEPTH of the way down to the canvas."""
    x = np.arange(W) + 0.5
    under = np.clip(half - np.abs(x - end) + 0.5, 0.0, 1.0) > 0.5
    v = _old_paint(cv)
    high = np.maximum(np.maximum(np.roll(v, 1), v), np.roll(v, -1))
    return (1.0 - DEPTH) * high[under].mean()


def _riding(sunk, span=3):
    """What a blade over every row rides on (its positions along it: the
    rows), resting at ``sunk`` on the paint and at 0 on the canvas."""
    return eng.Riding(
        rest=np.zeros((H, W), np.float32),
        sunk=sunk * np.ones((H, W)),
        bins=np.tile(np.arange(H)[:, None], (1, W)).astype(np.int64),
        depth=DEPTH,
        span=span,
    )


def _step(cv, end, ds, half, riding=None, phase=0.0, fill=None):
    """One step of ``ds`` px along +x of a blade over every row, ending
    with its middle at ``end``, its level read under where the step takes
    it: ``riding`` on the paint (the ``riding_flow`` fixture, which see for
    ``phase`` and ``fill``), or, None, at that level throughout. Returns
    what the flow returns."""
    sunk = _rest_under(cv, end, half)
    full = np.ones((H, W))
    along = np.tile(np.arange(W) + 0.5 - end, (H, 1))
    level = (sunk + RIDE) * full
    args = (
        cv, 0, 0, SID, np.zeros((H, W), np.float32), level, full, along,
        0.0 * full, half * full, ds, 1.0, 0.0, 0.6 * full, 3, FILM * full,
        level, FILM * full, _BEFORE,
    )  # fmt: skip
    if riding is not None:
        return riding(args, _riding(sunk), phase, fill)
    return eng.flow_under_blade(*args), level


def _pushed(ds, half, riding=None, travel=64.0):
    """A blade pushed ``travel`` px along a flat bed in steps of ``ds``.
    Returns how far it carried the paint (volume times distance, a row) and
    the heap it left ahead of where it stopped."""
    cv = _bed()
    end, phase = 40.0, 0.0
    for _ in range(round(travel / ds)):
        end += ds
        phase = _step(cv, end, ds, half, riding, phase)[-1]
    moved = _old_paint(cv) - BED
    x = np.arange(W) + 0.5
    return float((moved * x).sum()), float(moved[x > end].sum())


def test_a_blade_riding_on_its_wave_carries_as_far_in_long_steps_as_in_short(
    riding_flow,
):
    """A blade 12 px wide pushed 64 px along 2.4 units of wet paint, its
    level read for each step under where the step takes it: in steps of 8
    px it carries the paint as far as in steps of 4, 2 and 1 px and of half
    a pixel, and leaves the same heap, and a blade 22 px wide too. With
    the level held at what was read (as it was: flow_under_blade), where
    the step takes it the wave it pushes is not there yet: the narrow blade
    rode too low all along a long step and carried a third further, its
    heap 88% bigger."""
    for half in (6.0, 11.0):
        long = _pushed(8.0, half, riding_flow)
        for ds in (4.0, 2.0, 1.0, 0.5):
            short = _pushed(ds, half, riding_flow)
            assert abs(long[0] / short[0] - 1.0) < 0.02, (half, ds)
            assert abs(long[1] / short[1] - 1.0) < 0.03, (half, ds)
    # (what the level held over the step made of it)
    held_long, held_short = _pushed(8.0, 6.0), _pushed(1.0, 6.0)
    assert held_long[0] / held_short[0] > 1.2
    assert held_long[1] / held_short[1] > 1.5


def test_a_riding_blade_rests_on_the_paint_under_where_it_is(riding_flow):
    """At a sub-step the blade rests as _knife._blade_rest has it for a
    step, on the paint under where it is then: on the high points of the
    paint, each pixel counting by how much of it the blade is over, sunk
    ``depth`` of the way to the canvas. Over a bed with 1.5 units more
    paint on 8 columns under the blade, a step that ends over them finds
    the blade that much higher than the level read where there was none;
    over the rows it does not reach, the level stays the step's."""
    half, end, ds = 11.0, 80.0, 0.5  # (too short for a sub-step: where it ends)
    bump = (slice(76, 84), 1.5)
    cv = _bed(bump)
    before = _old_paint(cv)
    full = np.ones((H, W))
    along = np.tile(np.arange(W) + 0.5 - end, (H, 1))
    aa = np.zeros((H, W))
    aa[:16] = 1.0  # (the blade is over the first 16 rows only)
    sunk, level = 1.9, 2.0  # (as read where the bed is flat, and some film)
    args = (
        cv, 0, 0, SID, np.zeros((H, W), np.float32), level * full, aa, along,
        0.0 * full, half * full, ds, 1.0, 0.0, 0.6 * full, 3, FILM * full,
        (level - 0.05) * full, FILM * full, _BEFORE,
    )  # fmt: skip
    laid, got, _sides, reached, _phase = riding_flow(args, _riding(sunk, span=2))
    assert reached
    over = np.clip(half - np.abs(np.arange(W) + 0.5 - end) + 0.5, 0.0, 1.0)
    high = np.maximum(np.maximum(np.roll(before, 1), before), np.roll(before, -1))
    want = level + ((1.0 - DEPTH) * (over * high).sum() / over.sum() - sunk)
    assert want - level > 0.2  # (the paint under it holds it higher)
    # (rows 0..15 under the blade, and those within 2 of them along it)
    np.testing.assert_allclose(got[:18], want, rtol=0, atol=1e-9)
    np.testing.assert_array_equal(got[18:], level)
    # (what it laid is told where it was over the pixel, and nowhere else:
    # nothing here, a blade with no paint to lay)
    assert (laid[:16, over > 0] == 0.0).all()
    assert (laid[16:] < 0).all() and (laid[:, over == 0] < 0).all()


def test_the_flow_under_a_riding_blade_keeps_every_channel(riding_flow):
    """Nothing is made or lost, band by band, and nothing is left below
    zero."""
    cv = _bed((slice(60, 70), 1.0))
    before = (cv.top.astype(np.float64) + cv.und).sum(axis=(0, 1))
    end, phase = 50.0, 0.0
    for _ in range(5):
        end += 8.0
        out: Any = _step(cv, end, 8.0, 11.0, riding_flow, phase)
        laid, _level, _sides, reached, phase = out
        assert laid.shape == (H, W) and reached
    after = (cv.top.astype(np.float64) + cv.und).sum(axis=(0, 1))
    assert np.abs(_old_paint(cv) - BED).max() > 0.5  # (it did drag it)
    np.testing.assert_allclose(after, before, rtol=2e-6)
    assert cv.top.min() >= 0.0 and cv.und.min() >= 0.0


def test_a_riding_blade_far_above_the_paint_drags_nothing(riding_flow):
    """A blade the paint does not reach moves none, works nothing out of
    what it lays, and keeps the step's level."""
    cv = _bed()
    full = np.ones((H, W))
    along = np.tile(np.arange(W) + 0.5 - 80.0, (H, 1))
    level, hang = (BED + 2.0) * full, (BED + 1.5) * full
    top = cv.top.copy()
    args = (
        cv, 0, 0, SID, np.zeros((H, W), np.float32), level, full, along,
        0.0 * full, 11.0 * full, 8.0, 1.0, 0.0, 0.6 * full, 3, FILM * full, hang,
        FILM * full, _BEFORE,
    )  # fmt: skip
    laid, got, sides, reached, _phase = riding_flow(args, _riding(BED), 0.0, full)
    assert laid.shape == (0, 0) and not reached
    assert got.tobytes() == level.tobytes()
    assert not sides[0].any() and not sides[1].any()
    assert cv.top.tobytes() == top.tobytes()


# --- what the blade lays as it goes -------------------------------------------------


def _laying(cv, level, steps, riding, fill=0.3, end=60.0, slip=0.6):
    """A blade 22 px along its way, over every row, held ``level`` above
    the canvas where the bed lies flat (it rides on the paint: see
    :func:`_riding`), pushed along +x in ``steps`` (px each) to end with
    its middle at ``end``, filling the share ``fill`` of the gap under it
    over a pixel while it goes 8 px over it (and over a shorter way, its
    share of that: 1 - (1 - fill)^(way / 8)). After each step what it laid
    is laid on the canvas, as _engine.deposit lays a knife's paint: on
    top, the paint there before going under. Returns what it laid in all,
    pixel by pixel."""
    full = np.ones((H, W))
    sunk = (1.0 - DEPTH) * float(np.float32(BED))  # (as the bed lies)
    at, phase = end - sum(steps), 0.0
    total = np.zeros((H, W))
    for ds in steps:
        at += ds
        along = np.tile(np.arange(W) + 0.5 - at, (H, 1))
        # (how far the blade goes over each pixel in this step)
        way = np.clip(
            np.minimum(0.0, along + 11.0) - np.maximum(-ds, along - 11.0), 0, ds
        )
        share = 1.0 - (1.0 - fill) ** (way / 8.0)
        args = (
            cv, 0, 0, SID, np.zeros((H, W), np.float32), level * full, full, along,
            0.0 * full, 11.0 * full, ds, 1.0, 0.0, slip * full, 3, FILM * full,
            level * full, FILM * full, _BEFORE,
        )  # fmt: skip
        laid, _level, _sides, _reached, phase = riding(
            args, _riding(sunk), phase, share
        )
        laid = np.maximum(laid, 0.0)
        new = (laid > 0) & (cv.top_id != SID)
        cv.und[new] += cv.top[new]
        cv.top[new] = 0.0
        cv.top_id[new] = SID
        cv.top[..., IV] += laid.astype(np.float32)
        total += laid
    return total


def test_a_blade_fills_a_gap_that_does_not_change_as_it_always_did(riding_flow):
    """Over a gap that stays the same through the step (a blade that does
    not grip the paint under it, 0.1 units above it) the blade lays the
    step's share of it on every pixel it is over for the whole step,
    whatever sub-steps the step falls on: a step of 8 px, and one of half a
    pixel or less, with a sub-step in it or none."""
    fill = 0.3
    gap = (BED + 0.1) - float(np.float32(BED))  # (the bed is single precision)
    for ds in (8.0, 0.5, 0.2):
        cv = _bed()
        laid = _laying(cv, BED + 0.1, [ds], riding_flow, fill, slip=0.0)
        whole = slice(60 - 10, 60 + 10 - int(np.ceil(ds)))
        want = gap * (1.0 - (1.0 - fill) ** (ds / 8.0))
        np.testing.assert_allclose(laid[H // 2, whole], want, rtol=1e-9)
        earlier = cv.und[..., IV] + np.where(cv.top_id == SID, 0.0, cv.top[..., IV])
        assert (earlier == np.float32(BED)).all()  # (nothing moved)


def test_a_blade_lays_as_much_in_one_step_as_in_many(riding_flow):
    """What a blade pushed 64 px over wet paint that it drags lays as it
    goes, 0.05 and 0.1 units above where the paint lay: in steps of 8 px
    what it lays in steps of 4 and 1 px and of half a pixel, within 4% in
    all (2.6% at most here). The gap under it opens as it passes, as it
    draws the paint away, and each sub-step fills its share of the gap it
    finds, the paint laid earlier in the step lying on the surface as it
    does once it is laid.

    (Filling the step's share of the mean gap, it laid 8% less at a
    stroke's own steps, murex-kau; taking what it had laid in the step off
    what the film could fill of the gap without it, 2 to 4% less: a gap
    out of the film's reach stayed out of it till the step was over.)"""
    for above in (0.05, 0.1):
        laid = {}
        for ds in (8.0, 4.0, 1.0, 0.5):
            cv = _bed()
            steps = [ds] * round(64.0 / ds)
            row = _laying(cv, BED + above, steps, riding_flow, end=104.0)[H // 2]
            laid[ds] = float(row.sum())
            assert laid[ds] > 0.3  # (it does lay)
            assert np.abs(_old_paint(cv) - BED).max() > 0.1  # (and drag)
        for ds in (4.0, 1.0, 0.5):
            assert abs(laid[8.0] / laid[ds] - 1.0) < 0.04, (above, ds, laid)


def test_a_film_reaches_further_down_on_the_paint_it_has_laid(riding_flow):
    """A film 0.17 thick reaches a surface 0.18 below the blade poorly (see
    _engine.film_gap) and one 0.1 below it altogether. Over a gap of 0.18
    that does not change, a step of 8 px lays what eight steps of 1 px and
    sixteen of half a pixel lay (to 2%): what it has laid in the step
    brings the surface within its reach, as it does from one step to the
    next. That is over twice the step's share of what the film could fill
    as the step began."""
    fill = 0.9
    gap = (BED + 0.18) - float(np.float32(BED))
    got = []
    for steps in ([8.0], [1.0] * 8, [0.5] * 16):
        cv = _bed()
        laid = _laying(cv, BED + 0.18, steps, riding_flow, fill, slip=0.0)
        got.append(float(laid[H // 2, 51:62].mean()))
    assert abs(got[0] / got[1] - 1.0) < 0.02 and abs(got[0] / got[2] - 1.0) < 0.02, got
    at_first = gap * float(eng.smoothstep(1.3, 0.7, gap / FILM)) * fill
    assert got[0] > 2.0 * at_first


# --- a knife pull over wet paint, at its own steps and in shorter ones -----------
START, END = (60.0, 60.0), (190.0, 154.0)
_PIGMENTS = np.stack(
    [np.concatenate([p.K, [p.S, 1.0]]) for p in (DARK, P.TITANIUM_WHITE)], axis=1
)
_SCALE = 1.0 / np.abs(_PIGMENTS).max(axis=1)
_GROUND: dict = {}


def _ground():
    """A wet dark ground, 2.3 to 2.9 units thick: two pulls of a wide knife
    side by side, in their own steps."""
    if "dark" not in _GROUND:
        c = Canvas(260, 220, seed=1)
        for x in (60, 180):
            knife = Brush(brushes.knife("straight", 160, flex=0.5)).load(DARK, 5.0)
            c.stroke(
                [(x, 10), (x, 210)],
                None,
                brush=knife,
                angle=0,
                follow_path=False,
                pressure=0.7,
                lift=0.0,
                seed=1,
            )
        _GROUND["dark"] = c
    return _GROUND["dark"].copy()


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
    """Every channel, on the canvas and on the blade."""
    on = canvas.top.sum(axis=(0, 1), dtype=np.float64)
    on += canvas.und.sum(axis=(0, 1), dtype=np.float64)
    return on + (brush.tip.astype(np.float64) + brush.reservoir + brush.heel).sum(0)


def _knifed(canvas, step, seed, pressure, load=0.3):
    """White knifed on ``canvas`` with a blade 60 px long (12 px wide), 160
    px from START to END, the blade across the pull, its stroke cut into
    steps of ``step`` px at most (a stroke's: 8). Returns the blade."""
    way = np.subtract(END, START)
    brush = Brush(brushes.knife("straight", 60, flex=0.5)).load(P.TITANIUM_WHITE, load)
    longest = stm._MAX_STEP
    stm._MAX_STEP = step
    try:
        canvas.stroke(
            [START, tuple(np.add(START, END) / 2), END],
            None,
            brush=brush,
            angle=float(np.degrees(np.arctan2(way[1], way[0]))) - 90.0,
            follow_path=False,
            pressure=pressure,
            lift=0.0,
            seed=seed,
        )
    finally:
        stm._MAX_STEP = longest
    return brush


def _pull(step, seed, pressure=0.5):
    """The pull of :func:`_knifed` across the wet dark. Returns (how far
    the dark was carried along the pull, volume times distance; the heap of
    dark left from where the blade's middle stopped on; the white laid; how
    far every channel is from kept, as a share of the largest)."""
    c = _ground()
    way = np.subtract(END, START)
    length = float(np.hypot(*way))
    way = way / length
    dark, _white = _volumes(c)
    brush = Brush(brushes.knife("straight", 60, flex=0.5)).load(P.TITANIUM_WHITE, 0.3)
    before = _totals(c, brush)
    brush = _knifed(c, step, seed, pressure)
    after = _totals(c, brush)
    dark_after, white = _volumes(c)
    yy, xx = np.mgrid[0 : c.height, 0 : c.width]
    along = (xx + 0.5 - START[0]) * way[0] + (yy + 0.5 - START[1]) * way[1]
    moved = dark_after - dark
    return (
        float((moved * along).sum()),
        float(moved[along > length - 10.0].sum()),
        float(white.sum()),
        float(np.abs(after - before).max() / np.abs(before).max()),
    )


def test_a_knife_drags_wet_paint_as_far_at_its_own_steps_as_in_shorter_ones(
    same_textures,
):
    """The pull above at pressure 0.5 and 0.7, with the same textures: at a
    stroke's own steps the blade carries the dark as far as in steps of 2
    px (0.998 and 1.001 times), leaves the same heap where it stops (1.003
    and 1.004 times) and lays the same white (1.005 and 1.002 times; eight
    strokes at pressures 0.25 to 0.7 stay within 0.011, 0.012 and 0.008 of
    1). It was 1.58 and 1.49 times as far, 2.14 and 2.10 times the heap,
    and 0.90 and 0.87 times the white: its level, read 8 px ahead of a
    blade 12 px wide, missed two thirds of the wave it rode on. Every
    channel is kept (to 3e-9)."""
    _ground()  # (laid with its own textures, before the pulls' are matched)
    same_textures()
    for pressure, seed in ((0.5, 100), (0.7, 101)):
        own, fine = _pull(8.0, seed, pressure), _pull(2.0, seed, pressure)
        carried, heap, white = (np.array(own) / np.array(fine))[:3]
        assert 0.97 < carried < 1.03, (pressure, carried)
        assert 0.95 < heap < 1.05, (pressure, heap)
        assert 0.98 < white < 1.02, (pressure, white)
        assert own[3] < 1e-7 and fine[3] < 1e-7


def test_a_blade_coming_onto_the_canvas_is_over_every_pixel_it_covers(
    monkeypatch, by_name
):
    """The flow under a riding blade looks for the blade, at each of its
    sub-steps, only where the step can take it (_engine._swept_rows): the
    pixels it tells what the blade laid on are those the blade is over at
    one of them, as looking all over the window finds them, for a blade
    coming onto the canvas over its top edge and over its left one, its own
    edge 2 and 5 degrees off the canvas's. (Looking within 2 px of where the blade
    was a sub-step before, it missed the pixels of the canvas's edge rows
    that the blade's edge came over further along: in the steps that
    brought these three strokes' blades onto the canvas, 268, 207 and 199
    pixels the blade was over were not found under it, for all of the step
    or part of it, and it neither dragged their paint nor laid any there
    then.)"""
    seen = []
    flow = eng.flow_under_riding_blade

    def spy(*args):
        out = flow(*args)
        if out[0].size:
            given = by_name(flow, args)
            names = ("aa", "along", "c", "chord_half", "ds", "tx", "ty")
            got = (*(np.copy(given[name]) for name in names), given["subs"], out[0])
            seen.append(got)
        return out

    monkeypatch.setattr(eng, "flow_under_riding_blade", spy)
    top, left = [(130.0, -40.0), (130.0, 120.0)], [(-40.0, 110.0), (120.0, 110.0)]
    for path, angle in ((top, 2.0), (top, 5.0), (left, -86.0)):
        seen.clear()
        knife = Brush(brushes.knife("straight", 110, flex=0.5))
        _ground().stroke(
            path,
            None,
            brush=knife.load(P.TITANIUM_WHITE, 0.3),
            angle=angle,
            follow_path=False,
            pressure=0.5,
            lift=0.0,
            seed=3,
        )
        assert len(seen) > 8
        for aa, along, c, half, ds, tx, ty, (n, first), laid in seen:
            per = eng.RIDE_CFL / (abs(tx) + abs(ty))
            # (where the blade stands at the sub-steps that fall in the
            # step; with none, where the step ends)
            places = [min(-ds + first + k * per, 0.0) for k in range(n)] or [0.0]
            over = np.zeros(aa.shape)
            for pos in places:
                over += aa * np.clip(half - np.abs(along - pos - c) + 0.5, 0.0, 1.0)
            ever = over > 0
            assert np.array_equal(laid >= 0, ever), (angle, int(ever.sum()))


def test_the_bead_hangs_from_the_blade_not_from_the_paint_it_has_laid(monkeypatch):
    """Skimming, the flow under the blade is told the level its bead hangs
    from raised by the stroke's own paint (so that the bead finds the
    surface under that paint: murex-86z, see _knife._drag_film). What the
    slab is then given is the blade's: where the blade ends a step higher
    or lower than the step had it, its bead hangs as far below it as in the
    step, whatever paint of its own lies there (laid a third of a unit
    thick here, which would have lifted the bead off the surface)."""
    seen = []
    drag = _knife._drag_film

    def spy(run, s, level, hang, film, riding=None, ridges=None):
        met = drag(run, s, level, hang, film, riding, ridges)
        if met is not None and met.laid is not None:
            seen.append(
                (
                    float(np.abs((met.hang - met.level) - (hang - level)).max()),
                    float(_knife._own_paint(run, s).max()),
                    float(np.abs(met.level - level).max()),
                    float((level - hang).max()),
                )
            )
        return met

    monkeypatch.setattr(_knife, "_drag_film", spy)
    _knifed(_ground(), 8.0, 3, 0.2, load=3.0)
    off, own, moved, below = (max(v) for v in zip(*seen, strict=True))
    assert len(seen) > 10
    assert own > 0.2  # (its own paint lies under the blade)
    assert moved > 0.02  # (the blade does end steps off the step's level)
    assert below > 0.01  # (and its bead hangs below it)
    assert off < 1e-12

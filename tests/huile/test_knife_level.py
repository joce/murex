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
  works its level out again as it goes, about every pixel of its way, from
  the paint under where it is then, and takes sub-steps of one length
  whatever the step;
- the blade fills the gap under it sub-step by sub-step (_engine.blade_slab,
  filled_as_met).
"""

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


def _step(cv, end, ds, half, riding=True):
    """One step of ``ds`` px along +x of a blade over every row, ending
    with its middle at ``end``, its level read under where the step takes
    it. Returns what the flow returns."""
    sunk = _rest_under(cv, end, half)
    full = np.ones((H, W))
    along = np.tile(np.arange(W) + 0.5 - end, (H, 1))
    level = (sunk + RIDE) * full
    args = (
        cv, 0, 0, SID, np.zeros((H, W), np.float32), level, full, along,
        0.0 * full, half * full, ds, 1.0, 0.0, 0.6 * full, 3, FILM * full,
        level, FILM * full,
    )  # fmt: skip
    if riding:
        return eng.flow_under_riding_blade(*args, _riding(sunk))
    return eng.flow_under_blade(*args), level


def _pushed(ds, half, riding=True, travel=64.0):
    """A blade pushed ``travel`` px along a flat bed in steps of ``ds``.
    Returns how far it carried the paint (volume times distance, a row) and
    the heap it left ahead of where it stopped."""
    cv = _bed()
    end = 40.0
    for _ in range(round(travel / ds)):
        end += ds
        _step(cv, end, ds, half, riding)
    moved = _old_paint(cv) - BED
    x = np.arange(W) + 0.5
    return float((moved * x).sum()), float(moved[x > end].sum())


def test_a_blade_riding_on_its_wave_carries_as_far_in_long_steps_as_in_short():
    """A blade 12 px wide pushed 64 px along 2.4 units of wet paint, its
    level read for each step under where the step takes it: in steps of 8
    px it carries the paint as far as in steps of 1 px (0.4% further, its
    heap 2.2% smaller; steps of 4 and 2 px give what steps of 8 do within
    0.2%), and a blade 22 px wide too. With the level held at what was read (as it was:
    flow_under_blade), where the step takes it the wave it pushes is not
    there yet: the narrow blade rode too low all along a long step and
    carried a third further, its heap 88% bigger."""
    for half in (6.0, 11.0):
        long, short = _pushed(8.0, half), _pushed(1.0, half)
        assert abs(long[0] / short[0] - 1.0) < 0.04, half
        assert abs(long[1] / short[1] - 1.0) < 0.06, half
        for ds in (4.0, 2.0):
            np.testing.assert_allclose(_pushed(ds, half), long, rtol=0.02)
    # (what the level held over the step made of it)
    held_long, held_short = _pushed(8.0, 6.0, False), _pushed(1.0, 6.0, False)
    assert held_long[0] / held_short[0] > 1.2
    assert held_long[1] / held_short[1] > 1.5


def test_a_riding_blade_rests_on_the_paint_under_where_it_is():
    """At a sub-step the blade rests as _knife._blade_rest has it for a
    step, on the paint under where it is then: on the high points of the
    paint, each pixel counting by how much of it the blade is over, sunk
    ``depth`` of the way to the canvas. Over a bed with 1.5 units more
    paint on 8 columns under the blade, a sub-step that ends over them
    finds the blade that much higher than the level read where there was
    none; over the rows it does not reach, the level stays the step's."""
    half, end, ds = 11.0, 80.0, 0.5  # (one sub-step)
    bump = (slice(76, 84), 1.5)
    cv = _bed(bump)
    before = _old_paint(cv)
    full = np.ones((H, W))
    along = np.tile(np.arange(W) + 0.5 - end, (H, 1))
    aa = np.zeros((H, W))
    aa[:16] = 1.0  # (the blade is over the first 16 rows only)
    sunk, level = 1.9, 2.0  # (as read where the bed is flat, and some film)
    met, got = eng.flow_under_riding_blade(
        cv, 0, 0, SID, np.zeros((H, W), np.float32), level * full, aa, along,
        0.0 * full, half * full, ds, 1.0, 0.0, 0.6 * full, 3, FILM * full,
        (level - 0.05) * full, FILM * full, _riding(sunk, span=2),
    )  # fmt: skip
    over = np.clip(half - np.abs(np.arange(W) + 0.5 - end) + 0.5, 0.0, 1.0)
    high = np.maximum(np.maximum(np.roll(before, 1), before), np.roll(before, -1))
    want = level + ((1.0 - DEPTH) * (over * high).sum() / over.sum() - sunk)
    assert want - level > 0.2  # (the paint under it holds it higher)
    # (rows 0..15 under the blade, and those within 2 of them along it)
    np.testing.assert_allclose(got[:18], want, rtol=0, atol=1e-9)
    np.testing.assert_array_equal(got[18:], level)
    # (The level its bead hangs from moves with it: the bead, hanging 0.05
    # below the blade and so still in the paint, finds the surface at the
    # level it hangs from where the step ends.)
    assert (met[:16, over > 0, 0] == 1.0).all() and (met[16:, :, 0] == 0.0).all()
    np.testing.assert_allclose(met[:16, 74:86, 1], want - 0.05, rtol=0, atol=1e-9)


def test_the_flow_under_a_riding_blade_keeps_every_channel():
    """Nothing is made or lost, band by band, and nothing is left below
    zero."""
    cv = _bed((slice(60, 70), 1.0))
    before = (cv.top.astype(np.float64) + cv.und).sum(axis=(0, 1))
    end = 50.0
    for _ in range(5):
        end += 8.0
        met, _level = _step(cv, end, 8.0, 11.0)
        assert met.shape[:2] == (H, W) and met.shape[2] > 2
    after = (cv.top.astype(np.float64) + cv.und).sum(axis=(0, 1))
    assert np.abs(_old_paint(cv) - BED).max() > 0.5  # (it did drag it)
    np.testing.assert_allclose(after, before, rtol=2e-6)
    assert cv.top.min() >= 0.0 and cv.und.min() >= 0.0


def test_a_riding_blade_far_above_the_paint_drags_nothing():
    """A blade the paint does not reach moves none, tells nothing of what
    it met, and keeps the step's level."""
    cv = _bed()
    full = np.ones((H, W))
    along = np.tile(np.arange(W) + 0.5 - 80.0, (H, 1))
    level, hang = (BED + 2.0) * full, (BED + 1.5) * full
    top = cv.top.copy()
    met, got = eng.flow_under_riding_blade(
        cv, 0, 0, SID, np.zeros((H, W), np.float32), level, full, along,
        0.0 * full, 11.0 * full, 8.0, 1.0, 0.0, 0.6 * full, 3, FILM * full, hang,
        FILM * full, _riding(BED),
    )  # fmt: skip
    assert met.shape == (0, 0, 2) and got.tobytes() == level.tobytes()
    assert cv.top.tobytes() == top.tobytes()


# --- the slab, filled as the gap was met ---------------------------------------


def _slab(met, fill, level=1.0):
    """What a blade at ``level`` over an empty flat canvas lays on one pixel
    where it met ``met`` (see _engine.flow_under_riding_blade), filling
    ``fill`` of the gap over the step."""
    top = np.zeros((1, 1, PACKED), np.float32)
    d, surf = eng.blade_slab(
        top, top.copy(), np.zeros((1, 1), np.float32), 0, 0,
        np.full((1, 1), level), np.zeros((0, 0)), np.full((1, 1), 10.0),
        np.full((1, 1), fill), np.asarray(met, np.float64).reshape(1, 1, -1),
    )  # fmt: skip
    return float(d[0, 0]), float(surf[0, 0])


def test_a_blade_fills_a_gap_that_does_not_change_as_it_always_did():
    """Over a gap that stays the same through the step the blade lays the
    step's share of it, however many sub-steps it was met at and however
    much of the pixel the blade was over at each."""
    g, fill = 0.4, 0.7
    for weights in ((1.0, 1.0, 1.0, 1.0), (0.0, 0.3, 1.0, 1.0, 1.0, 0.6), (0.25,)):
        pairs = []
        for i in range(0, len(weights), 2):
            w = sum(weights[i : i + 2])
            pairs += [g * w, w]
        d, surf = _slab([1, 0.6, *pairs], fill)
        np.testing.assert_allclose(d, g * fill, rtol=1e-12)
        assert surf == 0.6  # (the surface as the bead found it)
    # (never under the blade: the gap the canvas shows, here up to the level)
    assert _slab([0.0, 0.6, 0.0, 0.0], fill, level=0.5) == (0.5 * fill, 0.0)


def test_a_blade_fills_a_gap_that_opens_as_it_passes_sub_step_by_sub_step():
    """Each pair of sub-steps fills its share of what is left of the gap it
    finds. A gap that opens half way through the step (behind the paint the
    blade pushes) is filled by the share of half a step, 1 - (1 - fill)^½ of
    it, where the step's share of the mean gap is fill / 2: half as much
    again at fill 0.75. A gap that closes half way keeps what was laid in
    it; one that grows is topped up."""
    g, fill = 0.4, 0.75
    half = 1.0 - (1.0 - fill) ** 0.5
    opens, _ = _slab([1, 0.0, 0.0, 2.0, g * 2.0, 2.0], fill)
    np.testing.assert_allclose(opens, g * half, rtol=1e-12)
    assert opens > 1.3 * (0.5 * g * fill)
    closes, _ = _slab([1, 0.0, g * 2.0, 2.0, 0.0, 2.0], fill)
    np.testing.assert_allclose(closes, g * half, rtol=1e-12)
    grows, _ = _slab([1, 0.0, 0.5 * g * 2.0, 2.0, g * 2.0, 2.0], fill)
    first = 0.5 * g * half
    np.testing.assert_allclose(grows, first + (g - first) * half, rtol=1e-12)
    # (the blade over the pixel for a fifth of its way only, at the end, and
    # not at all over the middle pair of sub-steps)
    late, _ = _slab([1, 0.0, 0.0, 2.0, 0.0, 0.0, g * 0.5, 0.5], fill)
    np.testing.assert_allclose(late, g * (1.0 - (1.0 - fill) ** 0.2), rtol=1e-12)
    # (and over hardly any of it at one sub-step: that changes nothing)
    np.testing.assert_allclose(
        _slab([1, 0.0, 1e-15 * g, 1e-15, g * 2.0, 2.0], fill)[0], g * fill, rtol=1e-12
    )


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
    sub-steps, only where the step can take it (_engine._swept_rows): what
    it notes of how much of each pixel the blade was over is what looking
    all over the window gives, to the last bit, for a blade coming onto
    the canvas over its top edge and over its left one, its own edge 2 and
    5 degrees off the canvas's. (Looking within 2 px of where the blade
    was a sub-step before, it missed the pixels of the canvas's edge rows
    that the blade's edge came over further along: in the steps that
    brought these three strokes' blades onto the canvas, 268, 207 and 199
    pixels the blade was over were not found under it, for all of the step
    or part of it, and it neither dragged their paint nor laid any there
    then.)"""
    seen = []
    flow = eng.flow_under_riding_blade

    def spy(*args):
        met, level = flow(*args)
        if met.size:
            given = by_name(flow, args)
            names = ("aa", "along", "c", "chord_half", "ds", "tx", "ty")
            seen.append((*(np.copy(given[name]) for name in names), met))
        return met, level

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
        for aa, along, c, half, ds, tx, ty, met in seen:
            n = max(eng.whole_ceil(ds * (abs(tx) + abs(ty)) / eng.RIDE_CFL), 1)
            over = np.zeros((*aa.shape, (n + 1) // 2))
            for k in range(1, n + 1):
                pos = -ds + k * (ds / n)
                reach = np.clip(half - np.abs(along - pos - c) + 0.5, 0.0, 1.0)
                over[..., (k - 1) // 2] += aa * reach
            ever = over.sum(axis=2) > 0
            assert np.array_equal(met[..., 0] == 1.0, ever), (angle, int(ever.sum()))
            np.testing.assert_array_equal(met[ever][:, 3::2], over[ever])


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

    def spy(run, s, level, hang, film, riding=None):
        met = drag(run, s, level, hang, film, riding)
        if met is not None and riding is not None:
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

"""A knife must not drop what it bulldozes where its own paint begins
(murex-6fa).

A blade pushes along the wet paint that stands above it, and glides on its
own fresh paint: under more than a film of that (0.3 units) it dragged
nothing at all. So a heap it was pushing stopped dead as soon as it came
under such a film, and the blade went on without it: a loaded pull along the
end ridge of an earlier one gathered the ridge into a heap and left it
where the ridge sank under the blade and the blade began to lay paint ahead
of the heap, or where the paint it squeezed out at its start had landed, as
a lump two to three times as thick as the paint around it.

Under its own film the blade still drags nothing, but it pushes on what is
in its way there (_engine.pushed_under_film): the paint it has brought
there and the paint that stands above it, as far as the surface stands
above it.
"""

import importlib.util
import os
import sys

import numpy as np
import pytest

import murex.huile.stroke as stm
from murex.huile import Brush, Canvas, Paint
from murex.huile import _engine as eng
from murex.huile import palette as P
from murex.huile._engine import IB, IS, IV, PACKED


def _load_probe():
    """tools/huile/knife_probe.py, whose dark ground showed the lumps, as a
    module (the entries it puts on ``sys.path`` are taken off again)."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "tools", "huile", "knife_probe.py"
    )
    spec = importlib.util.spec_from_file_location("huile_tools_knife_probe_6fa", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    saved_path = list(sys.path)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = saved_path
    return module


probe = _load_probe()

# --- what is in the blade's way under its own film -------------------------------


def test_under_its_own_film_a_blade_pushes_what_is_in_its_way():
    """The paint of earlier strokes under the stroke's own film, with the
    blade 3 units above the canvas: what it pushes on."""
    pushed = eng.pushed_under_film.py_func
    # (2 units lay there, a film of 1 filled the gap: nothing is in the way)
    assert pushed(2.0, 1.0, 3.0, 2.0) == 0.0
    # (half a unit more has come in under the film, and lifts it past the
    # blade: that half unit goes on)
    assert pushed(2.5, 1.0, 3.0, 2.0) == pytest.approx(0.5)
    # (under a film that does not fill the gap, it first fills what is left)
    assert pushed(2.5, 0.4, 3.0, 2.0) == 0.0
    assert pushed(2.9, 0.4, 3.0, 2.0) == pytest.approx(0.3)
    # (the stroke's own paint standing above the blade, a bead at its end,
    # on paint that lies as it lay: none of the blade's business)
    assert pushed(2.0, 4.0, 3.0, 2.0) == 0.0
    # (paint that stood above the blade before the stroke is in its way,
    # whatever lies on it; what is under the blade stays)
    assert pushed(4.5, 0.0, 3.0, 4.5) == pytest.approx(1.5)
    assert pushed(4.5, 1.0, 3.0, 4.5) == pytest.approx(1.5)
    # (never more than there is, with the blade down on the canvas)
    assert pushed(2.5, 1.0, 0.0, 0.0) == 2.5
    # (and it grows from nothing: no threshold)
    rng = np.random.default_rng(5)
    for old, film, gap, before in rng.uniform(0.0, 5.0, (200, 4)):
        got = pushed(old, film, gap, before)
        assert 0.0 <= got <= old
        nudged = pushed(old + 1e-9, film, gap, before)
        assert abs(nudged - got) < 3e-9


# --- the flow alone: a heap pushed along a flat bed, under the blade's film ---------
H, W = 24, 200
SID = 7  # the stroke's id
BED = 2.4  # how thick the earlier strokes' paint lies
HALF = 11.0  # the blade's half-length along its way (px)
FILM_FROM = 90  # the column the stroke's own film lies from
DARK = Paint(probe.DARK)


def _packed(paint, volume):
    out = np.zeros(PACKED, np.float32)
    out[:IS] = paint.K * volume
    out[IS] = paint.S * volume
    out[IV] = volume
    out[IB] = paint.body * volume
    return out


def _bed(film, bump=1.5, film_from=FILM_FROM):
    """A flat bed of dark, BED thick, with ``bump`` more of it on columns
    60..67 (a ridge across the blade's way); from column ``film_from`` on,
    the stroke has laid its own white on it, ``film`` thick, and the dark
    is in the layer below, as deposit leaves it."""
    top = np.zeros((H, W, PACKED), np.float32)
    und = np.zeros((H, W, PACKED), np.float32)
    top[:] = _packed(DARK, BED)
    top[:, 60:68] = _packed(DARK, BED + bump)
    ids = np.zeros((H, W), np.int32)
    und[:, film_from:] = top[:, film_from:]
    top[:, film_from:] = _packed(P.TITANIUM_WHITE, film)
    ids[:, film_from:] = SID
    one = np.ones((H, W), np.float32)
    return eng.Layers(top=top, und=und, top_a=one, und_a=one.copy(), top_id=ids)


def _old_paint(cv):
    """How thick the earlier strokes' paint lies along the middle row."""
    own = cv.top_id == SID
    return (cv.und[..., IV] + np.where(own, 0.0, cv.top[..., IV]))[H // 2].astype(
        np.float64
    )


def _pushed(cv, level, ds, riding, travel=120.0):
    """A blade over every row, at ``level`` over the canvas, pushed
    ``travel`` px along +x in steps of ``ds`` from column 40 (riding on the
    paint, see _engine.flow_under_riding_blade, or at that level
    throughout). Returns where its middle stops."""
    full = np.ones((H, W))
    before = np.full((H, W), BED, np.float32)  # (as the bed lay)
    end = 40.0
    for _ in range(round(travel / ds)):
        end += ds
        along = np.tile(np.arange(W) + 0.5 - end, (H, 1))
        args = (
            cv, 0, 0, SID, np.zeros((H, W), np.float32), level * full, full, along,
            0.0 * full, HALF * full, ds, 1.0, 0.0, 0.6 * full, 3, 0.17 * full,
            level * full, 0.17 * full, before,
        )  # fmt: skip
        if riding:
            # (it rests 0.27 of the way into the paint: on the flat bed,
            # that leaves it at ``level``)
            ride = eng.Riding(
                rest=np.zeros((H, W), np.float32),
                sunk=(1.0 - 0.27) * BED * full,
                bins=np.tile(np.arange(H)[:, None], (1, W)).astype(np.int64),
                depth=0.27,
                span=3,
            )
            eng.flow_under_riding_blade(*args, ride)
        else:
            eng.flow_under_blade(*args)
    return end


@pytest.mark.parametrize("riding", [False, True])
def test_a_heap_pushed_under_the_blades_own_film_goes_on_with_the_blade(riding):
    """A blade pushing a ridge of 12 units of paint (a row) along 2.4 units
    of wet paint comes to where its own film lies on that paint, half a
    unit thick and up to the blade.

    Held at its level, the blade takes the heap on under the film: where it
    stops, 70 px on, 38 units of paint more than the bed's stand from its
    trailing edge on, and behind it nothing stands above the bed. A blade
    that rides on the paint under it rides higher on the heap, which fills
    the room that leaves under the film: it lays the heap out behind it, 15
    units over 60 px, 0.6 above the bed at most. The same in steps of 8, 2
    and 1 px (to 4%).

    (The heap stopped where the film began, and the blade went on without
    it: a lump 19 units high on 2.4, or 8 under the riding blade.) Every
    channel is kept, and the film stays as it is."""
    x = np.arange(W) + 0.5
    moved = []
    for ds in (8.0, 2.0, 1.0):
        cv = _bed(film=0.5)
        total = (cv.top.astype(np.float64) + cv.und).sum(axis=(0, 1))
        film = cv.top[:, FILM_FROM:].copy()
        end = _pushed(cv, BED + 0.5, ds, riding)
        old = _old_paint(cv)
        behind = x < end - HALF - 1.0
        assert old[behind].max() < BED + 2.0, (ds, old[behind].max())
        with_the_blade = float((old - BED)[x > end - HALF].sum())
        laid_out = float((old - BED)[behind & (x > FILM_FROM)].clip(0.0).sum())
        if riding:
            assert 10.0 < laid_out < 20.0 and with_the_blade < 4.0, (ds, laid_out)
        else:
            assert with_the_blade > 25.0 and laid_out < 1.0, (ds, with_the_blade)
        moved.append(laid_out if riding else with_the_blade)
        assert cv.top[:, FILM_FROM:].tobytes() == film.tobytes()
        after = (cv.top.astype(np.float64) + cv.und).sum(axis=(0, 1))
        np.testing.assert_allclose(after, total, rtol=2e-6)
        assert cv.top.min() >= 0.0 and cv.und.min() >= 0.0
    np.testing.assert_allclose(moved, moved[0], rtol=0.08)


@pytest.mark.parametrize("riding", [False, True])
def test_paint_lying_as_it_lay_under_the_strokes_own_paint_is_left_alone(riding):
    """The blade glides on its own fresh paint: where 3 units of it stand
    on the bed, 2.5 above the blade (as a bead does at the blade's ends),
    the paint under them, which lies as it lay before the stroke and under
    the blade, does not move at all. (Pushed on as far as the surface
    stands above the blade, whatever the surface is made of, it went: a
    knife loaded with 3 then carried the wet paint under its slab 12%
    further, where this carries it 1% further than before.)"""
    cv = _bed(film=3.0, bump=0.0, film_from=0)
    top, und = cv.top.copy(), cv.und.copy()
    _pushed(cv, BED + 0.5, 8.0, riding, travel=96.0)
    assert cv.top.tobytes() == top.tobytes() and cv.und.tobytes() == und.tobytes()


# --- loaded pulls, each along the end ridge of the one before -----------------------


def _ground(step=None):
    """The dark ground of ``knife_probe.py ribs``: four pulls of a knife
    160 px long, loaded with 5 of a stiff dark, at pressure 0.7, each over
    the ridge the one before left at its blade's end; its strokes cut into
    steps of ``step`` px at most (a stroke's: 8). Returns how thick the wet
    paint lies."""
    longest = stm._MAX_STEP
    stm._MAX_STEP = longest if step is None else step
    try:
        c = Canvas(420, 300, seed=1)
        probe.dark_base(c, 5.0, 0.7)
    finally:
        stm._MAX_STEP = longest
    return c.wet_thickness.astype(np.float64)


def test_a_pull_along_an_earlier_pulls_end_ridge_drops_no_lump():
    """On that ground no pixel stands more than 3.5 units above all that
    lies on a ring 8 px around it (see the probe's ``standing_alone``: the
    beads along the pulls' edges are ridges, not peaks): the tallest stands
    2.5 above it, what a pull leaves where it stops. There were lumps 6.4
    units above it, up to 10.7 units thick on paint 3.5 thick: 69 pixels
    stood more than 3 units above what lay around them, 40 were more than
    8 units thick."""
    alone = probe.standing_alone(_ground())
    assert alone.max() < 3.5, alone.max()


@pytest.mark.parametrize("step", [8.0, 4.0, 2.0, 1.0])
def test_a_pull_along_a_ridge_drops_no_lump_in_shorter_steps_either(
    step, same_textures
):
    """Nor in steps of 8, 4, 2 or 1 px with the same textures: the tallest
    stands 2.5, 2.2, 2.2 and 1.8 units above what lies around it (the
    lumps stood 6.6, 7.6, 7.6 and 6.9 above it, 59, 54, 49 and 45 pixels
    of them more than 3)."""
    same_textures()
    alone = probe.standing_alone(_ground(step))
    assert alone.max() < 3.5, (step, alone.max())


def test_pulls_along_a_ridge_keep_every_channel():
    """Two such pulls wholly on the canvas, the second along the end ridge
    of the first: nothing is made or lost, blade and canvas together, band
    by band (to 7e-10 of the largest; the test allows 1e-8)."""
    dark = Paint(probe.DARK, body=0.7)
    c = Canvas(340, 330, seed=1)
    for x in (110, 230):
        knife = Brush(probe.BASE_KNIFE).load(dark, 5.0)
        before = _totals(c, knife)
        c.stroke(
            [(x, 40), (x, 280)],
            None,
            brush=knife,
            angle=0,
            follow_path=False,
            pressure=0.7,
            lift=0.0,
        )
        after = _totals(c, knife)
        assert np.abs(after - before).max() < 1e-8 * np.abs(before).max()
    assert c.top.min() >= 0.0 and c.und.min() >= 0.0


def _totals(canvas, brush):
    """Every channel, on the canvas and on the blade."""
    on = canvas.top.sum(axis=(0, 1), dtype=np.float64)
    on += canvas.und.sum(axis=(0, 1), dtype=np.float64)
    return on + (brush.tip.astype(np.float64) + brush.reservoir + brush.heel).sum(0)

"""Repeatability: marks that sit on the lines rounding used to decide,
painted again with their inputs moved by an ulp (as another machine's
rounding would move them), keep the same stroke on top of every pixel and
differ in their paint by far less than a whole mark would."""

import copy

import numpy as np
import pytest

from murex.huile import Brush, Canvas, brushes
from murex.huile import palette as P


def _wet_canvas():
    c = Canvas(160, 120, seed=7)
    for y in (24, 64, 104):
        c.stroke(
            [(5, y), (80, y + 5), (155, y)],
            P.YELLOW_OCHRE,
            amount=14,
            brush=brushes.FLAT_HOG.sized(40),
            pressure=0.6,
        )
    return c


_BASE = None


def _base():
    global _BASE
    if _BASE is None:
        _BASE = _wet_canvas()
    return copy.deepcopy(_BASE)


# Marks that sit on the lines rounding used to decide: whole-number
# positions and a length a whole number of steps long, a brush turned by
# exactly 90 degrees, a knife over wet paint, a dab of two paints at the
# default pressure 0.5, a stroke whose axis runs through the middles of a
# row of pixels (at half a pixel, or at 45 degrees between whole-number
# points), a curve with a segment a whole even number of pixels long, a
# knife riding on wet paint in steps a whole number of the flow's sub-steps
# long (7 px along x, ten sub-steps of _engine.RIDE_CFL: the stroke comes
# to the end of each within 2e-13 of a whole number of sub-steps, see the
# test of it below).
MARKS = {
    "flat along a half-pixel axis": (
        [(20.0, 40.5), (140.0, 40.5)],
        lambda: (
            Brush(brushes.FLAT_HOG)
            .load(P.CADMIUM_RED, 4)
            .load(P.TITANIUM_WHITE, 2, across="left")
        ),
        {"pressure": 0.5},
    ),
    "flat at 45 degrees": (
        [(30.0, 20.0), (110.0, 100.0)],
        lambda: (
            Brush(brushes.FLAT_HOG)
            .load(P.CADMIUM_RED, 4)
            .load(P.TITANIUM_WHITE, 2, across="left")
        ),
        {"pressure": 0.5, "angle": 180.0},
    ),
    "knife back along a curve": (
        [(30.0, 60.0), (120.0, 60.0), (40.0, 62.0)],
        lambda: Brush(brushes.PALETTE_KNIFE).load(P.TITANIUM_WHITE, 3),
        {"pressure": 0.3},
    ),
    "comb dab at a half-pixel centre": (
        [(80.5, 60.5)],
        lambda: (
            Brush(brushes.KNIFE_COMB)
            .load(P.CADMIUM_RED, 4)
            .load(P.TITANIUM_WHITE, 2, across="left")
        ),
        {"pressure": 0.5, "angle": 180.0},
    ),
    "flat at 90 degrees": (
        [(30.0, 40.0), (110.0, 40.0)],
        lambda: Brush(brushes.FLAT_HOG.sized(32)).load(P.COBALT_BLUE, 4),
        {"pressure": 0.5, "angle": 90.0},
    ),
    "knife over wet paint": (
        [(40.0, 64.0), (120.0, 64.0)],
        lambda: Brush(brushes.PALETTE_KNIFE),
        {"pressure": 0.85, "width": 30.0},
    ),
    "knife in steps of ten sub-steps": (
        [(40.0, 64.0), (110.0, 64.0)],
        lambda: Brush(brushes.PALETTE_KNIFE),
        {"pressure": 0.85, "width": 28.0},
    ),
    "dab of two paints": (
        [(80.0, 60.0)],
        lambda: (
            Brush(brushes.FILBERT_HOG)
            .load(P.CADMIUM_RED, 4)
            .load(P.TITANIUM_WHITE, 2, across="left")
        ),
        {"pressure": 0.5},
    ),
}


def _nudge(v, k):
    for _ in range(abs(k)):
        v = float(np.nextafter(v, np.inf if k > 0 else -np.inf))
    return v


def _paint(name, rng=None):
    path, brush, kw = MARKS[name]
    kw = dict(kw)
    if rng is not None:
        path = [
            (_nudge(x, rng.integers(-1, 2)), _nudge(y, rng.integers(-1, 2)))
            for x, y in path
        ]
        kw = {k: _nudge(v, rng.integers(-1, 2)) for k, v in kw.items()}
    c = _base()
    c.stroke(
        path,
        brush=brush(),
        seed=5,
        pressure=kw["pressure"],
        angle=kw.get("angle"),
        width=kw.get("width"),
    )
    return c


def _scaled_difference(a, b):
    """The largest difference over the paint, each value's as a share of the
    larger of the two (and of 1e-3, for values near 0)."""
    worst = 0.0
    for name in ("top", "und", "top_a", "und_a"):
        x, y = getattr(a, name).astype(float), getattr(b, name).astype(float)
        d = np.abs(x - y) / np.maximum(np.maximum(np.abs(x), np.abs(y)), 1e-3)
        worst = max(worst, float(d.max()))
    return worst


@pytest.mark.parametrize("name", sorted(MARKS))
def test_a_mark_nudged_by_an_ulp_paints_the_same_to_rounding(name):
    # Measured over 12 nudges of each mark: at most 2e-7 (the flat along a
    # half-pixel axis), 1.1e-7 (the knife back along a curve), 6e-10 (the
    # knife over wet paint), 2.5e-7 (the knife in steps of ten sub-steps),
    # the others 0; no id changed. Before, the dab
    # came out 0.73 apart (its bristle tips printed half or fully), the flat
    # at 90 degrees 1 (its sides mirrored, 173 pixels with another stroke on
    # top), the knife over wet paint 1 (21), and, as the fixes went in, the
    # flat at 45 degrees 0.40, the flat along a half-pixel axis 0.41 (its
    # middle row's paint to one ridge or the other) and the knife along a
    # curve 1 (15: the curve traced one point more or fewer).
    plain = _paint(name)
    for seed in range(3):
        nudged = _paint(name, np.random.default_rng(seed))
        assert np.array_equal(plain.top_id, nudged.top_id), seed
        assert _scaled_difference(plain, nudged) < 1e-3, seed


def test_the_knife_in_steps_of_ten_sub_steps_sits_on_the_line(monkeypatch):
    """The sub-steps of the flow under a blade are laid along the stroke,
    one every _engine.RIDE_CFL px of the paint's way, and a step takes those
    that fall in it (_engine.flow_sub_steps). That mark's steps end a whole
    number of sub-steps along the stroke in exact arithmetic (its first and
    last, cut for the blade to be set down and lifted off, see
    stroke._SET_DOWN, a seventh of one more or less), and that or a hair
    off as computed (10.000000000000092, where the hair adds up along the
    stroke): the sub-step at the end of each is counted in it, to the same
    count however the inputs fall (whole_floor), and the stroke is then at
    the start of a sub-step, not a hair before its end."""
    from murex.huile import _engine as eng

    def steps(rng):
        seen = []
        sub_steps = eng.flow_sub_steps

        def spy(phase, ds, tx, ty):
            out = sub_steps(phase, ds, tx, ty)
            reach = phase + ds * (abs(tx) + abs(ty)) / eng.RIDE_CFL
            seen.append((reach, *out))
            return out

        monkeypatch.setattr(eng, "flow_sub_steps", spy)
        _paint("knife in steps of ten sub-steps", rng)
        monkeypatch.setattr(eng, "flow_sub_steps", sub_steps)
        return seen

    plain = steps(None)
    counts = [n for _reach, n, _first, _phase in plain]
    assert counts == [0, *([10] * (len(counts) - 3)), 9, 1] and len(counts) >= 10
    whole = [(reach, phase) for reach, n, _first, phase in plain if n in (10, 1)]
    assert all(abs(reach - round(reach)) < 2e-13 for reach, _ in whole), whole
    assert any(reach != round(reach) for reach, _ in whole)  # (a hair off, some)
    assert all(phase < 2e-13 for _, phase in whole)
    for seed in range(3):
        nudged = steps(np.random.default_rng(seed))
        assert [n for _reach, n, _first, _phase in nudged] == counts, seed


def test_a_step_takes_the_sub_steps_that_fall_in_it():
    """A stroke along x cut into steps of any lengths takes the same
    sub-steps of the flow, at the same places along it: one every
    RIDE_CFL px. A step that ends within rounding of a sub-step takes it,
    whether it ends a hair before it or after."""
    from murex.huile import _engine as eng

    def places(steps):
        at, phase, found = 0.0, 0.0, []
        for ds in steps:
            n, first, phase = eng.flow_sub_steps(phase, ds, 1.0, 0.0)
            found += [at + first + k * eng.RIDE_CFL for k in range(n)]
            at += ds
        return np.array(found), phase

    want = eng.RIDE_CFL * np.arange(1, 81)
    rng = np.random.default_rng(3)
    for steps in ([8.0] * 7, [1.0] * 56, [0.5] * 112, rng.uniform(0.1, 3.0, 400)):
        steps = np.asarray(steps)[np.cumsum(steps) <= 56.0]
        found, phase = places(steps)
        np.testing.assert_allclose(found, want[: len(found)], rtol=0, atol=1e-9)
        assert len(found) == int((steps.sum() + 1e-9) / eng.RIDE_CFL)
        assert 0.0 <= phase < 1.0
    # (a step that ends a hair before a sub-step, or after: it takes it)
    for hair in (-1e-13, 0.0, 1e-13):
        n, _first, phase = eng.flow_sub_steps(0.0, 3 * eng.RIDE_CFL + hair, 1.0, 0.0)
        assert n == 3 and phase < 1e-12


def test_the_engine_is_compiled_with_the_slack_the_shared_modules_use():
    # (written out in _engine.py: its kernels compile it in)
    from murex import _rounding
    from murex.huile import _engine as eng

    assert eng.WHOLE_SLACK == _rounding.WHOLE_SLACK
    for x in (7.5, 8.0, 8 - 6e-6, 8 + 6e-6, 600.0000000000001):
        assert eng.whole_floor(x) == _rounding.whole_floor(x)
        assert eng.whole_ceil(x) == _rounding.whole_ceil(x)

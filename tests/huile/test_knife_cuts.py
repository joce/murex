"""A knife's stroke does not show how it is cut into steps: the same pull
at a stroke's own steps (8 px at most) and with its steps capped at 4, 2, 1
and half a pixel leaves the same paint. Its textures are the same at every
cut, as every stroke's are (murex-9t4: these tests switched the wobble of
the width off, which drew another count of random numbers at each cut, and
their figures were those of the one stroke that left; with its wobble each
pull has another tilt, other bands and other nicks, and how near the cuts
come to each other depends on those: each test says what its own pull
gives, and the worst of six). What still hung on the cut after murex-kau
and murex-6fa, and why:

- a heavily loaded knife carried the wet paint further the longer its steps
  (murex-5gw): a step read the film on the blade once, as it began, and the
  blade laid a third of its load or more as it was set down, in the same
  step as the first of its way;
- a blade rippled the surface along a slanted pull the more the longer its
  steps (murex-h6u): the sub-steps of the flow under it were whole
  divisions of each step, longer in long steps;
- a loaded knife skimming over wet paint of its own colour laid more the
  longer its steps (murex-dq0): what it laid joined the layer it skimmed
  over, and it then rested on it;
- the heap a blade carries was left as a point where a pull stops
  (murex-dl9): the flow under a blade went along the stroke only.

Of the 19 tests here, 17 fail without the change that closed them.
"""

import functools
import math

import numpy as np
import pytest

import murex.huile.stroke as stm
from murex.filters import box_blur
from murex.huile import Brush, Canvas, Paint, brushes
from murex.huile import palette as P
from murex.huile._engine import IV

DARK = "#1c1a24"
FINE = 0.5  # the cap the others are compared with (px)
CAPS = (8.0, 4.0, 2.0, 1.0)
SIZE = (420, 300)
# a slanted pull across the ground, and one at 45 degrees
SLANT = ((90.0, 50.0), math.atan2(80.0, 110.0), 272.0)
DIAGONAL = ((110.0, 60.0), math.radians(45.0), 250.0)


@functools.cache
def _ground():
    """Wet dark paint some 2.8 units thick all over the canvas, knifed on
    with its own textures."""
    w, h = SIZE
    c = Canvas(w, h, seed=1)
    paint = Paint(DARK, body=0.7)
    for x in range(60, w + 120, 120):
        knife = Brush(brushes.knife("straight", 160, flex=0.5)).load(paint, 5.0)
        c.stroke(
            [(x, 10), (x, h - 10)],
            None,
            brush=knife,
            angle=0,
            follow_path=False,
            pressure=0.7,
            lift=0.0,
        )
    return c


@functools.cache
def _pigments():
    pig = np.stack(
        [np.concatenate([p.K, [p.S, 1.0]]) for p in (Paint(DARK), P.TITANIUM_WHITE)],
        axis=1,
    )
    return pig, 1.0 / np.abs(pig).max(axis=1)


def _dark_white(canvas):
    """The volume of dark and of white at each pixel, the two wet layers
    together."""
    pig, scale = _pigments()
    a = (canvas.top.astype(np.float64) + canvas.und)[..., : IV + 1] * scale
    sol, *_ = np.linalg.lstsq(pig * scale[:, None], a.reshape(-1, IV + 1).T, rcond=None)
    sol = sol.T.reshape(a.shape[:2] + (2,))
    return sol[..., 0], sol[..., 1]


def _totals(canvas, brush):
    """Every channel: on the canvas, on the blade and gone over the edge."""
    on = canvas.top.sum(axis=(0, 1), dtype=np.float64)
    on += canvas.und.sum(axis=(0, 1), dtype=np.float64)
    on += (brush.tip.astype(np.float64) + brush.reservoir + brush.heel).sum(0)
    return on + canvas.edge_loss


def _pull(cap, way, width, load, pressure, seed=100, bare=False, first=None):
    """A knife ``width`` px wide loaded with ``load`` of white pulled along
    ``way`` (start, heading, length) at ``pressure`` across the wet dark
    ground (``bare``: across the bare canvas; ``first``: (pressure, load) of
    a pull of white along the same way before it), in steps of ``cap`` px at
    most. Returns what it did: how far it carried the dark (volume times
    distance along the pull), the white it laid, the dark it left beside
    its mark, how thick the wet paint lies behind it and how much that
    ripples along the pull (about a 17 px running mean), and how far the
    paint on the canvas, on the blade and gone over the edge is from what
    there was (of the largest channel)."""
    (x0, y0), heading, length = way
    d = np.array([math.cos(heading), math.sin(heading)])
    pts = [(x0, y0), (x0 + length * d[0], y0 + length * d[1])]
    angle = math.degrees(heading) - 90.0
    c = Canvas(*SIZE, seed=1) if bare else _ground().copy()
    bt = brushes.knife("straight", width, flex=0.5)
    blade = {"angle": angle, "follow_path": False, "lift": 0.0}
    if first is not None:
        knife = Brush(bt).load(P.TITANIUM_WHITE, first[1])
        c.stroke(pts, None, brush=knife, pressure=first[0], seed=7, **blade)
    knife = Brush(bt).load(P.TITANIUM_WHITE, load) if load > 0 else Brush(bt)
    dark0, white0 = _dark_white(c)
    before = _totals(c, knife)
    longest = stm._MAX_STEP
    stm._MAX_STEP = cap
    try:
        c.stroke(pts, None, brush=knife, pressure=pressure, seed=seed, **blade)
    finally:
        stm._MAX_STEP = longest
    after = _totals(c, knife)
    dark, white = _dark_white(c)
    wet = c.wet_thickness.astype(np.float64)
    yy, xx = np.mgrid[0 : c.height, 0 : c.width]
    s = (xx + 0.5 - x0) * d[0] + (yy + 0.5 - y0) * d[1]
    lat = -(xx + 0.5 - x0) * d[1] + (yy + 0.5 - y0) * d[0]
    half = 0.5 * width
    moved = dark - dark0
    near = np.abs(lat) < half + 25.0
    behind = (s > 60.0) & (s < length - 42.0) & (lat > 1.0) & (lat < 29.0)
    profile = np.array(
        [
            wet[behind & (s >= a) & (s < a + 1.0)].mean()
            for a in np.arange(60.0, length - 43.0)
        ]
    )
    wave = (profile - np.convolve(profile, np.ones(17) / 17, "same"))[20:-20]
    return {
        "carried": float((moved * s)[near].sum()),
        "white": float((white - white0).sum()),
        "beside": float(
            moved[(np.abs(lat) > half) & (s > 0) & (s < length - 20.0)].sum()
        ),
        "thick": float(wet[behind].mean()),
        "ripple": float(wave.std()),
        "kept": float(np.abs(after - before).max() / np.abs(before).max()),
    }


def _against_fine(what, **pull):
    """``what`` of a pull (see _pull) at each of CAPS over what it is in
    steps of FINE; every pull keeps its paint."""
    fine = _pull(FINE, **pull)
    assert fine["kept"] < 1e-7
    out = {}
    for cap in CAPS:
        got = _pull(cap, **pull)
        assert got["kept"] < 1e-7, cap
        out[cap] = [got[k] / fine[k] for k in what]
    return out


def _within(got, what, most):
    """Each of ``what`` is within ``most`` of 1 at every cap of ``got``
    (see _against_fine)."""
    for cap, ratios in got.items():
        for name, ratio, tol in zip(what, ratios, most, strict=False):
            assert abs(ratio - 1.0) < tol, (cap, name, ratio)


# --- murex-5gw: a heavily loaded knife ------------------------------------------------


def test_a_heavily_loaded_knife_carries_wet_paint_as_far_at_every_cut():
    """A knife 60 px wide loaded with 3 and pulled at pressure 0.25 across
    the wet dark carries it as far in steps of 8, 4, 2 and 1 px as in steps
    of half a pixel (to 1.2%, the most of six pulls, and the test allows
    2%; it carried 11.4, 5.5, 2.2 and 0.8% further), lays the same white
    (to 0.1%; 0.5% allowed) and leaves the same dark beside its mark (to
    2.6%, the most of six too; 4% allowed; it left 18% more at a stroke's
    own steps). (0.3% and 1.5% with the wobble of its width off, when 1%
    and 3% were allowed.)"""
    what = ("carried", "white", "beside")
    got = _against_fine(what, way=SLANT, width=60, load=3.0, pressure=0.25)
    _within(got, what, (0.02, 0.005, 0.04))


def test_a_loaded_knife_lays_as_thick_a_slab_on_the_bare_canvas_at_every_cut():
    """The same load on a knife 110 px wide, on the bare canvas: the slab
    behind the blade is as thick at every cut (to 2.2%, and the test allows
    3%; it was 12.5, 5.5, 2.3 and 0.7% thinner in steps of 8, 4, 2 and 1 px
    than in steps of half a pixel: the blade was set down and went its
    first step at the level it was set down at). How near depends on the
    pull's textures: of six pulls the slab is 0.8 to 2.5% thinner at a
    stroke's own steps, and at most 0.9, 0.3 and 0.1% in steps of 4, 2 and
    1 px. (With the wobble of its width off, as this test had it, this
    pull's was 0.1% thinner and 1% was allowed; six such pulls gave 2.2%
    thinner to 0.9% thicker: it was so before the textures were the same
    at every cut, murex-9t4.)"""
    what = ("thick", "white")
    got = _against_fine(what, way=SLANT, width=110, load=3.0, pressure=0.25, bare=True)
    _within(got, what, (0.03, 0.005))


def test_a_knife_pressed_hard_leaves_as_much_beside_it_at_every_cut():
    """A loaded knife at pressure 0.9, and a clean one at 0.7: what the
    blade spills past its ends is the same at every cut (to 0.6%, and the
    test allows 2%; in steps of 8, 4, 2 and 1 px it left 25, 15, 6 and 2%
    less beside it than in steps of half a pixel, the clean one 16, 9, 4
    and 1% less: what stands above the blade was read once a step, under
    the level the step read ahead of the wave it pushes), and the white the
    loaded one lays (to 1.7%; 2% allowed; it laid up to 5.4% less).

    The bound on the white holds for this pull, not for every one: of six
    pulls (seeds 100 to 105) the loaded knife lays 1.0 to 2.7% more white
    at a stroke's own steps than in steps of half a pixel, so other seeds
    exceed the 2% allowed. It was so before the textures were the same at
    every cut (murex-9t4); the bound is not widened to hide it."""
    what = ("beside", "white", "carried")
    got = _against_fine(what, way=SLANT, width=60, load=3.0, pressure=0.9)
    _within(got, what, (0.02, 0.02, 0.01))
    what = ("beside", "carried")
    got = _against_fine(what, way=SLANT, width=110, load=0.0, pressure=0.7)
    _within(got, what, (0.02, 0.005))


# --- murex-dl9: a skimming knife ------------------------------------------------------


def test_a_skimming_knife_carries_wet_paint_as_far_at_every_cut():
    """A lightly loaded knife skimming the wet dark at pressure 0.05
    carries it as far, and lays as much, at every cut (to 0.05%, and the
    test allows 0.5%; it carried
    1.9, 1.1, 0.6 and 0.3% further in steps of 8, 4, 2 and 1 px, and laid
    0.9% more at a stroke's own steps: the bead on its edge laid its paint
    when the step was over, and till then the blade dragged the paint under
    it as if it had laid none there)."""
    what = ("carried", "white")
    got = _against_fine(what, way=SLANT, width=110, load=0.3, pressure=0.05)
    _within(got, what, (0.005, 0.005))


# --- murex-dq0: a loaded skim over its own colour -------------------------------------


def test_a_loaded_skim_over_its_own_colour_lays_as_much_at_every_cut():
    """White knifed over the wet dark, and then a knife loaded with 8 of
    the same white skimming over it at pressure 0.03: it lays the same
    white at every cut (to 0.1%, and the test allows 1%; 31, 15, 7 and 2%
    more in steps of 8, 4, 2
    and 1 px than in steps of half a pixel, where it came to rest, a little
    more at each step, on what it had just laid: that paint had joined the
    white under it and passed for the earlier stroke's)."""
    what = ("white", "thick")
    got = _against_fine(
        what,
        way=SLANT,
        width=110,
        load=8.0,
        pressure=0.03,
        first=(0.5, 1.5),
    )
    _within(got, what, (0.01, 0.01))


# --- murex-dnj: the roll of a blade barely touching ----------------------------------
SKIM_WAY = [(70.0, 70.0), (231.8, 187.7)]  # (200 px down a slant)
SKIM_CURVE = [(60.0, 70.0), (150.0, 100.0), (250.0, 205.0)]


def _skim_cuts(ground, pressure=0.03, path=SKIM_WAY, load=8.0, **how):
    """White skimmed over ``ground`` (what gives the canvas) at
    ``pressure`` with a knife 110 px wide, the blade across the pull: for
    each of CAPS, how far what it lays is from what it lays in steps of
    FINE, in all (a share) and place by place (the root mean square of
    the difference, each smoothed over 7 px, as a share of that of what
    the fine one lays). Every pull keeps its paint."""
    blade = {
        "angle": math.degrees(math.atan2(80.0, 110.0)) - 90.0,
        "follow_path": False,
    }
    blade.update(how)
    laid = {}
    for cap in (FINE, *CAPS):
        c = ground()
        knife = Brush(brushes.knife("straight", 110, flex=0.5))
        knife.load(P.TITANIUM_WHITE, load)
        wet = c.wet_thickness.astype(np.float64)
        before = _totals(c, knife)
        longest = stm._MAX_STEP
        stm._MAX_STEP = cap
        try:
            c.stroke(path, brush=knife, pressure=pressure, seed=100, lift=0.0, **blade)
        finally:
            stm._MAX_STEP = longest
        after = _totals(c, knife)
        assert np.abs(after - before).max() / np.abs(before).max() < 1e-7, cap
        laid[cap] = c.wet_thickness.astype(np.float64) - wet
    fine = _smoothed(laid[FINE])
    out = {}
    for cap in CAPS:
        off = _smoothed(laid[cap]) - fine
        out[cap] = (
            laid[cap].sum() / laid[FINE].sum() - 1.0,
            math.sqrt((off**2).mean() / (fine**2).mean()),
        )
    return out


def _smoothed(a):
    """``a`` averaged over 7 by 7 pixels."""
    return box_blur(a, 3)


@pytest.mark.parametrize("base", ["knifed", "brushed"])
@pytest.mark.parametrize("surface", [None, "LINEN_COARSE"])
def test_a_skim_lays_the_same_sheet_at_every_cut(dark_ground, surface, base):
    """White skimmed at pressure 0.03, where the bead on the blade's edge
    lays as a roll (_knife._Roll), on the default canvas and on
    LINEN_COARSE, over a dark knifed thin and over one brushed rough and
    textured: it lays the same white in steps of 8, 4, 2 and 1 px as in
    steps of half a pixel, in all (to 0.003% on the four grounds, and the
    test allows 0.1%) and place by place (to 0.32% root mean square at a
    stroke's own steps, smoothed over 7 px, 0.13% in steps of 4 px and
    0.05% in steps of 2; 1% allowed).

    Where the roll lays is settled before the stroke, over the stroke,
    from the surface as it lay then: no step reads anything of it that
    changes while the stroke lasts. (The bead as it was, on the same four
    grounds with the same textures: 0.03 to 0.11% in all and 0.4 to 0.6%
    place by place. The study of murex-dnj found its prototype 1.3% off in
    all and 6% place by place on the brushed LINEN_COARSE, and the bead as
    it was 84% off place by place there: it was measured before a
    stroke's textures were the same at every cut, murex-9t4, when every
    cut had other nicks.)"""
    got = _skim_cuts(lambda: dark_ground(surface, base))
    for cap, (total, place) in got.items():
        assert abs(total) < 0.001, (cap, total)
        assert place < 0.01, (cap, place)


@pytest.mark.parametrize(
    ("pull", "most"),
    [
        ({"pressure": 0.0}, (0.001, 0.01)),
        ({"pressure": 0.055}, (0.002, 0.01)),
        ({"pressure": [0.0, 0.04]}, (0.001, 0.01)),
        ({"pressure": [0.02, 0.09]}, (0.006, 0.025)),
        ({"path": SKIM_CURVE, "angle": 0, "follow_path": True}, (0.001, 0.01)),
        ({"path": SKIM_CURVE}, (0.001, 0.01)),
    ],
    ids=[
        "no pressure",
        "between the two rules",
        "pressed harder, the roll alone",
        "pressed harder, past the roll",
        "round a curve",
        "round a curve, the blade held",
    ],
)
def test_a_skim_lays_the_same_at_every_cut_whatever_the_pull(dark_ground, pull, most):
    """On the brushed LINEN_COARSE, the roughest of the four grounds, at
    every cut against steps of half a pixel, in all and place by place
    (see :func:`_skim_cuts`): a pull with no pressure at all (0.01% and
    0.38%); one at pressure 0.055, where the roll is going out and the
    bead's catching coming in (0.03% and 0.30%); one pressed from nothing
    at its start to 0.04 at its end, which reads the pressure where each
    place is; one round a curve, its blade turning with it (0.006% and
    0.12%) or held as it was set down (0.003% and 0.28%). The test allows
    0.1% and 1% (0.2% between the two rules).

    A pull pressed from 0.02 to 0.09 is 0.30% and 1.55% off at a stroke's
    own steps (0.14% and 0.72% in steps of 4 px), and the test allows 0.6%
    and 2.5%: that is not the roll's. Past 0.05 the blade spreads its
    film, by the pressure of each step, which is the mean of its two
    ends': with no roll at all the same pull is 0.30% and 1.59% off."""
    got = _skim_cuts(lambda: dark_ground("LINEN_COARSE", "brushed"), **pull)
    for cap, (total, place) in got.items():
        assert abs(total) < most[0], (cap, total)
        assert place < most[1], (cap, place)


# --- murex-h6u: the ripple down a slant -----------------------------------------------


def test_a_pull_down_a_slant_ripples_the_same_at_every_cut():
    """A pull at 45 degrees at pressure 0.5: the surface behind the blade
    ripples by 0.066 units along the pull at every cut (0.055 with the
    wobble of its width off; the test allows 8% between the cuts, and
    0.075 units, which holds for this pull and not for every one: six
    pulls with other seeds ripple by 0.040 to 0.084 units, as their
    textures fall, and it was so before murex-9t4): what sub-steps of 0.7
    px of the paint's way give
    (_engine.RIDE_CFL). It rippled by 0.048, 0.030, 0.022, 0.015 and 0.013
    in steps of 8, 4, 2, 1 and half a pixel, the sub-steps of the flow
    under the blade being whole divisions of each step. The blade carries
    the dark as far and lays as much white (to 0.1%, and the test allows
    1%; it laid 2.1% less at a stroke's own steps)."""
    what = ("ripple", "carried", "white")
    got = _against_fine(what, way=DIAGONAL, width=110, load=0.3, pressure=0.5)
    _within(got, what, (0.08, 0.01, 0.01))
    assert _pull(8.0, way=DIAGONAL, width=110, load=0.3, pressure=0.5)["ripple"] < 0.075


# --- other grounds, other ways of holding the blade ----------------------------------
UMBER = P.BURNT_UMBER


@functools.cache
def _brushed():
    """Thick wet umber brushed on in overlapping strokes: a textured ground,
    with the furrows and ridges a hog brush leaves."""
    c = Canvas(360, 260, seed=4)
    for y in range(8, 260, 14):
        c.stroke(
            [(-10, y), (180, y + 3), (370, y)],
            UMBER,
            amount=14,
            brush=brushes.FLAT_HOG.sized(30),
            pressure=0.5,
            seed=y,
        )
    return c


def _umber(canvas):
    """The volume of umber at each pixel, the two wet layers together."""
    pig = np.stack(
        [np.concatenate([p.K, [p.S, 1.0]]) for p in (UMBER, P.TITANIUM_WHITE)], axis=1
    )
    scale = 1.0 / np.abs(pig).max(axis=1)
    a = (canvas.top.astype(np.float64) + canvas.und)[..., : IV + 1] * scale
    sol, *_ = np.linalg.lstsq(pig * scale[:, None], a.reshape(-1, IV + 1).T, rcond=None)
    return sol.T.reshape(a.shape[:2] + (2,))[..., 0]


def _drag(cap, path, width, load, pressure, **how):
    """A knife ``width`` px wide loaded with ``load`` of white taken along
    ``path`` over the brushed ground in steps of ``cap`` px at most
    (``how``: the stroke's other settings). Returns how far it carried the
    umber (volume times distance along the path's chord), how much umber
    it moved in all, and how far the paint on the canvas, on the blade and
    gone over the edge is from what there was."""
    c = _brushed().copy()
    bt = brushes.knife("straight", width, flex=0.5)
    knife = Brush(bt).load(P.TITANIUM_WHITE, load) if load > 0 else Brush(bt)
    umber = _umber(c)
    before = _totals(c, knife)
    longest = stm._MAX_STEP
    stm._MAX_STEP = cap
    try:
        c.stroke(path, None, brush=knife, pressure=pressure, seed=11, **how)
    finally:
        stm._MAX_STEP = longest
    after = _totals(c, knife)
    (x0, y0), (x1, y1) = path[0], path[-1]
    length = math.hypot(x1 - x0, y1 - y0)
    yy, xx = np.mgrid[0 : c.height, 0 : c.width]
    s = ((xx + 0.5 - x0) * (x1 - x0) + (yy + 0.5 - y0) * (y1 - y0)) / length
    moved = _umber(c) - umber
    return (
        float((moved * s).sum()),
        float(np.abs(moved).sum()),
        float(np.abs(after - before).max() / np.abs(before).max()),
    )


@pytest.mark.parametrize(
    ("path", "knife", "how", "most"),
    [
        # square to its way, over the furrows of the brushed ground (it
        # carried the umber 9.2% further in its own steps, and moved 6.7% more)
        ([(40, 130), (320, 130)], (60, 3.0, 0.25), {"lift": 0.0}, (0.02, 0.02)),
        # edge-on: pulled along its own length (19.2% further, 13.0% more)
        (
            [(40, 130), (320, 130)],
            (60, 3.0, 0.25),
            {"angle": 0, "follow_path": False, "lift": 0.0},
            (0.03, 0.03),
        ),
        # lifted off at the end, pulling the paint up (7.9% further, 4.4% more)
        ([(40, 130), (300, 110)], (80, 3.0, 0.5), {"lift": 1.0}, (0.02, 0.02)),
        # leaving the canvas over its edge (44% less far, 10.8% more)
        ([(200, 130), (420, 140)], (60, 2.0, 0.5), {"lift": 0.0}, (0.04, 0.02)),
    ],
    ids=["square", "edge-on", "lifted", "over-the-edge"],
)
def test_a_loaded_knife_over_a_brushed_ground_at_its_own_steps(path, knife, how, most):
    """A knife loaded with white pulled across thick brushed umber, four
    ways: at a stroke's own steps it carries the umber as far, and moves
    as much of it, as in steps of half a pixel (to 0.2 and 0.0% square to
    its way, 1.3 and 1.9% edge-on, 0.4 and 0.1% lifted off, 2.2 and 0.3%
    leaving over the edge; the test allows what is beside each case, with
    what it was). Every channel is kept."""
    own = _drag(8.0, path, *knife, **how)
    fine = _drag(FINE, path, *knife, **how)
    assert own[2] < 1e-7 and fine[2] < 1e-7
    for name, a, b, tol in zip(("carried", "moved"), own, fine, most, strict=False):
        assert abs(a / b - 1.0) < tol, (name, a / b)


def test_a_clean_knife_over_a_brushed_ground_does_what_it_did():
    """A clean blade 60 px wide pulled at pressure 0.3 across the brushed
    umber, in steps of 2 px: it carries the umber 118,800 units times px and
    moves 4,290 units of it in all (the test allows 2%). With the wobble of
    its width off, as these tests had it before murex-9t4, it was another
    pull, which carried 121,500 and moved 4,250: what that one did in steps
    of half a pixel before a knife's stroke was made the same at every cut
    (121,900 and 4,240: within 0.4%). Nothing but the cut was to change
    for it: no part of the change gives a pull over a textured ground
    another character. (With what stands in a blade's way spread across
    its way, as it was for a while, such a pull carried 15% further and
    moved a third more.) The figures of today's pull were not measured on
    that older engine: they are what this one gave when the textures were
    made the same at every cut, when the pull with its wobble off still
    gave the older figures."""
    _brushed()
    carried, moved, kept = _drag(2.0, [(40, 120), (320, 150)], 60, 0.0, 0.3, lift=0.0)
    assert kept < 1e-7
    assert carried == pytest.approx(118800.0, rel=0.02)
    assert moved == pytest.approx(4290.0, rel=0.02)


@functools.cache
def _dried():
    """Ridges of thick paint brushed across the canvas, 12 px apart, dry."""
    c = Canvas(400, 200, seed=7)
    for y in range(40, 170, 12):
        c.stroke(
            [(20, y), (380, y)],
            P.IVORY_BLACK,
            amount=30,
            brush=brushes.FLAT_HOG.sized(24),
            seed=1,
        )
    c.dry()
    return c


@functools.cache
def _specked():
    """The dried ridges with a speck of wet paint on them every 9 px, 0.02
    units thick: far too thin to hold a blade up."""
    glazed = _dried().copy()
    glazed.stroke(
        [(60, 20), (200, 180)],
        P.ULTRAMARINE_BLUE,
        amount=0.3,
        brush=brushes.FLAT_HOG.sized(40),
        pressure=0.3,
        seed=2,
    )
    wet = glazed.top[..., IV]
    at = np.unravel_index(np.argmax(wet), wet.shape)
    c = _dried().copy()
    for y in range(45, 160, 9):
        for x in range(45, 200, 9):
            c.top[y, x] = glazed.top[at] * np.float32(0.02 / wet[at])
            c.top_a[y, x] = glazed.top_a[at]
            c.top_id[y, x] = 1  # (an earlier stroke's)
    return c


def _skimmed(ground, pressure, cap):
    """How much a small knife skimming across ``ground`` at ``pressure``
    lays, its strokes cut into steps of ``cap`` px at most."""
    c = ground.copy()
    before = float(c.thickness.astype(np.float64).sum())
    knife = Brush(brushes.knife("straight", 40, flex=0.5))
    knife.load(P.TITANIUM_WHITE, 0.22)
    longest = stm._MAX_STEP
    stm._MAX_STEP = cap
    try:
        c.stroke(
            [(60, 60), (120, 100), (180, 140)],
            brush=knife,
            pressure=pressure,
            seed=1,
            angle=-40,
            follow_path=False,
            lift=0.0,
        )
    finally:
        stm._MAX_STEP = longest
    return float(c.thickness.astype(np.float64).sum()) - before


@pytest.mark.parametrize("pressure", [0.1, 0.3])
def test_a_knife_skimming_dried_ridges_lays_as_much_at_its_own_steps(pressure):
    """A small knife skimming across dried ridges lays as much in a
    stroke's own steps as in steps of half a pixel (to 0.2%, and the test
    allows 1%; it laid 3.8% more at pressure 0.1 and 2.4% less at 0.3, more
    or less as its steps fell on the ridges: where the blade rests on a
    dried relief was read once a step. Over dried paint with nothing wet
    on it to hold the blade up, a knife's steps are now 2 px long at most,
    stroke._DRY_STEP)."""
    _dried()
    laid = [_skimmed(_dried(), pressure, cap) for cap in (8.0, FINE)]
    assert abs(laid[0] / laid[1] - 1.0) < 0.01, laid


def test_specks_of_wet_paint_on_dried_ridges_do_not_bring_the_long_steps_back():
    """The same skim at pressure 0.1 over the same ridges with a speck of
    wet paint 0.02 units thick on them every 9 px: as much in a stroke's
    own steps as in steps of half a pixel (to 0.2%, and the test allows
    1%). Any wet paint at all under a step kept its steps long, and it
    laid 2.0% more, as if the ridges were none of a knife's business: only
    wet paint a blade would ride on counts (_knife._KNIFE_RIDES_ON)."""
    _specked()
    laid = [_skimmed(_specked(), 0.1, cap) for cap in (8.0, FINE)]
    assert abs(laid[0] / laid[1] - 1.0) < 0.01, laid


def test_a_knife_takes_short_steps_over_a_dried_relief_and_nowhere_else(monkeypatch):
    """A knife's steps are cut short (stroke._DRY_STEP) over dried ridges,
    with or without specks of wet paint on them, and not over the bare
    canvas, nor over the same ridges a tenth of a unit thick at most,
    which are no more of a relief than the weave (stroke._DRY_RELIEF; any
    dried paint at all cut them short), nor over wet paint thick enough to
    ride on, where the flow under the blade takes steps of its own."""
    cut = stm._Run._parts
    parts = []

    def counted(self, seg):
        out = cut(self, seg)
        parts.append(len(out))
        return out

    monkeypatch.setattr(stm._Run, "_parts", counted)

    def steps(ground):
        parts.clear()
        _skimmed(ground, 0.1, 8.0)
        return sum(parts)

    thin = _dried().copy()
    thin.dry_height *= np.float32(0.1 / float(thin.dry_height.max()))
    thin._update_relief()
    wet = Canvas(400, 200, seed=7)
    wet.stroke(
        [(40, 100), (220, 100)], DARK, amount=30, brush=brushes.FLAT_HOG.sized(120)
    )
    wet_on_dried = _dried().copy()
    wet_on_dried.top[...] = wet.top
    wet_on_dried.top_a[...] = wet.top_a
    wet_on_dried.top_id[...] = wet.top_id
    bare = steps(Canvas(400, 200, seed=7))
    assert steps(_dried()) > 3 * bare
    assert steps(_specked()) == steps(_dried())
    assert steps(thin) == bare
    assert steps(wet_on_dried) == bare


# --- the steps themselves -------------------------------------------------------------


def test_a_knife_is_set_down_and_lifted_off_in_steps_of_their_own(monkeypatch):
    """A knife's stroke begins with a step that sets the blade down and
    ends with one that lifts it off, an eighth of a pixel long each, and
    the way between is the stroke's (a blade laid a third of its load or
    more as it was set down, and then went a whole step at the level it
    was set down at). A dab is one step, as it was."""
    steps = []
    step = stm._knife_step

    def spy(run, s):
        motion = s.st.motion
        steps.append((motion.ds, bool(motion.first), bool(motion.last)))
        return step(run, s)

    monkeypatch.setattr(stm, "_knife_step", spy)
    c = Canvas(200, 120, seed=1)
    knife = Brush(brushes.knife("straight", 40)).load(P.TITANIUM_WHITE, 2.0)
    c.stroke([(40, 60), (160, 60)], brush=knife, pressure=0.5)
    lengths = [ds for ds, _, _ in steps]
    assert lengths[0] == stm._SET_DOWN == lengths[-1]
    assert max(lengths) <= stm._MAX_STEP and min(lengths[1:-1]) > 1.0
    assert sum(lengths) == pytest.approx(120.0, abs=1e-5)
    assert [first for _, first, _ in steps] == [True] + [False] * (len(steps) - 1)
    assert [last for _, _, last in steps] == [False] * (len(steps) - 1) + [True]
    steps.clear()
    c.stroke([(100, 30)], brush=knife, pressure=0.5)
    assert len(steps) == 1


@pytest.mark.parametrize("move", [(37, 53), (51, 70), (128, 256)])
def test_a_knife_stroke_moved_by_whole_pixels_is_the_same_stroke(move):
    """A knife pulled through wet paint, and the same strokes a whole
    number of pixels further on on a larger canvas: the same paint, to the
    bit, wherever they are (a knife's path lies on a grid, see
    stroke._PATH_GRID: off it, the steps of the moved stroke came out a few
    units in the last place longer or shorter, and that showed in a last
    bit of the paint of a pixel or of 250, as the move fell)."""

    def paint(dx, dy):
        c = Canvas(280 + 2 * dx, 120 + 2 * dy, texture=0, seed=1)
        c.stroke(
            [(60 + dx, 50 + dy), (140 + dx, 70 + dy), (220 + dx, 55 + dy)],
            P.ULTRAMARINE_BLUE,
            amount=12,
            brush=brushes.FLAT_HOG,
            seed=3,
        )
        knife = Brush(brushes.PALETTE_KNIFE).load(P.TITANIUM_WHITE, 4)
        c.stroke([(70.3 + dx, 75.1 + dy), (210.7 + dx, 60.9 + dy)], brush=knife, seed=5)
        return c

    dx, dy = move
    here, there = paint(0, 0), paint(dx, dy)
    for name in ("top", "und", "top_a", "und_a"):
        moved = getattr(there, name)[dy : dy + 120, dx : dx + 280]
        assert getattr(here, name).tobytes() == moved.tobytes(), name

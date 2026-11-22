"""A knife dragging wet paint must not show how its stroke is cut into steps.

A knife pulled across thick wet paint left ribs parallel to its blade, one
per step of the stroke, for two reasons, each tested here on its own and
then together on the stroke that showed them:

- the film flow under the blade (_engine.flow_under_blade) worked out the
  speed of each wet layer apart. Where the blade has laid its own film, the
  old top layer has gone under: along that line, drawn afresh at every step,
  the flow fell to about half, and paint heaped up behind it and was drained
  ahead of it;
- the blade laid its own paint (_knife._slab) in the gap the canvas showed
  under it when the step ended. The paint it drags travels under it, so that
  gap, read once per step, printed the shape of the paint under the blade at
  every step.
"""

import importlib.util
import os
import sys

import numpy as np

import murex.huile.stroke as stm
from murex import spline
from murex.huile import Brush, Canvas, Paint
from murex.huile import _engine as eng
from murex.huile import palette as P
from murex.huile._engine import IB, IS, IV, PACKED


def _load_probe():
    """tools/huile/knife_probe.py, which measures these ribs, as a module
    (the entries it puts on ``sys.path`` are taken off again)."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "tools", "huile", "knife_probe.py"
    )
    spec = importlib.util.spec_from_file_location("huile_tools_knife_probe", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    saved_path = list(sys.path)
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = saved_path
    return module


probe = _load_probe()

# --- the film flow alone, on a flat bed ------------------------------------------
H, W = 24, 120
SID = 7  # the stroke's id
BED = 2.4  # how thick the earlier strokes' paint lies
DARK = Paint(probe.DARK)


def _packed(paint, volume):
    out = np.zeros(PACKED, np.float32)
    out[:IS] = paint.K * volume
    out[IS] = paint.S * volume
    out[IV] = volume
    out[IB] = paint.body * volume
    return out


def _bed(film_on):
    """A flat bed of dark, BED thick. On the columns ``film_on`` the blade
    has laid a thin film of its own white: the dark is in the layer below
    there, as deposit leaves it; elsewhere it is the top layer."""
    top = np.zeros((H, W, PACKED), np.float32)
    und = np.zeros((H, W, PACKED), np.float32)
    top[:] = _packed(DARK, BED)
    ids = np.zeros((H, W), np.int32)
    und[:, film_on] = top[:, film_on]
    top[:, film_on] = _packed(P.TITANIUM_WHITE, 0.03)
    ids[:, film_on] = SID
    one = np.ones((H, W), np.float32)
    return eng.Layers(top=top, und=und, top_a=one, und_a=one.copy(), top_id=ids)


FILM = 0.17  # how thick the film on the blade is


def _sweep(cv, level, end=60.0, ds=8.0, film=FILM, hang=None, bead=None):
    """A blade 22 px along its way, over every row, at ``level`` over the
    canvas, goes ``ds`` px along +x and ends centred on ``end``, carrying a
    ``film`` of paint, its bead (``bead`` tall: the film) hanging from
    ``hang`` (the level). Returns what it met (see
    _engine.flow_under_blade)."""
    along = np.tile(np.arange(W) + 0.5 - end, (H, 1))
    full = np.full((H, W), 1.0)
    hang = level if hang is None else hang
    bead = film if bead is None else bead
    return eng.flow_under_blade(
        cv, 0, 0, SID, 0.0 * full, level * full, full, along, 0.0 * full,
        11.0 * full, ds, 1.0, 0.0, 0.6 * full, 3, film * full, hang * full,
        bead * full,
    )  # fmt: skip


def _old_paint(cv):
    """How thick the earlier strokes' paint lies along the middle row."""
    own = cv.top_id == SID
    return (cv.und[..., IV] + np.where(own, 0.0, cv.top[..., IV]))[H // 2]


def test_the_film_flow_does_not_see_which_layer_holds_the_old_paint():
    """One step of the flow moves the old paint the same way whether it is
    the top layer, lies under the blade's own film, or changes from one to
    the other under the blade. (Across that line the old paint ended up to
    0.95 units off, of 2.4, with the blade 0.2 into it: a heap of 3.1 behind
    the line and a hollow of 1.3 ahead of it; 0.3 off with the blade riding
    0.6 above it.)"""
    for level in (2.2, 3.0):
        plain = _bed(slice(0, 0))
        _sweep(plain, level)
        want = _old_paint(plain)
        assert np.abs(want - BED).max() > 0.3  # (the blade does drag it)
        for film_on in (slice(0, 60), slice(0, 66), slice(60, W), slice(0, W)):
            cv = _bed(film_on)
            _sweep(cv, level)
            assert np.abs(_old_paint(cv) - want).max() < 0.01, (level, film_on)


def test_old_paint_dragged_in_goes_under_the_blades_own_film():
    """The film the blade has laid stays as it is, and where it is: the old
    paint the flow brings to a pixel under it joins the layer below. (It
    joined the film, which does not move: a thin white film over dark took
    in the dark dragged to it and kept it, a dark rib in the white.)
    Nothing is made or lost."""
    cv = _bed(slice(60, W))  # (the film ahead of the old top layer)
    film = cv.top[:, 60:].copy()
    before = (cv.top.astype(np.float64) + cv.und).sum(axis=(0, 1))
    _sweep(cv, 2.2)
    assert cv.top[:, 60:].tobytes() == film.tobytes()
    assert cv.und[:, 60:, IV].max() > BED + 0.3  # (dragged in, under it)
    after = (cv.top.astype(np.float64) + cv.und).sum(axis=(0, 1))
    np.testing.assert_allclose(after, before, rtol=2e-6)


def test_the_flow_tells_the_gap_the_blade_met_under_it():
    """The flow returns the gap the blade's film could fill over each pixel
    while the blade was over it (below 0 where it never was; nothing at all
    if the blade touches no wet paint), and the surface as its bead found
    it. A blade 0.1 above a flat bed: behind it, where it has drawn paint
    away, the surface lies deeper than its bead reaches (the film on it,
    0.17), and is taken to lie that far down; ahead, the paint it pushes
    stands against it, and leaves no gap."""
    level = BED + 0.1
    gaps = _sweep(_bed(slice(0, 0)), level)
    assert gaps.shape == (H, W, 2)
    fill, bead = gaps[H // 2, :, 0], level - gaps[H // 2, :, 1]
    # (the blade went from over columns 41..63 to over 49..71)
    assert (gaps[:, :41, 0] == -1.0).all() and (gaps[:, 72:, 0] == -1.0).all()
    assert (fill[42:71] >= 0).all() and (fill[42:71] <= bead[42:71] + 1e-12).all()
    np.testing.assert_allclose(bead[42:46], FILM, atol=1e-6)
    assert fill[48:60].min() > 0.03 and fill[48:60].max() < 0.13
    assert fill[66:71].max() == 0.0 and np.abs(bead[66:71]).max() < 1e-12
    # (the blade far above the paint: it touches none, and tells nothing)
    assert _sweep(_bed(slice(0, 0)), BED + 2.0).shape == (0, 0, 2)


def test_the_bead_meets_the_surface_from_the_level_it_hangs_from():
    """A skimming blade loaded with more paint than its bead is tall rides
    on that paint, above the level its bead hangs from (_knife._blade_level;
    murex-iaa). What the flow tells of the surface the bead met is measured
    from that level, sub-step by sub-step: the same as the flow taken a
    sub-step at a time, reading the canvas after each. (The film: 3 units;
    the bead: 1.2, hanging 0.3 below the blade's level, at the top of the
    bed. Measured from the blade's level, the surface would have been found
    0.3 further off all along.)"""
    level, hang, film, bead = BED + 0.3, BED, 3.0, 1.2
    one = _bed(slice(0, 0))
    got = _sweep(one, level, film=film, hang=hang, bead=bead)
    stepped = _bed(slice(0, 0))
    total, weight = np.zeros((H, W)), np.zeros((H, W))
    for k in range(1, 9):
        end = 52.0 + k  # (the blade's centre after this sub-step)
        _sweep(stepped, level, end=end, ds=1.0, film=film, hang=hang, bead=bead)
        over = np.clip(11.0 - np.abs(np.arange(W) + 0.5 - end) + 0.5, 0.0, 1.0)
        surface = (stepped.top[..., IV] + stepped.und[..., IV]).astype(np.float64)
        total += over * np.clip(hang - surface, 0.0, bead)
        weight += over
    assert one.top.tobytes() == stepped.top.tobytes()  # (the same flow)
    under = weight[H // 2] > 0
    assert under.sum() > 25 and (got[H // 2, under, 0] >= 0).all()
    want = hang - total[:, under] / weight[:, under]
    np.testing.assert_allclose(got[:, under, 1], want, rtol=0, atol=1e-12)
    # (the bead is clear of the surface behind the blade, where it has drawn
    # paint away, and pressed against it ahead)
    depth = hang - got[H // 2, under, 1]
    assert depth.max() > 0.1 and depth[-5:].max() < 1e-12


def test_the_bead_is_as_tall_in_the_flow_as_where_it_lays(monkeypatch, by_name):
    """How tall the bead is, is one number in one place: the flow is told it
    by _knife._drag_film, from the constant _knife._slab lays the bead by
    (_KNIFE_BEAD_HEIGHT), not from a copy of it in the engine; under a blade
    resting on the canvas alone (the first pull of the base) and under one
    riding on wet paint (see _engine.flow_under_riding_blade)."""
    from murex.huile import _knife

    seen = {"flow_under_blade": [], "flow_under_riding_blade": []}

    def spied(name):
        flow = getattr(eng, name)

        def spy(*args):
            given = by_name(flow, args)
            seen[name].append((given["film"].copy(), given["bead"].copy()))
            return flow(*args)

        return spy

    for name in seen:
        monkeypatch.setattr(eng, name, spied(name))
    monkeypatch.setattr(_knife, "_KNIFE_BEAD_HEIGHT", 0.5)
    c = Canvas(200, 120, seed=3)
    probe.dark_base(c, 3.0)
    knife = Brush(probe.SNOW_KNIFE.sized(60)).load(P.TITANIUM_WHITE, 3.0)
    c.stroke([(40, 60), (160, 62)], None, brush=knife, angle=90, pressure=0.08)
    for calls in seen.values():
        assert len(calls) > 5
        assert any((film > 0.5).any() for film, _ in calls)
        for film, bead in calls:
            assert bead.tobytes() == np.minimum(film, 0.5).tobytes()


# --- the stroke that showed the ribs (tools/huile/knife_probe.py ribs) -----------
START = (90, 50)
_BASES: dict = {}


def _dark():
    """The wet dark the pulls go across (a copy: laid once, in its own
    steps)."""
    if "dark" not in _BASES:
        c = Canvas(420, 300, seed=1)
        probe.dark_base(c, 5.0, 0.7)
        _BASES["dark"] = c
    return _BASES["dark"].copy()


def _pull(k=1, seed=None, pressure=0.25, step=None):
    """White knifed across a thick wet dark at pressure 0.25, its path cut
    into steps ``k`` times shorter than a stroke's (and of ``step`` px at
    most, where a stroke's are of 8). Returns (the ripple of the wet
    paint's thickness along the pull, the ripple of the volume of white
    along it over its mean)."""
    c = _dark()
    x, y = START
    path = [(x, y), (x + 110, y + 80), (x + 220, y + 160)]
    longest = stm._MAX_STEP
    stm._MAX_STEP = longest if step is None else step
    try:
        c.stroke(
            _Finer(path, k) if k > 1 else path,
            None,
            brush=Brush(probe.SNOW_KNIFE).load(P.TITANIUM_WHITE, 0.3),
            angle=probe.ACROSS,
            follow_path=False,
            pressure=pressure,
            lift=0.0,
            seed=seed,
        )
    finally:
        stm._MAX_STEP = longest
    # (as the probe measures them: along the pull, averaged along the blade)
    wet = probe.along_the_pull(c.wet_thickness.astype(np.float64), START)
    laid = probe.along_the_pull(_white(c), START)
    wave = (laid - np.convolve(laid, np.ones(17) / 17, "same"))[20:-20]
    return probe.ripple(wet)[0], float(wave.std() / laid.mean())


class _Finer(spline.Path):
    """A path sampled ``k`` times as finely as a stroke asks."""

    def __init__(self, points, k):
        self.path, self.k = spline.as_path(points), k
        self.n_knots = self.path.n_knots

    def _dense(self):
        return self.path._dense()

    def sample(self, spacing):
        return self.path.sample(spacing / self.k)


_PIGMENTS = np.stack(
    [np.concatenate([p.K, [p.S, 1.0]]) for p in (DARK, P.TITANIUM_WHITE)], axis=1
)
_SCALE = 1.0 / np.abs(_PIGMENTS).max(axis=1)


def _white(canvas):
    """The volume of white at each pixel, the two wet layers together."""
    a = (canvas.top + canvas.und)[..., : IV + 1].astype(np.float64) * _SCALE
    sol, *_ = np.linalg.lstsq(
        _PIGMENTS * _SCALE[:, None], a.reshape(-1, IV + 1).T, rcond=None
    )
    return sol.T.reshape(a.shape[:2] + (2,))[..., 1]


def test_a_knife_dragging_thick_wet_paint_leaves_no_rib_at_its_steps():
    """The stroke of the issue: the wet paint under it ripples along it by
    0.037 units (root mean square about a 17 px running mean), less than the
    dark base did before the stroke (0.057); it was 0.118, a rib every 7.8
    px, the step. The white the blade leaves is even along the pull to 0.063
    of its thickness (it was 0.26: a bright line per step). (0.030 and
    0.046 while the blade rode too low at a stroke's own steps and dragged
    the unevenness of the base away: murex-kau.)"""
    wet, white = _pull()
    assert wet < 0.06
    assert white < 0.12


def test_a_knife_pull_cut_twice_as_fine_ripples_the_same():
    """The same pull in steps half as long leaves much the same surface
    (three strokes each: 0.057 against 0.048 units of ripple, each within
    0.01 from stroke to stroke; it was 0.135 against 0.065), and as even a
    film of white (0.055 and 0.063 of its thickness; it was 0.29 and 0.16):
    the steps of a stroke give what only short ones gave. (The two cuts do
    not have the same textures, which are drawn point by point along the
    path: with the same ones they ripple by 0.066 and 0.065.)"""
    coarse = np.mean([_pull(1, seed) for seed in (100, 101, 102)], axis=0)
    fine = np.mean([_pull(2, seed) for seed in (100, 101, 102)], axis=0)
    assert 0.5 < coarse[0] / fine[0] < 1.5
    assert coarse[1] < 0.12 and fine[1] < 0.12


def test_a_knife_pressed_into_wet_paint_does_not_waver_at_some_steps(same_textures):
    """At pressure 0.5 the blade rides on the wave of paint it pushes, and
    the surface it leaves is as even at a stroke's own steps as in steps of
    4 px and of 2 (two strokes, each with the same textures at every step:
    0.024, 0.024 and 0.025 units of ripple between them). It wavered in
    steps of 4 and 2 px (0.030, 0.044 and 0.042 units; 0.025 in steps of 1
    px): its level was read once per step, ahead of the wave it rides on,
    and the flow under it took sub-steps of whatever length fitted the step
    (see _engine.RIDE_CFL). (With the level read under where the blade
    stands as the step begins, it wavered at a stroke's own steps too:
    0.10, murex-kau.)"""
    _dark()  # (laid with its own textures, before the pulls' are matched)
    same_textures()
    seeds = (102, 103)
    own = np.mean([_pull(1, seed, 0.5)[0] for seed in seeds])
    assert own < 0.04
    for step in (4.0, 2.0):
        fine = np.mean([_pull(1, seed, 0.5, step)[0] for seed in seeds])
        assert 0.8 < own / fine < 1.25, (step, own, fine)

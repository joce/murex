"""One step of a knife: a rigid blade riding on the paint, laying its load
as a slab, dragging the wet paint under it and pushing it aside, and lifted
off at the end."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, NamedTuple

import numpy as np

from ..filters import smoothstep
from ..noise import aniso_noise, value_noise_2d
from . import _engine as eng
from ._engine import COLUMNS, IB, IV, PACKED
from ._geometry import _Step
from ._hair import _NO_TEX2

if TYPE_CHECKING:
    from .stroke import _Run

# --- knives --------------------------------------------------------------------
# How high a knife blade rides above the surface with no pressure (paint thickness
# units).
_KNIFE_GAP = 16.0
# Paint a knife carries on its blade beyond what fits under it (load units).
_KNIFE_CARRY = 1.5
# How far the colour bands of a loaded knife wander sideways (in blade half-lengths).
_KNIFE_BAND_WANDER = 0.12
# Share of the wet paint standing above a moving blade near the edges of its
# mark that spills out sideways as lips (the rest is bulldozed ahead), and how
# near (px): a narrow mark spills almost all of it, a wide scraper only at its ends.
_KNIFE_SPILL = 0.3
_KNIFE_SPILL_PX = 8.0
# Below about this pressure a knife skims: only the bead of paint on its edge
# touches the high points of the surface.
_KNIFE_SKIM = 0.3
# How much paint a knife presses out beyond the ends of its blade, per unit of
# slab thickness over a pass (times 0.8 + pressure), from how far in from its
# ends (px).
_KNIFE_END = 1.35
_KNIFE_END_PX = 5.0
# How far (px) beyond the end of the blade the paint it presses out lands.
_KNIFE_END_OUT = 2.5
# How much paint the bead on a skimming blade's edge leaves (relative to a
# blade spreading its film), how high the grain must stand for it to catch
# with no pressure at all, and how tall the bead stands at most (paint
# thickness units).
_KNIFE_BEAD = 1.5
_KNIFE_TOUCH = 0.7
_KNIFE_BEAD_HEIGHT = 1.2
# How fast a skimming blade lays as it slides over a pixel, as a length of
# blade along the stroke (px): over each such length the bead leaves
# 1 - e^(-4/n) of its height there, and the film fills (1 - skim) of what a
# blade spreading it fills, n being how many such lengths the blade is
# along the stroke (n = 0.4 + 2h over this, h its half-length along the
# stroke; see _slab). So the longer the blade along the stroke, the more it
# lays, leveling off at 4 times the bead's height. A rate per px of blade,
# not per step: it was the stroke's nominal step, 8 px (what it is for a
# knife 32 px or longer), and a stroke cut into shorter steps laid more
# (murex-86z).
_KNIFE_SKIM_PX = 8.0
# A knife rides no higher than this times the paint film under its blade.
_KNIFE_FILM = 0.5
# Radius (px) over which wet paint dragged by a blade moves together (viscosity).
_VISCOUS = 3
# How deep a knife sinks into wet paint already on the canvas, as a share of
# its thickness: pressure ** _KNIFE_SINK (light touch: skims; hard: nearly all).
_KNIFE_SINK = 1.8


# --- the stage: a knife's stroke that reaches past the edge of the canvas ---------
# How far past each edge of the canvas a stage reaches at most (px). It
# bounds the memory a stroke takes (0.25 KB per pixel of a stage), however
# far out the stroke goes; it models nothing: a blade pushes along the wet
# paint it passes over, so what it brings onto the canvas depends on all of
# its way there. Further out the blade goes on as it did before there was
# a stage (see _knife_step): it lays its paint and drags none. (A blade
# 110 px long coming onto the canvas over 3.6 units of wet paint, in a
# stroke's own steps, with the stage cut at 128 px against one that holds
# all of its way: from 200 px out, the wet paint it brings on is within
# 0.4% at pressures 0.25 and 0.5 and 15% short at 0.9, where it scrapes up
# nearly all it passes over; from 400 px out, within 1%, 4% short and 28%
# short. Cut at 64 px it is 9% over, 2% short and 44% short from 200 px
# out. A blade set down no further out than this is not cut at all.)
_STAGE_FAR = 128
# The planes of a canvas that a stroke changes.
_PAINT = ("top", "und", "top_a", "und_a", "top_id")


def _mirrored(n: int, lo: int, hi: int) -> np.ndarray:
    """Which of the n pixels along one side of a canvas each of the
    positions lo..hi-1 along it reads: itself on the canvas; past its edge,
    the canvas's mirror image there (the pixel at the edge first, as
    numpy.pad's "symmetric"; and that mirrored again, as far as it takes)."""
    at = np.mod(np.arange(lo, hi), 2 * n)
    return np.where(at < n, at, 2 * n - 1 - at)


class _Stage:
    """What the steps of a knife's stroke that reach past the edge of the
    canvas are painted on: the part of the canvas under them, and past its
    edge, as far as they go (see :class:`_Edge`), the canvas going on as
    its own mirror image, wet paint, dried paint and weave, as it was
    before the stroke. On it a step is a step like any other, with canvas
    all round: the wet paint past the edge is dragged, pushed and ridden on
    as on the canvas, and comes onto the canvas with the blade or leaves
    it. :meth:`take` brings its part of the canvas up to date before those
    steps, and :meth:`put_back` puts it back after them; what lies past the
    edge is gone with the stroke.

    (The flow under a blade, _engine.flow_under_blade and
    flow_under_riding_blade, was given the canvas alone: it let paint out
    over the canvas's edge, uncounted, and none in, and what lay past the
    edge was the canvas's edge pixel, still, whatever the blade had done
    there. So the paint under a blade coming on, or set down across the
    edge, drained away from the edge (0.4 to 1.3 units left of 2.4 in the
    first 10 px, where a blade leaves 1.8 behind it), and the blade laid
    its own paint in its place, more or less of it as its stroke was cut
    into steps: murex-duo.)

    The canvas goes on as its mirror image, not as its edge pixel repeated
    (as it does past the stage, and for a brush): the maps a blade reads
    belong together, where it rests on the thread tops around a pixel and
    the surface it fills down to, and repeated pixel by pixel they do not.
    (White knifed onto the canvas over its top edge with a blade 110 px
    long, against the same stroke on a canvas 90 px larger all round: over
    bare canvas it lays 13 to 24% more with the edge pixel repeated, at
    pressures 0.25 and 0.5, and within 2% mirrored; over 3.6 units of wet
    paint at pressure 0.25, 8% more and within 1%.)

    It is all a stroke uses of a canvas (a ``stroke._Canvas``), from
    (``y0``, ``x0``) of the canvas ``on``; ``wet_before`` is how thick the
    wet paint lay on it before the stroke (see :func:`_before_the_blade`)."""

    def __init__(self, on, y0: int, y1: int, x0: int, x1: int):
        H, W = on.height, on.width
        self.on, self.y0, self.x0 = on, y0, x0
        self.height, self.width = y1 - y0, x1 - x0
        self.surface = on.surface
        # (its part of the canvas: there, and here)
        cy0, cy1, cx0, cx1 = max(y0, 0), min(y1, H), max(x0, 0), min(x1, W)
        self._there = (slice(cy0, cy1), slice(cx0, cx1))
        self._here = (slice(cy0 - y0, cy1 - y0), slice(cx0 - x0, cx1 - x0))
        # (how far it reaches past its part of the canvas, each way; where
        # that is further than the part is large, the canvas's mirror image
        # is not that part's: each pixel is looked up)
        self._pads = ((cy0 - y0, y1 - cy1), (cx0 - x0, x1 - cx1))
        self._at = None
        if max(self._pads[0]) > cy1 - cy0 or max(self._pads[1]) > cx1 - cx0:
            self._at = (_mirrored(H, y0, y1)[:, None], _mirrored(W, x0, x1)[None, :])
        self.top = self._goes_on(on.top)
        self.und = self._goes_on(on.und)
        self.top_a = self._goes_on(on.top_a)
        self.und_a = self._goes_on(on.und_a)
        self.top_id = self._goes_on(on.top_id)
        self.dry_height = self._goes_on(on.dry_height)
        relief = on._relief()
        self._relief_maps = type(relief)(*(self._goes_on(m) for m in relief))
        self.wet_before = self.top_v + self.und_v
        # (the slab laid past the stage's own edge: see _laid_off)
        self.knife_off: dict[tuple[int, int], np.ndarray] | None = None

    def _goes_on(self, plane: np.ndarray) -> np.ndarray:
        """The ``plane`` of the canvas over the stage, a copy."""
        if self._at is not None:
            return plane[self._at]
        # (the same, four to ten times as fast for a plane of one number a
        # pixel)
        pads = self._pads + ((0, 0),) * (plane.ndim - 2)
        return np.pad(plane[self._there], pads, mode="symmetric")

    @property
    def top_v(self) -> np.ndarray:
        return self.top[..., IV]

    @property
    def und_v(self) -> np.ndarray:
        return self.und[..., IV]

    def _stroke_rng(self, seed) -> np.random.Generator:
        return self.on._stroke_rng(seed)

    def _new_stroke_id(self) -> int:
        return self.on._new_stroke_id()

    def _relief(self):
        return self._relief_maps

    def _weave_hollows(self) -> np.ndarray:
        return self._goes_on(self.on._weave_hollows())

    def _beyond_weave(self) -> float:
        # (the canvas's: no hollow of the stage is deeper than its deepest)
        return self.on._beyond_weave()

    def take(self, earlier=()) -> None:
        """Bring the stage up to date, before the steps painted on it: its
        part of the canvas, as the canvas is now; and past the edge, where
        the stroke has been before on the stages ``earlier`` (in the order
        it was), what it left there."""
        for name in _PAINT:
            getattr(self, name)[self._here] = getattr(self.on, name)[self._there]
        H, W = self.on.height, self.on.width
        for other in earlier:
            y0, x0 = max(self.y0, other.y0), max(self.x0, other.x0)
            y1 = min(self.y0 + self.height, other.y0 + other.height)
            x1 = min(self.x0 + self.width, other.x0 + other.width)
            if y0 >= y1 or x0 >= x1:
                continue
            ys, xs = np.arange(y0, y1), np.arange(x0, x1)
            past = ((ys < 0) | (ys >= H))[:, None] | ((xs < 0) | (xs >= W))[None, :]
            here = (
                slice(y0 - self.y0, y1 - self.y0),
                slice(x0 - self.x0, x1 - self.x0),
            )
            there = (
                slice(y0 - other.y0, y1 - other.y0),
                slice(x0 - other.x0, x1 - other.x0),
            )
            for name in _PAINT:
                getattr(self, name)[here][past] = getattr(other, name)[there][past]

    def put_back(self) -> None:
        """Put the stage's part of the canvas back on the canvas."""
        for name in _PAINT:
            getattr(self.on, name)[self._there] = getattr(self, name)[self._here]


class _Reach(NamedTuple):
    """A run of a knife stroke's steps that may lay paint past the edge of
    the canvas (see :class:`_Edge`)."""

    first: int  # the steps: the points of the path they end at
    last: int
    box: tuple[int, int, int, int]  # (y0, y1, x0, x1): all they can reach
    past: bool  # whether the window of any reaches past the edge


def _join(a, b):
    """The box that holds the boxes ``a`` and ``b`` (y0, y1, x0, x1)."""
    return (min(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), max(a[3], b[3]))


def _on_stage(box, H: int, W: int):
    """The part of ``box`` that a stage may hold: on the canvas (H by W)
    and no further than _STAGE_FAR px past its edges."""
    far = _STAGE_FAR
    return (
        max(box[0], -far),
        min(box[1], H + far),
        max(box[2], -far),
        min(box[3], W + far),
    )


def _area(box) -> int:
    return max(box[1] - box[0], 0) * max(box[3] - box[2], 0)


def _reaches(run: _Run) -> list[_Reach]:
    """The runs of steps of a knife's stroke that may lay paint past the
    edge of the canvas: those whose window, or what they lay outside it,
    is not all on the canvas. None for a stroke that stays clear of the
    edge. Two runs are taken as one, with the steps between them, where
    one stage for both is no larger than a stage for each."""
    canvas, pts = run.canvas, run.pts
    H, W = canvas.height, canvas.width
    # How far outside its window a step lays anything: its ridges (see
    # _engine._ridge_pads) and what its blade presses out at its ends, which
    # is smeared along the stroke over two steps (see _press_out).
    steps = np.linalg.norm(np.diff(pts, axis=0), axis=1) if len(pts) > 1 else [0.0]
    out = max(
        math.ceil(run.margin),
        eng.whole_ceil(_KNIFE_END_OUT + _KNIFE_END_PX + 2.0 * float(np.max(steps))) + 1,
    )
    # (the whole stroke clear of the edge, as most are: no step to look at)
    reach = run.pad + 1 + out
    if (
        math.floor(float(pts[:, 1].min()) - reach) >= 0
        and math.floor(float(pts[:, 0].min()) - reach) >= 0
        and math.ceil(float(pts[:, 1].max()) + reach) + 1 <= H
        and math.ceil(float(pts[:, 0].max()) + reach) + 1 <= W
    ):
        return []
    found: list[tuple[_Reach, tuple | None]] = []  # (with the box of the steps before)
    now, between = None, None
    for i in range(1, len(pts)):
        seg = run._segment(i)
        if seg is None:
            continue
        w = run._window(seg)
        box = (w.y0 - out, w.y1 + out, w.x0 - out, w.x1 + out)
        if box[0] >= 0 and box[2] >= 0 and box[1] <= H and box[3] <= W:
            if now is not None:
                found.append(now)
            now, between = None, box if between is None else _join(between, box)
            continue
        past = not (w.y0 >= 0 and w.x0 >= 0 and w.y1 <= H and w.x1 <= W)
        if now is None:
            now, between = (_Reach(i, i, box, past), between), None
        else:
            r = now[0]
            now = (_Reach(r.first, i, _join(r.box, box), r.past or past), now[1])
    if now is not None:
        found.append(now)
    runs: list[_Reach] = []
    for r, gap in found:
        if runs and gap is not None:
            a = runs[-1]
            both = _join(_join(a.box, gap), r.box)
            if _area(_on_stage(both, H, W)) <= _area(_on_stage(a.box, H, W)) + _area(
                _on_stage(r.box, H, W)
            ):
                runs[-1] = _Reach(a.first, r.last, both, a.past or r.past)
                continue
        runs.append(r)
    return runs


def _held(brush) -> np.ndarray:
    """The paint on a tool, channel by channel."""
    return (brush.tip.astype(np.float64) + brush.reservoir + brush.heel).sum(axis=0)


def _lying(top, und, part) -> np.ndarray:
    """The wet paint on the ``part`` (two slices) of a canvas's layers,
    channel by channel."""
    return top[part].sum(axis=(0, 1), dtype=np.float64) + und[part].sum(
        axis=(0, 1), dtype=np.float64
    )


class _Edge:
    """A knife's stroke at the edge of the canvas: which of its steps are
    painted on a stage (see :class:`_Stage`), and the count of the paint
    that crosses the edge.

    The stroke's steps that may lay paint past the edge come in runs (see
    :func:`_reaches`). A run with a step whose window reaches past the edge
    is painted on a stage that holds all the run can reach, on the canvas
    and up to _STAGE_FAR px past it; the other steps of the stroke are
    painted on the canvas itself, as ever, and so is all of a stroke whose
    windows stay on the canvas. So a stroke takes the memory of the parts
    of it that are near the edge, not of all of it. (One stage for a whole
    stroke took 0.25 KB for every pixel of the stroke's bounding box: a
    stroke across a canvas 4,000 px square that left over its edge, 4 GB.)
    The stages are made before the stroke's first step: what lies past the
    edge is the mirror image of the canvas as it was before the stroke, not
    of what the blade has just laid on its way to the edge.

    Over each run the canvas and the knife together lose what the run sends
    past the edge and gain what it brings on from there: that difference,
    channel by channel, is added to the canvas's ``edge_loss``, whatever
    the run is painted on (a stage; the canvas, where only a ridge or what
    a blade presses out at its end crosses the edge; nothing, for steps
    further out than a stage reaches, whose paint is used up). The steps of
    no run lose nothing: all they can reach is on the canvas."""

    def __init__(self, run: _Run):
        canvas: Any = run.canvas  # (a huile.Canvas: the stroke's own)
        self.canvas = canvas
        H, W = canvas.height, canvas.width
        self.runs = _reaches(run)
        self.stages: list[_Stage | None] = []
        for r in self.runs:
            y0, y1, x0, x1 = _on_stage(r.box, H, W)
            holds = r.past and max(y0, 0) < min(y1, H) and max(x0, 0) < min(x1, W)
            self.stages.append(_Stage(canvas, y0, y1, x0, x1) if holds else None)
        self.next = 0  # (the next run to come)
        self.on: int | None = None  # (the run the stroke is in)
        self._before = np.zeros(PACKED)
        self._home: tuple = ()

    def at(self, run: _Run, i: int) -> None:
        """The stroke comes to its step ``i``: leave the run it was in if
        that is over, and enter the one that begins."""
        if self.on is not None and i > self.runs[self.on].last:
            self.leave(run)
        ahead = self.runs[self.next].first if self.next < len(self.runs) else None
        if self.on is None and ahead is not None and i >= ahead:
            self._enter(run)

    def _part(self, canvas):
        """The part of the canvas the run the stroke is in can reach."""
        assert self.on is not None
        y0, y1, x0, x1 = self.runs[self.on].box
        H, W = canvas.height, canvas.width
        return (
            slice(max(y0, 0), max(min(y1, H), 0)),
            slice(max(x0, 0), max(min(x1, W), 0)),
        )

    def _enter(self, run: _Run) -> None:
        self.on, self.next = self.next, self.next + 1
        stage = self.stages[self.on]
        self._before = _held(run.brush)
        if stage is None:
            self._before += _lying(
                run.canvas.top, run.canvas.und, self._part(run.canvas)
            )
            return
        stage.take([s for s in self.stages[: self.on] if s is not None])
        self._before += _lying(stage.top, stage.und, stage._here)
        self._home = (run.canvas, run.blade, run.knife_off)
        blade = run.blade
        run.blade = _BladeStart(0, 0, stage.wet_before, blade.bands, blade.band_period)
        run.knife_off = stage.knife_off
        run.paint_on(stage, stage.x0, stage.y0)

    def leave(self, run: _Run) -> None:
        """The stroke leaves the run it is in, if any (and when it is
        over): what was painted on a stage goes back on the canvas, and
        what the canvas and the knife have lost over the run is counted."""
        if self.on is None:
            return
        stage = self.stages[self.on]
        after = _held(run.brush)
        if stage is None:
            after += _lying(run.canvas.top, run.canvas.und, self._part(run.canvas))
        else:
            after += _lying(stage.top, stage.und, stage._here)
            stage.put_back()
            stage.knife_off = run.knife_off
            canvas, run.blade, run.knife_off = self._home
            run.paint_on(canvas)
        self.canvas.edge_loss += self._before - after
        self.on = None


class _BladeStart(NamedTuple):
    """What a knife stroke starts from (see :func:`_before_the_blade`)."""

    wet_y0: int  # where wet_before lies on the canvas
    wet_x0: int
    wet_before: np.ndarray  # the wet paint there before the stroke
    bands: np.ndarray  # the bands the colours on the blade wander in
    band_period: float  # (px along the stroke)


def _before_the_blade(canvas, rng, pts, pad, w_typ, arc) -> _BladeStart:
    """What a knife stroke starts from: the wet paint lying on the canvas
    before it, which the blade's ends push aside into lips (a pile it is
    carrying mostly rides along), over the part of the canvas within ``pad``
    px of its path, from (wet_y0, wet_x0); and the bands its colours wander
    in (see :func:`_wandering_bands`) and their period along the stroke (px)."""
    H, W = canvas.height, canvas.width
    wet_y0 = min(max(math.floor(float(pts[:, 1].min()) - pad - 1), 0), H)
    wet_x0 = min(max(math.floor(float(pts[:, 0].min()) - pad - 1), 0), W)
    wet_y1 = max(math.ceil(float(pts[:, 1].max()) + pad + 1) + 1, wet_y0)
    wet_x1 = max(math.ceil(float(pts[:, 0].max()) + pad + 1) + 1, wet_x0)
    box = (slice(wet_y0, wet_y1), slice(wet_x0, wet_x1))
    wet_before = canvas.top_v[box] + canvas.und_v[box]
    # Paint on a blade isn't held in lanes like paint in bristles: its
    # colour bands wander a little from side to side along the stroke.
    period = max(0.5 * w_typ, 4.0)
    n_s = eng.whole_floor(arc[-1] / period) + 3
    bands = value_noise_2d(8 * n_s, 64, 8.0, rng)
    return _BladeStart(wet_y0, wet_x0, wet_before, bands, period)


def _wandering_bands(run: _Run, F, st, part: eng.Window):
    """Where across the blade (-1..1) the paint a knife lays on each pixel of
    the ``part`` (wy0, wx0, ch, cw) of the window of step ``st`` (footprint
    ``F``) comes from: paint on a blade isn't held in lanes, so its colour
    bands wander a little from side to side along the stroke."""
    blade = run.blade
    return eng.wandering_bands(
        F,
        part.wy0,
        part.wx0,
        part.ch,
        part.cw,
        float(run.arc[st.motion.i]),
        blade.band_period,
        blade.bands,
        _KNIFE_BAND_WANDER,
    )


def _all_of(win: eng.Window) -> eng.Window:
    """The window ``win``, all of it taken as its part on the canvas."""
    return eng.Window(
        x0=win.x0,
        y0=win.y0,
        hh=win.hh,
        ww=win.ww,
        cy0=win.y0,
        cx0=win.x0,
        ch=win.hh,
        cw=win.ww,
        wy0=0,
        wx0=0,
    )


def _knife_taps(run: _Run, st, F):
    """The bristle taps of a knife's step ``st`` (footprint ``F``) over its
    part of the canvas, and (None if that is all of its window) over all of
    its window, past the edge of the canvas too (see :func:`_whole_window`):
    worked out once over the window, and cropped to the canvas."""
    win = st.win
    ring = run.brush.ring
    if win.ch == win.hh and win.cw == win.ww:
        u = _wandering_bands(run, F, st, win)
        return eng.bristle_taps(u, st.hold.span, st.hold.nsub, ring, st.hold.rho), None
    u = _wandering_bands(run, F, st, _all_of(win))
    taps_all = eng.bristle_taps(u, st.hold.span, st.hold.nsub, ring, st.hold.rho)
    taps = eng.crop_taps(taps_all, win.ww, win.wy0, win.wx0, win.ch, win.cw)
    return taps, taps_all


def _knife_step(run: _Run, s: _Step) -> None:
    """One step of a knife, in stages that change the canvas in this order:
    the paint it pushes aside (4), the film it drags (5), the paint squeezed
    out beside it, the slab it lays and the paint it presses out at its ends
    (6), the peaks it pulls up as it lifts off, and the layers it folds
    together (7)."""
    st = s.st
    win = st.win
    area = max(run.area_unit * st.hold.r * st.hold.r, 1e-9)  # of the blade, px
    if win.ch == 0 or win.cw == 0:
        _knife_step_off(run, s, area)
        return
    # (how readily the paint takes stirring, as it lies before this step)
    _f_pick, _f_dep, f_mix, _f_drag = eng.surface_factors(run.cv, run.aux, win, run.K)
    # (The canvas, here and below: what the step is painted on. For the
    # steps of a stroke that reach past the edge of the canvas that is a
    # stage, the canvas going on past its edge, see _Stage and _Edge; a
    # step meets the stage's own edge only where it goes further out than
    # a stage may reach, _STAGE_FAR.)
    # Where the blade sticks out past the edge of the canvas, it goes on as
    # over a canvas going on as it is at its edge (see _engine.off_canvas):
    # it rests and rides on that, and lays its slab there from the paint on
    # it, which is gone. (Taking the step over the canvas alone, the paint
    # under the part past the edge stayed on the blade, and went down on the
    # visible part, a third to three quarters too much of it.) It drags no
    # wet paint out there, and none comes in from there: the flow under it
    # (5) has the canvas alone, and what it carries over the edge is gone.
    whole = _whole_window(run, s) if win.ch < win.hh or win.cw < win.ww else None
    flows = run.bt.clumps == 0  # (a comb's teeth cut the paint: they drag none)

    # 1) All the paint on a knife is on the blade, ready to go down; several
    #    paints loaded side by side blend slowly as it works. (A knife doesn't
    #    pick wet paint up as it goes: it drags it, step 5.)
    eng.work_load(run.br, run.K, st, np.inf)
    col_vol, _load, col_load, _col_body, body = eng.load_stats(
        run.brush.tip, run.brush.reservoir, st.hold.Wn
    )
    gap, hold = _blade_gap(run, st.hold.p)  # 2)
    if whole is None:
        film = _film(run, s, area)
        level, ride, hang, riding = _blade_riding(run, s, gap, film)  # 3)
    else:
        film_w = _film(run, whole.s, area)
        level_w, ride_w, hang_w, riding = _blade_riding(run, whole.s, gap, film_w)
        level = np.ascontiguousarray(level_w[s.wsl])
        ride = np.ascontiguousarray(ride_w[s.wsl])
        # (one array for a blade with no bead, as _blade_riding gives them)
        hang = level if hang_w is level_w else np.ascontiguousarray(hang_w[s.wsl])
        film = np.ascontiguousarray(film_w[s.wsl])
        riding = _on_canvas(riding, s.wsl)
        whole = whole._replace(level=level_w, ride=ride_w, hang=hang_w)
    ridges = _push_aside(run, s, level)  # 4)
    gaps = None  # (the gaps under the blade as it met them: see _drag_film)
    met = _drag_film(run, s, level, hang, film, riding) if flows else None  # 5)
    if met is not None:
        # (from here on the blade is where the step ends, at the level the
        # paint it has dragged there holds it at)
        gaps, level, hang = met
        if whole is not None:
            _ends_at(whole, s.wsl, level, hang)
    eng.squeeze_out(run.br, run.K, st, col_vol, col_load, hold, ridges, run.col_u)
    grid, c_tab, h_tab = s.tables
    eng.lay_ridges_off(
        run.cv,
        run.pend,
        run.br,
        run.K,
        st,
        ridges,
        grid,
        c_tab,
        h_tab,
        hair=_NO_TEX2,
        lose_off=True,
    )
    _fill_under_blade(run, s, level, ride, hang, area, whole, gaps)  # 6)
    # A knife lifted off thick paint pulls it up into little peaks and torn ridges.
    if run.eff["lift"] > 0 and st.motion.i == len(run.pts) - 1:
        _lift_blade(run, s, body)
    _fold_layers(run, s, level, f_mix)  # 7)


def _blade_gap(run: _Run, p: float) -> tuple[float, float]:
    """2) The blade rides above the surface at a gap set by pressure ``p``
    (all its paint is a film under it; what doesn't fit under it rides along
    on it). Returns the gap and how much paint the blade holds (load units)."""
    bt = run.bt
    gap = _KNIFE_GAP * (1.0 - p) ** 1.6 * (0.55 + 0.45 * bt.stiffness) + 0.05
    if bt.clumps > 0:  # the teeth of a comb dig in, down to the threads
        gap *= 0.03
    return gap, gap * run.area_unit / 4.0 + _KNIFE_CARRY


def _film(run: _Run, s: _Step, area: float):
    """How thick the film of paint on the blade is over each pixel, from the
    paint on it as it stands now: where the blade rides (3) and what it
    fills (6) each read it, before and after it has spread and squeezed
    some out."""
    brush, st = run.brush, s.st
    return (
        eng.at_pixels(
            s.taps, brush.tip[:, IV] + brush.reservoir[:, IV], st.win.ch, st.win.cw
        )
        * COLUMNS
        / area
    )


def _blade_rest(run: _Run, s: _Step) -> tuple[np.ndarray, eng.Riding | None]:
    """3) Where the blade sits: on the high points of the surface below
    (thread tops for a flexible blade, the highest ridges around for a stiff
    one). (Worked out pixel by pixel by _engine.blade_rest, blade_bins and
    blade_sink.) Returns that and, if it rides on wet paint of earlier
    strokes, what that was worked out from (an _engine.Riding: the flow
    under the blade works it out again as the blade goes, see
    :func:`_drag_film`), else None."""
    canvas, bt, st, relief = run.canvas, run.bt, s.st, run.relief
    win = st.win
    rest, old_v, vmax, under_blade, any_under, top_ib, und_ib = eng.blade_rest(
        canvas.top,
        canvas.und,
        canvas.top_id,
        relief.peaks_fine,
        relief.peaks_wide,
        win.cy0,
        win.cx0,
        win.ch,
        win.cw,
        run.stroke_id,
        run.stiff_blade,
        s.F,
        win.wy0,
        win.wx0,
        gathered=s.sl is None,
    )
    # Wet paint from earlier strokes holds the blade up too, the heap it pushes
    # included (a knife rides on a wave of paint): it rests on its high points
    # and sinks in the harder it is pressed (less into stiff paint). A light
    # touch lays new paint on top of the old.
    if not (vmax > 0.05 and any_under):
        return rest.astype(np.float64), None
    # (summed by numpy, and summed as numpy always summed it: on the canvas
    # over the strided view of the canvas itself, row by row, which rounds
    # differently from a contiguous copy of the same pixels; past the edge
    # over the gathered copy)
    if s.sl is not None:
        und_ib = canvas.und[..., IB][s.sl]
    old_body = float((und_ib.sum() + top_ib.sum()) / max(float(old_v.sum()), 1e-9))
    # How far into it the blade sinks, as a share of its thickness: a light
    # touch skims, a firm one cuts in, pressing hard goes nearly down to the
    # canvas, however thick the paint. Stiff paint resists a little.
    depth = min(
        max(st.hold.p**_KNIFE_SINK * (1.15 - 0.3 * min(old_body, 1.0)), 0.0), 1.0
    )
    # narrow teeth concentrate the pressure: they cut right through
    if bt.clumps > 0:
        depth = max(depth, 0.9)
    # The blade is rigid along the direction it moves: its height varies only
    # along its length. It rests on the high points under it (not on the pile
    # it pushes ahead), bending to follow them over a span set by its
    # stiffness: what lies under it at each position along it (whole px from
    # its end), averaged over ``span`` px either way.
    span = eng.whole_floor(min(max(0.1 * run.w_typ * (0.5 + run.stiff_blade), 2), 10))
    hi, b, cnt, tot_hi, tot_rest = eng.blade_bins(
        relief.floor,
        win.cy0,
        win.cx0,
        old_v,
        rest,
        under_blade,
        s.F,
        win.wy0,
        win.wx0,
    )
    kernel = np.ones(2 * span + 1)
    sunk = eng.blade_sink(
        rest,
        hi,
        b,
        np.convolve(cnt, kernel, mode="same"),
        np.convolve(tot_hi, kernel, mode="same"),
        np.convolve(tot_rest, kernel, mode="same"),
        depth,
    )
    return sunk, eng.Riding(rest=rest, sunk=sunk, bins=b, depth=depth, span=span)


def _on_canvas(riding: eng.Riding | None, wsl) -> eng.Riding | None:
    """``riding`` (see :func:`_blade_rest`), worked out over all of a step's
    window, over its part ``wsl`` on the canvas."""
    if riding is None:
        return None
    return riding._replace(
        rest=np.ascontiguousarray(riding.rest[wsl]),
        sunk=np.ascontiguousarray(riding.sunk[wsl]),
        bins=np.ascontiguousarray(riding.bins[wsl]),
    )


def _nearest(run: _Run, win: eng.Window):
    """The pixels of the canvas the step's part of it (``win``: cy0, cx0, ch,
    cw) lies at; past its edge (see :func:`_whole_window`), the nearest ones
    (to index a plane of the canvas with)."""
    H, W = run.canvas.height, run.canvas.width
    return np.ix_(
        np.clip(np.arange(win.cy0, win.cy0 + win.ch), 0, H - 1),
        np.clip(np.arange(win.cx0, win.cx0 + win.cw), 0, W - 1),
    )


def _blade_level(run: _Run, s: _Step, gap: float, film):
    """3) How high the blade's edge rides over each pixel: on what it rests
    on (:func:`_blade_rest`), at ``gap``, less as the paint under it runs low
    (``film``, see :func:`_film`). Returns the level, how high it rides on
    the paint (see _engine.blade_level), and the level the bead on its edge
    hangs from if it skims (see :func:`_slab`; the level if it doesn't)."""
    return _blade_riding(run, s, gap, film)[:3]


def _blade_riding(run: _Run, s: _Step, gap: float, film):
    """:func:`_blade_level`, and what the blade rides on if that is wet
    paint of earlier strokes (see :func:`_blade_rest`), else None."""
    st = s.st
    # The blade rides on the paint under it: as that runs low, it sinks and the
    # slab thins out (not a comb's teeth). Nicks and grit on its edge leave
    # fine scratches along the stroke; it wavers as it is pushed (chatter) and
    # is never pressed quite evenly along its length (tilt).
    # (skimming, the blade glides: no chatter; its nicks still streak the paint)
    skim = eng.smoothstep(_KNIFE_SKIM, 0.05, st.hold.p)
    rest, riding = _blade_rest(run, s)
    comb = run.bt.clumps > 0

    def riding_on(paint):
        return eng.blade_level(
            rest,
            paint,
            _KNIFE_FILM,
            gap,
            comb=comb,
            chat=1.0 + 0.25 * (1.0 - skim) * run.chatter[st.motion.i],
            tilt=run.blade_tilt,
            F=s.F,
            wy0=st.win.wy0,
            wx0=st.win.wx0,
        )

    level, ride = riding_on(film)
    if not (skim > 0 and not comb):
        return level, ride, level, riding
    # Skimming, the blade isn't spreading its film: what reaches down from it
    # is the bead on its edge, which touches the high points it glides over
    # however much paint the blade carries. Its bead hangs from the blade as
    # it would ride on no more paint than the bead (the same level where the
    # film is no taller than that). (Hanging from the level the whole film
    # holds the blade up at, a bead on a blade carrying more than twice its
    # height of paint was lifted off the surface: the more paint on the
    # blade, the less it laid, and loaded with a few times that, nothing at
    # all: murex-iaa.)
    hang, _ = riding_on(np.minimum(film, _KNIFE_BEAD_HEIGHT))
    return level, ride, hang, riding


def _push_aside(run: _Run, s: _Step, level):
    """4) Wet paint standing above the blade is bulldozed ahead by the flow
    (5); near the edges of the mark, some of the paint that was lying there
    spills out sideways (lips; the pile the blade carries rides along with
    it). Nicks and flex let streaks of it slip under the blade and stay. A
    comb's teeth push what they cut into ridges between them. Returns the
    paint spilt to each side of the blade, as :func:`_engine.squeeze_out`
    adds to it (a Ridges)."""
    canvas, st = run.canvas, s.st
    win = st.win
    wsl = s.wsl
    hair, expo_c = s.hair[wsl], s.expo[wsl]
    ridges = eng.Ridges(np.zeros(PACKED), np.zeros(PACKED), np.zeros(PACKED))
    flowing = run.bt.clumps == 0
    # (what was lying there before the stroke; a comb: none spills)
    wet = _wet_before(run, win) if flowing else np.zeros((0, 0), np.float32)
    # (what stands above the blade, the share of it a pass moves, and near
    # the edges of the mark what spills: see _engine.blade_excess)
    excess, tv, emax = eng.blade_excess(
        canvas.top,
        canvas.und,
        run.relief.floor,
        win.cy0,
        win.cx0,
        level,
        1.0 - np.exp(-4.0 * expo_c * (0.15 + 1.7 * hair**2)),
        s.F,
        win.wy0,
        win.wx0,
        max(st.hold.r * st.hold.lmax, 1e-6),  # the mark's half-width, px
        _KNIFE_SPILL_PX,
        _KNIFE_SPILL,
        wet,
    )
    if emax > 1e-3:
        moved = eng.take(canvas.top, canvas.und, win.cy0, win.cx0, excess, tv)
        if flowing:
            eng.add_sides(ridges, moved, np.ascontiguousarray(s.lat_px[wsl]), 1.0)
        else:
            fresh = (
                s.between
                * smoothstep(-st.motion.ds - 1.0, 0.0, s.along - s.c)
                * smoothstep(1.0, -1.0, s.along - s.c - s.h)
            )[wsl]
            eng.spread(
                cv=run.cv,
                pend=run.pend,
                br=run.br,
                sy0=win.cy0,
                sx0=win.cx0,
                w=fresh,
                pk=moved.sum(axis=(0, 1)),
                cover=np.zeros(fresh.shape),
                stroke_id=run.stroke_id,
                by_film=False,
            )
    return ridges


def _drag_film(run: _Run, s: _Step, level, hang, film, riding=None):
    """5) The blade drags the wet paint it touches, as a thin-film flow:
    between the moving blade and the still canvas the paint shears, so paint
    near the blade travels almost with it and paint at the canvas hardly
    moves; what stands above the blade is bulldozed ahead of it. Each wet
    layer moves at its own speed, so their order is kept (white dragged over
    purple stays on top). The blade glides on its own fresh paint: under
    that it drags nothing, and pushes on only what is in its way, the paint
    it has brought there and what stands above it (see
    _engine.pushed_under_film; it left that where its own paint began, in a
    heap: murex-6fa).

    The paint it drags travels under it, so the gap left under the blade for
    its own paint changes as it goes; and where the blade rides on that
    paint (``riding``, see :func:`_blade_rest`), so does how high it rides:
    its level is worked out again as it goes, from the paint under where it
    is then (see _engine.flow_under_riding_blade; ``level`` and ``hang`` are
    read from the paint under where the step takes it, which the wave it
    pushes has not reached yet). Returns, for :func:`_slab`, what the blade
    met over each pixel as it went (see _engine.flow_under_blade and
    flow_under_riding_blade): the gap its ``film``, the one it rides on (3),
    could fill under its level, and the surface as the bead hanging from
    ``hang`` found it, as far down as the bead reaches; and its level and
    the level its bead hangs from where it ends the step. None if it dragged
    nothing: the gap and the surface are then those the canvas shows, and
    the levels those of the step."""
    st, wsl = s.st, s.wsl
    hair = s.hair[wsl]
    # (planes passed as arrays of their own: one compiled kernel, whether
    # the step's window is all on the canvas or not)
    flow = (
        run.cv,
        st.win.cy0,
        st.win.cx0,
        run.stroke_id,
        np.ascontiguousarray(run.relief.floor[s.sl]),
        level,
        np.ascontiguousarray(s.aa[wsl]),
        np.ascontiguousarray(s.along[wsl]),
        np.ascontiguousarray(s.c[wsl]),
        np.ascontiguousarray(s.h[wsl]),
        st.motion.ds,
        st.motion.tx,
        st.motion.ty,
        np.clip((0.5 + 0.45 * st.hold.p) * (0.6 + 0.8 * hair), 0.0, 1.0),
        _VISCOUS,
        film,
        # (the bead finds the surface under the stroke's own paint, see
        # _slab: hanging from a level raised by that paint, it finds the
        # paint's surface as far below it as the one under it)
        hang + _own_paint(run, s),
        np.minimum(film, _KNIFE_BEAD_HEIGHT),  # (the bead: see _slab)
        _wet_before(run, st.win),
    )
    if riding is None:  # (on the solid surface alone: its level stays)
        gaps = eng.flow_under_blade(*flow)
    else:
        gaps, ends = eng.flow_under_riding_blade(*flow, riding)
        # (the level the bead hangs from moves with the blade's; the flow
        # was given it raised by the stroke's own paint, _slab is not. A
        # blade that does not skim has no bead: its level is given for it,
        # see _blade_riding, and stays so.)
        hang = ends if hang is level else hang + (ends - level)
        level = ends
    return _Met(gaps, level, hang) if gaps.size else None


def _wet_before(run: _Run, win: eng.Window):
    """How thick the wet paint lay on the step's part of the canvas (``win``:
    cy0, cx0, ch, cw) before the stroke (see :func:`_before_the_blade`)."""
    blade = run.blade
    return np.ascontiguousarray(
        blade.wet_before[
            win.cy0 - blade.wet_y0 : win.cy0 - blade.wet_y0 + win.ch,
            win.cx0 - blade.wet_x0 : win.cx0 - blade.wet_x0 + win.cw,
        ]
    )


class _Met(NamedTuple):
    """What a blade met as it dragged the wet paint under it along, and how
    high it ends the step (see :func:`_drag_film`)."""

    gaps: np.ndarray
    level: np.ndarray
    hang: np.ndarray


def _own_paint(run: _Run, s: _Step, surf_add=None):
    """The stroke's own paint over each pixel of the step's part of the
    canvas (past its edge, see :func:`_whole_window`, the slab it laid out
    there: the nearest canvas pixel's, plus ``surf_add``)."""
    canvas = run.canvas
    at = _nearest(run, s.st.win)
    own = np.where(canvas.top_id[at] == run.stroke_id, canvas.top[..., IV][at], 0.0)
    return own if surf_add is None else own + surf_add


def _fill_under_blade(
    run: _Run, s: _Step, level, ride, hang, area: float, whole, gaps=None
) -> None:
    """6) The blade fills the space under it, up to its ``level``, from the
    film of paint it carries (its bead hanging from ``hang`` if it skims: see
    :func:`_slab`), and presses some out at its ends
    (:func:`_press_out_ends`). If that makes three wet layers, the
    two most alike merge (white laid on white-over-purple joins the white; a
    new colour stays on top of the others). With ``whole`` (see
    :func:`_whole_window`), the blade also fills under its part past the edge
    of the canvas, from the paint on it, which is gone. ``gaps``: the space
    under it over its part of the canvas as it met it, where it dragged the
    wet paint there along (see :func:`_drag_film`)."""
    if not (run.brush.tip[:, IV].sum() > 0 and run.bt.deposits):
        return
    st, wsl = s.st, s.wsl
    if whole is None:
        d, skim = _slab(run, s, level, hang, area, gaps=gaps)
        extra = np.empty(0)
    else:
        if gaps is not None:  # (past the edge of the canvas it dragged nothing)
            # (below 0, or over no sub-step: see _engine.blade_slab)
            none = -1.0 if gaps.shape[2] == 2 else 0.0
            gaps_w = np.full((*whole.level.shape, gaps.shape[2]), none)
            gaps_w[wsl] = gaps
            gaps = gaps_w
        d_w, skim = _slab(
            run, whole.s, whole.level, whole.hang, area, whole.surf_add, gaps=gaps
        )
        d = np.ascontiguousarray(d_w[wsl])
        d_off = d_w.copy()
        d_off[wsl] = 0.0  # (on the canvas: d)
        extra = eng.column_demand(whole.s.taps, d_off)
        _lay_off(run, st.win, d_off)
    if run.bt.clumps == 0:
        _press_out_ends(run, s, ride, skim)
        if whole is not None:
            _press_out_past_edge(run, whole, skim)
    eng.lay_off(
        run.cv,
        run.pend,
        run.br,
        s.taps,
        st.win.cy0,
        st.win.cx0,
        d,
        np.ascontiguousarray(s.cover[wsl]),
        run.stroke_id,
        moved=True,
        by_film=False,
        reach=np.ascontiguousarray(s.expo[wsl]),
        has_reach=False,
        extra=extra,
    )


class _Whole(NamedTuple):
    """A step of a knife over the whole of its window (see
    :func:`_whole_window`)."""

    s: _Step  # the step, its part of the canvas all of the window
    step: _Step  # the step as it is (its part on the canvas: step.wsl of the window)
    surf_add: np.ndarray  # what to add to the surface read off the canvas
    level: np.ndarray | None = None  # how high the blade rides (see _blade_level)
    ride: np.ndarray | None = None
    hang: np.ndarray | None = None


def _ends_at(whole: _Whole, wsl, level, hang) -> None:
    """Over its part ``wsl`` on the canvas, the blade of ``whole`` ends the
    step at ``level``, its bead hanging from ``hang`` (see
    :func:`_drag_film`; past the edge of the canvas, where it drags nothing,
    they stay the step's)."""
    assert whole.level is not None and whole.hang is not None
    whole.level[wsl] = level
    if whole.hang is not whole.level:  # (one array for a blade with no bead)
        whole.hang[wsl] = hang


def _whole_window(run: _Run, s: _Step) -> _Whole:
    """The step ``s`` over the whole of its window, past the edge of the
    canvas too, where the canvas is taken to go on as it is at its edge:
    as a step whose part of the canvas is all of it (its pixels read from
    the nearest canvas pixel, see :func:`_nearest`)."""
    st = s.st
    win = st.win
    st_w = eng.Step(win=_all_of(win), motion=st.motion, hold=st.hold)
    # (its pixels gathered: see _nearest)
    sw = _Step(st_w, s.F, s.tables, s.taps_all, gathered=True)
    # Past the edge, the surface is the canvas's at its edge, with the slab
    # this stroke has laid out there in place of the one it laid at the edge
    # (a blade fills up to its level: over its own slab it lays no more).
    canvas = run.canvas
    surf_add = eng.off_surface(
        canvas.top,
        canvas.top_id,
        run.stroke_id,
        st.win.y0,
        st.win.x0,
        _laid_off(run, st.win),
        st.win.wy0,
        st.win.wx0,
        st.win.ch,
        st.win.cw,
    )
    return _Whole(sw, s, surf_add)


# Side (px) of the tiles in which the slab a knife lays past the edge of the
# canvas is kept (see _laid_off).
_OFF_TILE = 32


def _laid_off(run: _Run, win: eng.Window):
    """The slab the stroke has laid past the edge of the canvas, over the
    window ``win`` of a step. (Kept in tiles of _OFF_TILE px, only where it has
    laid any: what a long stroke keeps grows with the off-canvas stretch the
    blade passed over, not with the stroke's bounding box.)"""
    tiles = run.knife_off
    out = np.zeros((win.hh, win.ww))
    if not tiles:
        return out
    T = _OFF_TILE
    for ty in range(win.y0 // T, (win.y0 + win.hh - 1) // T + 1):
        for tx in range(win.x0 // T, (win.x0 + win.ww - 1) // T + 1):
            tile = tiles.get((ty, tx))
            if tile is None:
                continue
            y0, x0 = max(ty * T, win.y0), max(tx * T, win.x0)
            y1 = min((ty + 1) * T, win.y0 + win.hh)
            x1 = min((tx + 1) * T, win.x0 + win.ww)
            out[y0 - win.y0 : y1 - win.y0, x0 - win.x0 : x1 - win.x0] = tile[
                y0 - ty * T : y1 - ty * T, x0 - tx * T : x1 - tx * T
            ]
    return out


def _lay_off(run: _Run, win: eng.Window, d) -> None:
    """Record the slab ``d`` laid over the window ``win`` of a step past the
    edge of the canvas (zero on the canvas; see :func:`_laid_off`)."""
    if run.knife_off is None:
        run.knife_off = {}
    tiles = run.knife_off
    T = _OFF_TILE
    for ty in range(win.y0 // T, (win.y0 + win.hh - 1) // T + 1):
        for tx in range(win.x0 // T, (win.x0 + win.ww - 1) // T + 1):
            y0, x0 = max(ty * T, win.y0), max(tx * T, win.x0)
            y1 = min((ty + 1) * T, win.y0 + win.hh)
            x1 = min((tx + 1) * T, win.x0 + win.ww)
            part = d[y0 - win.y0 : y1 - win.y0, x0 - win.x0 : x1 - win.x0]
            if not part.any():
                continue
            tile = tiles.get((ty, tx))
            if tile is None:
                tile = tiles[ty, tx] = np.zeros((T, T), np.float32)
            tile[y0 - ty * T : y1 - ty * T, x0 - tx * T : x1 - tx * T] += part


def _press_out_past_edge(run: _Run, whole: _Whole, skim: float) -> None:
    """The paint the blade presses out at an end past the edge of the
    canvas (see :func:`_press_out_ends`) is gone."""
    sw, on = whole.s, whole.step.st
    d_end = _end_press(whole.ride, sw, skim, on.win)
    if d_end.max() > 1e-6:
        eng.take_tips(run.brush.tip, sw.taps, d_end)


def _end_press(ride, s: _Step, skim: float, on: eng.Window | None = None):
    """How much paint the blade presses out near its ends over each pixel of
    the step's part of the canvas (see :func:`_press_out_ends`), none over
    the part on the canvas of the window ``on`` (ch by cw px at wy0, wx0; see
    _engine.blade_ends)."""
    st = s.st
    oy, ox, oh, ow = (0, 0, 0, 0) if on is None else (on.wy0, on.wx0, on.ch, on.cw)
    # (skimming, the blade spreads no film to press out; it takes a slab
    # of some thickness to stand in a bead)
    # (as much as the slab is thick, over each step's share of a pass:
    # not what this step filled, which wavers from step to step with
    # the blade's chatter and would come out as a bead at every step)
    return eng.blade_ends(
        ride,
        s.F,
        st.win.wy0,
        st.win.wx0,
        max(st.hold.r * st.hold.lmax, 1e-6),
        _KNIFE_END_PX,
        _KNIFE_END * (0.8 + st.hold.p) * (1.0 - skim),
        oy,
        ox,
        oh,
        ow,
    )


def _knife_step_off(run: _Run, s: _Step, area: float) -> None:
    """A step of a knife wholly off the canvas: it goes on as over a canvas
    going on as it is at its edge (see :func:`_whole_window`), and the paint
    it lays and squeezes out there is gone."""
    st = s.st
    eng.work_load(run.br, run.K, st, np.inf)
    col_vol, _load, col_load, _col_body, _body = eng.load_stats(
        run.brush.tip, run.brush.reservoir, st.hold.Wn
    )
    gap, hold = _blade_gap(run, st.hold.p)
    ridges = eng.Ridges(np.zeros(PACKED), np.zeros(PACKED), np.zeros(PACKED))
    eng.squeeze_out(run.br, run.K, st, col_vol, col_load, hold, ridges, run.col_u)
    if not (run.brush.tip[:, IV].sum() > 0 and run.bt.deposits):
        return
    whole = _whole_window(run, s)
    # (nothing changes the paint on the blade between where it rides and what
    # it fills: the same film)
    film = _film(run, whole.s, area)
    level_w, ride_w, hang_w = _blade_level(run, whole.s, gap, film)
    whole = whole._replace(level=level_w, ride=ride_w, hang=hang_w)
    d_w, skim = _slab(run, whole.s, level_w, hang_w, area, whole.surf_add, film)
    if run.bt.clumps == 0:
        _press_out_past_edge(run, whole, skim)
    extra = eng.column_demand(whole.s.taps, d_w)
    _lay_off(run, st.win, d_w)
    empty = np.zeros((0, 0))
    eng.lay_off(
        run.cv,
        run.pend,
        run.br,
        s.taps,
        0,
        0,
        empty,
        empty,
        run.stroke_id,
        moved=True,
        by_film=False,
        reach=empty,
        has_reach=False,
        extra=extra,
    )


def _slab(
    run: _Run, s: _Step, level, hang, area: float, surf_add=None, film=None, gaps=None
):
    """How much paint the blade lays under it over each pixel this step (see
    :func:`_fill_under_blade`): with plenty of paint, a smooth slab; running
    low, it only reaches the high points (broken colour). Barely touching,
    the blade isn't spreading a film any more: only the bead of paint on its
    edge reaches down (from ``hang``, see :func:`_blade_level`), and it
    touches the high points of the surface (thread tops, ridges of paint)
    and leaves paint on them, nothing in the hollows: broken colour ("let it
    break"). Returns that, and how much the blade skims (0: not at all)."""
    canvas, st = run.canvas, s.st
    p, wsl = st.hold.p, s.wsl
    hair, expo_c = s.hair[wsl], s.expo[wsl]
    if film is None:  # (the paint on the blade as it is now: see _film)
        film = _film(run, s, area)
    # Barely touching, the blade skims: it fills less of the gap under it.
    skim = eng.smoothstep(_KNIFE_SKIM, 0.05, p)
    # Each step fills the share of the gap left that it passes over: as the
    # gap shrinks step by step, how full a pixel ends up depends only on
    # how much of a full pass went over it, not on how the stroke is cut
    # into steps. (Filling a fixed share of each step's fill instead, as a
    # skimming blade did, a pixel passed over in two steps got more than
    # one passed over in one: a sawtooth along a pointed or rounded blade
    # end, where the blade is shorter along the stroke than a step.) How
    # much a skimming blade fills, and how much its bead leaves, over a
    # whole pass depends on how long the blade is along the stroke, the
    # same on a curve or a pointed end (n: that length in _KNIFE_SKIM_PX,
    # not in the stroke's nominal steps, as it was: then the shorter a
    # stroke's steps, the more a skimming blade laid, half as much again
    # in steps of 2 px rather than 8; murex-86z).
    n = 1.0
    if skim > 0:
        n = np.maximum(0.4 + 2.0 * s.h[wsl] / _KNIFE_SKIM_PX, 1.0)
        per_step = 1.0 - (1.0 - skim) * (1.0 - np.exp(-4.0 / n))
        k_fill = -n * np.log(np.maximum(per_step, 1e-12))
    else:  # (the same: per_step is e^(-4/n))
        k_fill = 4.0
    # The gap between the blade and the surface (past the edge of the canvas,
    # plus surf_add: see _whole_window), as far as its film reaches, filled
    # by the share k_fill gives over this step's share of a pass (see
    # _engine.blade_slab). Where the blade dragged the wet paint under it
    # along in this step, the gap, and the surface, as it met them (gaps:
    # see _drag_film).
    d, surf = eng.blade_slab(
        canvas.top,
        canvas.und,
        run.relief.floor,
        st.win.cy0,
        st.win.cx0,
        level,
        np.zeros((0, 0)) if surf_add is None else surf_add,
        film,
        1.0 - np.exp(-k_fill * expo_c),
        np.zeros((0, 0, 2)) if gaps is None else gaps,
    )
    if skim > 0 and run.bt.clumps == 0:
        bead = np.minimum(film, _KNIFE_BEAD_HEIGHT)
        # The bead runs along the blade's edge: it passes over a pixel once
        # in a pass, and touches what was there before the stroke, as the
        # blade rests on it (see _blade_rest), not the paint it has just
        # left there. (Touching that too, it caught the more the more it
        # had laid, and laid the more the more steps the pass was cut
        # into: a tenth more in steps of 2 px rather than 8; murex-86z.)
        surf = surf - _own_paint(run, s, surf_add)
        touch = np.clip((surf - (hang - bead)) / np.maximum(bead, 1e-6), 0.0, 1.0)
        # the bead is uneven and the paint below still follows the threads
        # of the canvas: barely touching, it catches in streaks along the
        # blade's nicks and on the thread tops, the fewer the lighter the touch
        grain = 0.55 * hair + 0.45 * run.relief.tooth[_nearest(run, st.win)]
        thr = _KNIFE_TOUCH - 2.2 * p
        touch = touch * smoothstep(thr - 0.1, thr + 0.1, grain)
        # the bead leaves paint wherever it passes, in proportion to how
        # much of a pass this step is (for the same reason)
        pass_bead = n * (1.0 - np.exp(-4.0 / n))
        d += skim * _KNIFE_BEAD * pass_bead * bead * touch**0.7 * expo_c
    return d, skim


def _press_out_ends(run: _Run, s: _Step, ride, skim: float) -> None:
    """Near its two ends the blade presses paint out sideways, more the
    harder it is pressed: it stands in a bead on the edge of the slab and
    beyond each end of the blade (see :func:`_press_out`)."""
    st, wsl = s.st, s.wsl
    d_end = _end_press(ride, s, skim)
    if d_end.max() > 1e-6:
        _press_out(run, st, s.taps, s.lat_px[wsl], s.along[wsl], d_end)


def _lift_blade(run: _Run, s: _Step, body: float) -> None:
    """A knife lifted off thick paint (at the last step) pulls it up into
    little peaks and torn ridges, the stiffer the paint on it (``body``)
    the more (see :func:`_lift_off`)."""
    st, wsl = s.st, s.wsl
    under = (s.aa * np.clip((s.h - np.abs(s.rel)) / 1.5, 0.0, 1.0))[wsl]
    # most along the trailing edge, the last of the blade to leave the paint
    under = under * (0.3 + 0.7 * smoothstep(0.3, -0.5, (s.rel / s.h)[wsl]))
    _lift_off(
        run.canvas,
        s.sl,
        under,
        run.eff["lift"] * (0.5 + 0.8 * body),
        max(2.5, 0.08 * st.hold.Wd),
        np.degrees(np.arctan2(st.motion.ty, st.motion.tx)),
        run.rng,
        run.stroke_id,
    )


def _fold_layers(run: _Run, s: _Step, level, f_mix) -> None:
    """7) A blade only shears the paint it cuts through: riding within the
    top layer it leaves the one below alone; cutting into it, it folds the
    two into each other in streaks (marbling), not evenly."""
    st, wsl = s.st, s.wsl
    win = st.win
    p = st.hold.p
    expo_c = s.expo[wsl]
    m = 1.0 - np.exp(-run.eff["mixing"] * 3.0 * p * p * expo_c * s.streak[wsl] * f_mix)
    # (in streaks along its nicks, as far as it cuts into the layer below:
    # see _engine.blade_folds)
    m = eng.blade_folds(
        run.canvas.und,
        run.relief.floor,
        win.cy0,
        win.cx0,
        level,
        m,
        s.F,
        win.wy0,
        win.wx0,
    )
    eng.stir(run.cv, win.cy0, win.cx0, m)


# ----------------------------------------------------------------------------
# helpers


def _press_out(run: _Run, st, taps, lat, along_px, d_end) -> None:
    """Paint pressed out at a blade's ends: ``d_end`` per pixel near each end
    (over the step's part of the canvas) moves out past the end of the blade
    to within _KNIFE_END_OUT px past the end of the blade, as it was spread (so
    it is as even along the stroke as the slab itself), smeared along the
    stroke over two steps (the paint escaping at the end of the blade runs
    together into one bead, whatever was laid in which step), and stands
    there in a bead against the slab's edge. (Landing from where it was
    spread to just beyond the end of the blade: on what the blade has filled,
    it would change what later steps fill.)"""
    win = st.win
    H, W = run.canvas.height, run.canvas.width
    m = eng.whole_ceil(_KNIFE_END_OUT + _KNIFE_END_PX + 2.0 * st.motion.ds) + 1
    y0, x0 = max(win.cy0 - m, 0), max(win.cx0 - m, 0)
    y1, x1 = min(win.cy0 + win.ch + m, H), min(win.cx0 + win.cw + m, W)
    wl, wr = eng.splat_out(
        d_end,
        np.ascontiguousarray(lat),
        np.ascontiguousarray(along_px),
        win.cy0 - y0,
        win.cx0 - x0,
        y1 - y0,
        x1 - x0,
        st.motion.tx,
        st.motion.ty,
        st.motion.ds,
        st.motion.arc_i,
        run.K.arc_end,
        max(st.hold.r * st.hold.lmax, 1e-6),
        _KNIFE_END_OUT,
    )
    # (each side's share of each pixel's paint, as splat_out shares it: a
    # pixel centred on the axis, which a blade narrower than its ends' bead
    # presses out at too, half each; it went to neither)
    right = np.where(lat > eng.ROUND_PX, 1.0, np.where(lat < -eng.ROUND_PX, 0.0, 0.5))
    for share, w in ((1.0 - right, wl), (right, wr)):
        src = share * d_end
        if not src.max() > 1e-9:
            continue
        pk = eng.take_tips(run.brush.tip, taps, src)
        eng.spread(
            cv=run.cv,
            pend=run.pend,
            br=run.br,
            sy0=y0,
            sx0=x0,
            w=w,
            pk=pk,
            cover=smoothstep(0.1, 0.6, w),
            stroke_id=run.stroke_id,
            by_film=False,
        )


# How far (in crest cells) the paint pulled up into a knife's crests comes
# from: the spread (as a Gaussian's sigma) of the square window, about 1.7
# times this each way, over which _engine.pull_up moves paint to a rising
# pixel. Crests lie about a cell apart across the pull, so over a knife's
# lift 81% to 96% of the paint moved comes from beside the crest it goes
# to; the rest is shared among all the pixels that rise.
KNIFE_PULL = 1.0


def _lift_off(canvas, sl, under, amp, cell, direction, rng, stroke_id):
    """The stroke's own paint under a tool lifted off it is pulled up into
    torn crests and peaks, stretched along the way the tool was moving: the
    crests are made of the paint between them, which falls (see
    _engine.pull_up), so nothing is made or lost, pigment by pigment; other
    strokes' paint is left as it is."""
    if amp <= 0 or not under.any():
        return
    top = canvas.top[sl]
    own = canvas.top_id[sl] == stroke_id
    V = np.where(own, top[..., IV], 0.0).astype(np.float64)
    wv = under * V
    if wv.sum() <= 1e-9:
        return
    hh, ww = under.shape
    n = aniso_noise(hh, ww, 6.0 * cell, cell, direction, rng, octaves=2)
    n = (n - n.min()) / max(np.ptp(n), 1e-9)
    crest = (1.0 - np.abs(2.0 * n - 1.0)) ** 2
    m = (wv * crest).sum() / wv.sum()
    fac = np.clip(1.0 + 2.0 * amp * under * (crest - m), 0.05, None)
    fac *= V.sum() / max((V * fac).sum(), 1e-12)
    fac = np.where(own, fac, 1.0)  # (1: left alone)
    eng.pull_up(top, fac, KNIFE_PULL * cell)

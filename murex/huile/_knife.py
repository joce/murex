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
# Wet paint of earlier strokes holds a blade up where it lies thicker than
# this somewhere under it (paint thickness units; see _blade_rest): thinner,
# it is a trace the blade goes through, and the blade rests on the solid
# surface. (Far above rounding dust, _engine.EMPTY; a third of the thinnest
# film that holds together, _engine.MIN_FILM, and a fourteenth of the weave
# of a canvas, canvas.WEAVE_DEPTH.)
_KNIFE_RIDES_ON = 0.05
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
# How much the bead leaves by how hard it is pressed against the surface (0
# clear of it, 1 flat against it): that to this power.
_KNIFE_CATCH = 0.7
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
# --- a skimming blade's roll of paint (see _Roll) ---------------------------------
# Lengths on the painting, in pixels, tuned at about 2 px/mm (a 24 in canvas
# 1200 px wide; huile has no scale of its own to turn millimetres into
# pixels by).
#
# Below _ROLL_ALONE of pressure the bead on a skimming blade's edge lays as
# a roll, and from _ROLL_GONE on as it did, catching on each thread top
# (see _slab): every stroke pressed that hard or harder all along is what it
# was, to the bit. Between the two the catching comes in evenly and the roll
# goes out late: by the smoothstep of the way from the one pressure to the
# other, that way raised to the power _ROLL_LATE for the roll (see _Roll).
# At each place the bead leaves the larger of the two, not their sum
# (murex-cwa): summed, a roll kept late lay on top of the catching, and a
# pull laid more midway than at _ROLL_GONE. (Summed, with _ROLL_LATE at 1.3,
# a pull loaded with 8 laid 2.7% less at 0.055 than at 0.0475 on the bare
# LINEN_COARSE and 38% less on a ground with no tooth. The larger of the
# two: at 2 a pull loaded with 8 lays 0.15% less at one pressure than at
# the one before on the bare canvas; at 3, one loaded with 3 lays 0.7%
# less over a brushed dark on LINEN_COARSE; at 2.5 both rise all the way,
# there and over a knifed dark and on the bare LINEN_COARSE loaded with 8;
# not on every ground, nor with every load: see _Roll.)
_ROLL_ALONE, _ROLL_GONE = 0.04, 0.07
_ROLL_LATE = 2.5
# How wide the roll is (px, a whole odd number): it reads the surface
# smoothed over that, in which the threads of a canvas are lost.
_ROLL_WIDTH = 5
# Over how far along the blade, either way, the roll's edge is straight
# (px): it rests on the high places of the surface that far along it, and
# what it meets elsewhere is a hollow under it.
_ROLL_STRAIGHT = 10
# How far below its edge the roll reaches with no pressure at all (paint
# thickness units), and how much further per unit of pressure.
_ROLL_REACH, _ROLL_REACH_P = 0.3, 8.0
# How much of the hollow under its edge the roll feels.
_ROLL_HOLLOW = 0.6
# How far the roll's reach wanders over the stroke (paint thickness units,
# the standard deviation: the hand wavers and the roll is uneven), in cells
# this long along the stroke and this wide along the blade (px), and finer
# ones on top, _ROLL_FINER of the first in strength.
_ROLL_WANDER = 0.55
_ROLL_CELLS = ((16.0, 5.0), (6.0, 3.0))
_ROLL_FINER = 0.6
# Over how much reach the roll comes to lay (paint thickness units): how
# soft the edges of what it lays are.
_ROLL_SOFT = 0.15
# How hard the roll is pressed against the surface where it lays (0 to 1,
# as the touch of a bead: see _slab): how thick the white lies.
_ROLL_PRESS = 0.091
# How thick the film on the blade must be for the roll to lay its whole
# sheet (paint thickness units): with a thinner film the roll is pressed
# that much less (a ramp), so that a blade with little paint lays a thinner
# sheet all along its pull and does not lay all it has as a roll (it then
# laid more barely touching than pressed harder: murex-cwa). A 110 px
# blade loaded with 8 carries a film of 40, and 32 when a pull of 270 px
# is over; loaded with 1, 5 and less as it goes.
_ROLL_FILM = 10.0
# The standard deviation of a number drawn evenly between -0.5 and 0.5.
_EVEN_SD = 1.0 / math.sqrt(12.0)
# How many rows of a roll's surface are read off the canvas at a time (see
# _roll_surface): what bounds the memory it takes, not what comes out.
_ROLL_ROWS = 64
# A knife rides no higher than this times the paint film under its blade.
_KNIFE_FILM = 0.5
# Radius (px) over which wet paint dragged by a blade moves together (viscosity).
_VISCOUS = 3
# How deep a knife sinks into wet paint already on the canvas, as a share of
# its thickness: pressure ** _KNIFE_SINK (light touch: skims; hard: nearly all).
_KNIFE_SINK = 1.8


# --- past the edge of the canvas ---------------------------------------------------
# A canvas goes on past its edge: bare at first (its ground and weave, no
# paint), and holding whatever strokes leave there. The steps of a stroke
# that reach past the edge are painted on a stage (see _Stage, _Edge): the
# part of the canvas under them and what lies past the edge there, as one
# surface, on which a step is a step like any other; so what a stroke
# leaves on the canvas is what it leaves on a larger canvas.
#
# (At first, murex-duo, past the edge was the canvas's mirror image, made
# anew for every stroke: paint that was never laid lay out there, and
# again after a blade had brought it on. Eight pulls of a clean knife onto
# the canvas over one track brought on 30,300 units where a larger canvas
# gets 18,400, murex-n6o; and over a ground a brush had laid up to the
# edge, a blade brought on 1,100 to 4,000 units where a larger canvas has
# none out there to bring, murex-6s6.)
#
# How far past each edge the canvas keeps what strokes leave, from one
# stroke to the next (px). A stroke is painted as far out as it goes, on
# what it has itself left out there; when it is over, what lies further
# out than this is forgotten (it is counted with all that crossed the
# edge, see Canvas.edge_loss), so that what a canvas keeps is bounded
# however far strokes go.
_KEPT_FAR = 128
# The planes of a canvas that a stroke changes.
_PAINT = ("top", "und", "top_a", "und_a", "top_id")
# Side (px) of the tiles in which a canvas keeps what lies past its edge
# (Canvas._past_edge): for each tile that holds anything, the planes of
# _PAINT over it and the height of the paint dried there. A tile there is
# none of is bare canvas: a canvas nothing has been taken past the edge of
# keeps nothing, and one that has keeps what was left where, 0.23 KB a
# pixel.
_KEPT_TILE = 16
# About how large a stage may be (px): a run of steps past the edge is cut
# into stages of this size, one after another (see _reaches), so that a
# stroke takes the memory of a stage, 0.25 KB a pixel, however long its way
# past the edge. (No less than a few of its steps reach.)
_STAGE_AREA = 64_000
# The paint settling after a stroke (see stroke._Run.settle) comes out the
# same at a pixel whatever lies further from it than this (px, each way: a
# pass of _engine.level moves paint one pixel, stroke._LEVEL_PASSES times,
# and what a pixel covers is then read off the pixels within four of it).
_SETTLE_REACH = 20
# About how large a piece of what the paint settles on across the edge may
# be (px; see _settling_boxes): what comes out does not hang on it.
_SETTLE_AREA = _STAGE_AREA
# How deep into the canvas (px, from an edge the stroke's reach crosses) the
# stroke's reach may go for all of it to settle with what lies past that
# edge, in pieces, and none of it on the canvas alone (see _settling_boxes).
# No less than four times _SETTLE_REACH: where it goes deeper, the strips
# along two opposite edges each take twice _SETTLE_REACH px of the canvas,
# and on less canvas than that between them one would read what the other
# has put back, and put back what the other has. (Forced on a canvas 40 px
# across, in small pieces, that way left the paint 1.4 units off and lost
# some.)
_SETTLE_DEEP = 160
assert _SETTLE_DEEP >= 4 * _SETTLE_REACH


def _kept_tiles(H: int, W: int, y0: int, y1: int, x0: int, x1: int):
    """The tiles of what a canvas H by W px keeps past its edge that the
    box (y0, y1, x0, x1) reaches, none of those that lie wholly on the
    canvas: for each its key, and the part of the box in it (ya, yb, xa,
    xb)."""
    T = _KEPT_TILE
    for ty in range(y0 // T, (y1 - 1) // T + 1):
        ya, yb = max(ty * T, y0), min((ty + 1) * T, y1)
        rows_on = ya >= 0 and yb <= H
        for tx in range(x0 // T, (x1 - 1) // T + 1):
            xa, xb = max(tx * T, x0), min((tx + 1) * T, x1)
            if rows_on and xa >= 0 and xb <= W:
                continue
            yield (ty, tx), ya, yb, xa, xb


def _bare_tile(canvas) -> tuple[np.ndarray, ...]:
    """A tile of what ``canvas`` keeps past its edge, with nothing on it:
    the planes of _PAINT, and the height of the dried paint."""
    T = _KEPT_TILE
    return (
        *(
            np.zeros((T, T, *plane.shape[2:]), plane.dtype)
            for plane in (getattr(canvas, name) for name in _PAINT)
        ),
        np.zeros((T, T), np.float32),
    )


def _dried_over(canvas, y0: int, y1: int, x0: int, x1: int) -> np.ndarray:
    """The height of the dried paint over the box (y0, y1, x0, x1) of the
    ``canvas`` and what lies past its edge: the canvas's on the canvas, and
    what has dried past the edge where the canvas keeps any."""
    H, W, T = canvas.height, canvas.width, _KEPT_TILE
    dry = np.zeros((y1 - y0, x1 - x0), np.float32)
    kept = canvas._past_edge
    if kept:
        for key, ya, yb, xa, xb in _kept_tiles(H, W, y0, y1, x0, x1):
            tile = kept.get(key)
            if tile is not None:
                dry[ya - y0 : yb - y0, xa - x0 : xb - x0] = tile[-1][
                    ya - key[0] * T : yb - key[0] * T, xa - key[1] * T : xb - key[1] * T
                ]
    cy0, cy1, cx0, cx1 = max(y0, 0), min(y1, H), max(x0, 0), min(x1, W)
    if cy0 < cy1 and cx0 < cx1:
        dry[cy0 - y0 : cy1 - y0, cx0 - x0 : cx1 - x0] = canvas.dry_height[
            cy0:cy1, cx0:cx1
        ]
    return dry


def _kept_far(key, H: int, W: int) -> bool:
    """Whether the tile ``key`` lies further past the edge of a canvas H by
    W px than the canvas keeps anything from one stroke to the next."""
    T, far = _KEPT_TILE, _KEPT_FAR
    y0, x0 = key[0] * T, key[1] * T
    return y0 + T <= -far or y0 >= H + far or x0 + T <= -far or x0 >= W + far


def _repeated(n: int, lo: int, hi: int) -> np.ndarray:
    """Which of the n pixels along one side of a canvas each of the
    positions lo..hi-1 along it reads, for the weave: itself on the canvas;
    past its edge, the canvas over again (as numpy.pad's "wrap")."""
    return np.mod(np.arange(lo, hi), n)


class _Stage:
    """What the steps of a stroke that reach past the edge of the canvas
    are painted on: the part of the canvas under them and what lies past
    its edge there, as one surface. Past the edge it holds the paint the
    canvas keeps there (``Canvas._past_edge``), wet and dried, and bare
    canvas where it keeps none; the weave goes on as the canvas's own, over
    again (as numpy.pad's "wrap"): a weave with the lay of the canvas's,
    its maps belonging together, where a blade rests on the thread tops
    around a pixel and the surface it fills down to. (The edge pixel
    repeated has no weave: white knifed onto bare canvas over the edge laid
    13 to 24% more on it than on a larger canvas. The canvas's mirror image
    has the weave's lay turned over: skimming through a corner at pressure
    0.03, a blade laid 7% less on the canvas than on larger canvases, six
    weaves each, which differ by 2% among themselves; over the weave
    repeated, 2% less.)

    It is made when the steps painted on it begin, from the canvas as it is
    then; after them :meth:`put_back` puts its part of the canvas back, and
    :meth:`keep` has the canvas keep what lies past the edge.

    It is all a stroke uses of a canvas (a ``stroke._Canvas``), from
    (``y0``, ``x0``) of the canvas ``on``. (Without ``relief`` it has the
    paint and the dried paint's height, not the maps of the relief: all the
    paint needs to settle, see :meth:`_Edge.settle`.)"""

    top: np.ndarray
    und: np.ndarray
    top_a: np.ndarray
    und_a: np.ndarray
    top_id: np.ndarray
    wet_before: np.ndarray | None

    def __init__(self, on, y0: int, y1: int, x0: int, x1: int, relief: bool = True):
        H, W = on.height, on.width
        self.on, self.y0, self.x0 = on, y0, x0
        self.height, self.width = y1 - y0, x1 - x0
        self.surface = on.surface
        # (its part of the canvas: there, and here)
        cy0, cy1, cx0, cx1 = max(y0, 0), min(y1, H), max(x0, 0), min(x1, W)
        if cy0 >= cy1 or cx0 >= cx1:  # (none)
            cy0, cy1, cx0, cx1 = y0, y0, x0, x0
        self._there = (slice(cy0, cy1), slice(cx0, cx1))
        self._here = (slice(cy0 - y0, cy1 - y0), slice(cx0 - x0, cx1 - x0))
        shape = (self.height, self.width)
        for name in _PAINT:
            plane = getattr(on, name)
            setattr(self, name, np.zeros(shape + plane.shape[2:], plane.dtype))
        self.dry_height = np.zeros(shape, np.float32)
        kept = on._past_edge
        if kept:
            for key, there, here, _past in self._tiles():
                tile = kept.get(key)
                if tile is None:
                    continue
                for name, plane in zip(_PAINT, tile, strict=False):
                    getattr(self, name)[here] = plane[there]
                self.dry_height[here] = tile[-1][there]
        for name in (*_PAINT, "dry_height"):
            getattr(self, name)[self._here] = getattr(on, name)[self._there]
        self._at = (_repeated(H, y0, y1)[:, None], _repeated(W, x0, x1)[None, :])
        if relief:
            self._relief_maps = on._relief_past_edge(self)
        # (how thick the wet paint lay before the stroke: a knife's, see
        # _Edge._enter)
        self.wet_before = None

    def _goes_on(self, plane: np.ndarray) -> np.ndarray:
        """The ``plane`` of the canvas over the stage, going on past the
        edge as the canvas's own, over again: a copy."""
        return plane[self._at]

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
        return self.on._beyond_weave()

    def _tiles(self, box=None):
        """The tiles of what the canvas keeps past its edge that the stage
        reaches (its part ``box`` of the canvas, if given: y0, y1, x0, x1;
        see :func:`_kept_tiles`): for each its key, its part of the tile
        and of the stage (two slices each), and which pixels of that part
        lie past the edge of the canvas (None: all of them)."""
        H, W, T = self.on.height, self.on.width, _KEPT_TILE
        own = (self.y0, self.y0 + self.height, self.x0, self.x0 + self.width)
        if box is None:
            box = own
        box = (
            max(box[0], own[0]),
            min(box[1], own[1]),
            max(box[2], own[2]),
            min(box[3], own[3]),
        )
        if box[0] >= box[1] or box[2] >= box[3]:
            return
        for key, ya, yb, xa, xb in _kept_tiles(H, W, *box):
            there = (
                slice(ya - key[0] * T, yb - key[0] * T),
                slice(xa - key[1] * T, xb - key[1] * T),
            )
            here = (
                slice(ya - self.y0, yb - self.y0),
                slice(xa - self.x0, xb - self.x0),
            )
            past = None
            if not (yb <= 0 or ya >= H or xb <= 0 or xa >= W):
                ys, xs = np.arange(ya, yb), np.arange(xa, xb)
                past = ((ys < 0) | (ys >= H))[:, None] | ((xs < 0) | (xs >= W))[None, :]
            yield key, there, here, past

    def part(self, box) -> _Stage:
        """The paint the stage holds over the ``box`` (y0, y1, x0, x1, in
        the canvas's pixels; all within the stage): a copy, to put back or
        keep later."""
        part = object.__new__(type(self))
        part.on, part.y0, part.x0 = self.on, box[0], box[2]
        part.height, part.width = box[1] - box[0], box[3] - box[2]
        here = (
            slice(box[0] - self.y0, box[1] - self.y0),
            slice(box[2] - self.x0, box[3] - self.x0),
        )
        for name in _PAINT:
            setattr(part, name, getattr(self, name)[here].copy())
        return part

    def take(self, part: _Stage) -> None:
        """Take the paint of ``part`` (another stage, or a :meth:`part` of
        one) where it lies on this one."""
        box = _meet(
            (self.y0, self.y0 + self.height, self.x0, self.x0 + self.width),
            (part.y0, part.y0 + part.height, part.x0, part.x0 + part.width),
        )
        if _area(box) == 0:
            return
        here = (
            slice(box[0] - self.y0, box[1] - self.y0),
            slice(box[2] - self.x0, box[3] - self.x0),
        )
        there = (
            slice(box[0] - part.y0, box[1] - part.y0),
            slice(box[2] - part.x0, box[3] - part.x0),
        )
        for name in _PAINT:
            getattr(self, name)[here] = getattr(part, name)[there]

    def put_back(self) -> None:
        """Put the stage's part of the canvas back on the canvas."""
        for name in _PAINT:
            getattr(self.on, name)[self._there] = getattr(self, name)[self._here]

    def keep(self, box=None) -> None:
        """The canvas keeps the wet paint the stage holds past its edge (in
        the ``box`` y0, y1, x0, x1, in the canvas's pixels, if given): in
        tiles, made where there is any paint and dropped where none is
        left (see _KEPT_TILE)."""
        kept = self.on._past_edge
        for key, there, here, past in self._tiles(box):
            tile = kept.get(key)
            top, und = self.top[here], self.und[here]
            if tile is None:
                if not (top[..., IV].any() or und[..., IV].any()):
                    continue
                tile = kept[key] = _bare_tile(self.on)
            if past is None:
                for name, plane in zip(_PAINT, tile, strict=False):
                    plane[there] = getattr(self, name)[here]
            else:
                for name, plane in zip(_PAINT, tile, strict=False):
                    plane[there][past] = getattr(self, name)[here][past]
            if not (tile[0][..., IV].any() or tile[1][..., IV].any() or tile[-1].any()):
                del kept[key]


class _Reach(NamedTuple):
    """A run of a stroke's steps painted on one stage (see :class:`_Edge`)."""

    first: int  # the steps: the points of the path they end at
    last: int
    box: tuple[int, int, int, int]  # (y0, y1, x0, x1): all they can reach


def _join(a, b):
    """The box that holds the boxes ``a`` and ``b`` (y0, y1, x0, x1)."""
    return (min(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), max(a[3], b[3]))


def _meet(a, b):
    """The box the boxes ``a`` and ``b`` share (none: no area)."""
    return (max(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), min(a[3], b[3]))


def _kept_band(box, H: int, W: int):
    """The part of ``box`` on a canvas H by W px and no further than
    _KEPT_FAR px past its edges."""
    far = _KEPT_FAR
    return _meet(box, (-far, H + far, -far, W + far))


def _area(box) -> int:
    return max(box[1] - box[0], 0) * max(box[3] - box[2], 0)


def _grown(box, by: int):
    """The ``box`` (y0, y1, x0, x1), ``by`` px larger all round."""
    return (box[0] - by, box[1] + by, box[2] - by, box[3] + by)


def _gathered(boxes) -> list[tuple[int, int, int, int]]:
    """The ``boxes`` (y0, y1, x0, x1), one box for two wherever that holds
    no more than the two."""
    found: list[tuple[int, int, int, int]] = []
    for b in boxes:
        joined = True
        while joined:
            joined = False
            for i, other in enumerate(found):
                both = _join(other, b)
                if _area(both) <= _area(other) + _area(b) - _area(_meet(other, b)):
                    b, joined = both, True
                    del found[i]
                    break
        found.append(b)
    return found


def _lays_outside(run: _Run, longest: float) -> int:
    """How far outside its window (px) a step of the stroke lays anything,
    the longest of its steps being ``longest`` px: a knife's ridges (see
    _engine._ridge_pads) and what its blade presses out at its ends, which
    is smeared along the stroke over two steps (see _press_out); a brush's
    ridges, as far as they may go, and the wet paint it meets all round
    its window before it pushes any there (see _engine._meet)."""
    if run.bt.rigid:
        end = _KNIFE_END_OUT + _KNIFE_END_PX + 2.0 * longest
        return max(math.ceil(run.margin), eng.whole_ceil(end) + 1)
    meets = eng.whole_ceil(max(longest, run.margin)) + 1
    return max(math.ceil(max(run.margin, run.room)) + 2, meets)


def _clear_of_edge(run: _Run, out: int) -> bool:
    """Whether no step of the stroke lays anything past the edge of its
    canvas, each laying nothing further than ``out`` px outside its
    window."""
    canvas = run.canvas
    pad = run.pad if run.bt.rigid else run.r_max * run.reach
    reach = pad + 1 + out
    y0, y1, x0, x1 = run.path_box
    return (
        math.floor(y0 - reach) >= 0
        and math.floor(x0 - reach) >= 0
        and math.ceil(y1 + reach) + 1 <= canvas.height
        and math.ceil(x1 + reach) + 1 <= canvas.width
    )


def _reaches(run: _Run) -> list[_Reach]:
    """The runs of steps of a stroke that are painted on a stage: those
    whose window, or what they lay outside it, is not all on the canvas
    (none for a stroke that stays clear of the edge), each run cut into
    runs that reach no more than about _STAGE_AREA px. A knife's are all
    of them, as far out as it goes: a blade pushes along the wet paint it
    passes over, so what it brings onto the canvas depends on all of its
    way there. A brush's stages end _KEPT_FAR px from the canvas: further
    out it goes on as over the stage's edge (see _engine.off_canvas) and
    uses its paint up, so that what it leaves within _KEPT_FAR px of the
    canvas does not hang on how far out it started."""
    canvas, pts = run.canvas, run.pts
    H, W = canvas.height, canvas.width
    # (the whole stroke clear of the edge, as most are: no step to look at,
    # and nothing to work out that the stroke has not worked out already)
    out = _lays_outside(run, run.longest_step)
    if _clear_of_edge(run, out):
        return []
    runs: list[_Reach] = []
    now: list[tuple[int, tuple[int, int, int, int]]] = []  # (the run being made)

    def close():
        if not now:
            return
        most = max(_STAGE_AREA, 2 * max(_area(b) for _, b in now))
        first, box = now[0]
        last = first
        for i, b in now[1:]:
            both = _join(box, b)
            if _area(both) > most:
                runs.append(_Reach(first, last, box))
                first, box = i, b
            else:
                box = both
            last = i
        runs.append(_Reach(first, last, box))
        now.clear()

    for i in range(1, len(pts)):
        seg = run._segment(i)
        if seg is None:
            continue
        w = run._window(seg)
        box = (w.y0 - out, w.y1 + out, w.x0 - out, w.x1 + out)
        on = box[0] >= 0 and box[2] >= 0 and box[1] <= H and box[3] <= W
        if not on and not run.bt.rigid:
            # (a brush's, no further out than the canvas keeps anything: past
            # that the stage ends, and the brush goes on as over its edge)
            box = _kept_band(box, H, W)
            on = _area(box) == 0
        if on:
            close()
        else:
            now.append((i, box))
    close()
    return runs


def _settling_boxes(canvas, reach):
    """Where in ``reach`` (y0, y1, x0, x1) the paint settles across the
    edge of the canvas: the boxes that settle each on its own (see
    :meth:`_Edge.settle`), and whether the canvas then settles alone as
    well.

    A strip along each edge the reach crosses: what lies past that edge as
    far out as anything is kept there, and twice _SETTLE_REACH px beyond
    it, with twice _SETTLE_REACH px of the canvas (the strips along the top
    and the bottom have the corners; those along the sides begin where the
    canvas does); the canvas settles alone as well, and takes over
    _SETTLE_REACH px in. Or, where the reach goes no deeper into the canvas
    than _SETTLE_DEEP px across it (a stroke along an edge), one strip that
    holds all of it, and the canvas does not settle alone: nothing settles
    twice. Each strip is cut along its length into boxes of about
    _SETTLE_AREA px, which overlap by twice _SETTLE_REACH px: what is put
    back of each lies _SETTLE_REACH px in from where it is cut, so no pixel
    is put back twice."""
    H, W, T, r = canvas.height, canvas.width, _KEPT_TILE, _SETTLE_REACH
    # (how far out anything is kept past each edge, within reach)
    top, bottom, left, right = -1, H + 1, -1, W + 1
    for key in canvas._past_edge:
        b = _meet((key[0] * T, key[0] * T + T, key[1] * T, key[1] * T + T), reach)
        if _area(b) > 0:
            top, bottom = min(top, b[0]), max(bottom, b[1])
            left, right = min(left, b[2]), max(right, b[3])
    y0, y1 = max(top - 2 * r, reach[0]), min(bottom + 2 * r, reach[1])
    x0, x1 = max(left - 2 * r, reach[2]), min(right + 2 * r, reach[3])
    on = _meet(reach, (0, H, 0, W))
    over_y = reach[0] < 0 or reach[1] > H
    over_x = reach[2] < 0 or reach[3] > W
    strips = []  # (the strip, and whether it is cut along y)
    if over_y and (_area(on) == 0 or on[1] - on[0] <= _SETTLE_DEEP):
        strips, deep = [((y0, y1, x0, x1), False)], False
    elif over_x and on[3] - on[2] <= _SETTLE_DEEP:
        strips, deep = [((y0, y1, x0, x1), True)], False
    else:
        deep = True
        if reach[0] < 0:
            strips.append(((y0, min(2 * r, reach[1]), x0, x1), False))
        if reach[1] > H:
            strips.append(((max(H - 2 * r, reach[0]), y1, x0, x1), False))
        # (a side's, between the strips along the top and the bottom)
        sy0, sy1 = (0 if reach[0] < 0 else y0), (H if reach[1] > H else y1)
        if reach[2] < 0:
            strips.append(((sy0, sy1, x0, min(2 * r, reach[3])), True))
        if reach[3] > W:
            strips.append(((sy0, sy1, max(W - 2 * r, reach[2]), x1), True))
    boxes = []
    for (sy0, sy1, sx0, sx1), tall in strips:
        lo, hi, across = (sy0, sy1, sx1 - sx0) if tall else (sx0, sx1, sy1 - sy0)
        span = max(_SETTLE_AREA // max(across, 1), 4 * r)
        at = lo
        while at < hi:
            end = hi if hi - at <= span + 2 * r else at + span
            a = max(at - 2 * r, lo)
            boxes.append((a, end, sx0, sx1) if tall else (sy0, sy1, a, end))
            at = end
    return boxes, deep


ALL = (slice(None), slice(None))


def _lying(top, und, part) -> np.ndarray:
    """The wet paint on the ``part`` (two slices) of a canvas's layers,
    channel by channel."""
    return top[part].sum(axis=(0, 1), dtype=np.float64) + und[part].sum(
        axis=(0, 1), dtype=np.float64
    )


class _Edge:
    """A stroke at the edge of the canvas: which of its steps are painted
    on a stage (see :class:`_Stage`), the count of the paint that crosses
    the edge, and how the paint settles across the edge after the stroke
    (see :meth:`settle`).

    The stroke's steps that may lay paint past the edge come in runs (see
    :func:`_reaches`), each painted on a stage that holds all the run can
    reach; the other steps are painted on the canvas itself, as ever, and
    so is all of a stroke that stays clear of the edge. A stage is made
    when its run begins and is gone when it ends, the canvas keeping what
    it held past the edge (in tiles: see _KEPT_TILE): a stroke takes the
    memory of one stage, however long it is and however far out it goes.
    What it leaves further out than the canvas keeps anything (_KEPT_FAR)
    is kept only as long as a later run of the stroke may reach it.

    Over each run the canvas and the tool together lose what the run sends
    past the edge and gain what it brings on from there: that difference,
    channel by channel, is added to the canvas's ``edge_loss`` (a knife's;
    see ``Canvas.edge_loss``)."""

    def __init__(self, run: _Run):
        canvas: Any = run.canvas  # (a huile.Canvas: the stroke's own)
        self.canvas = canvas
        self.runs = _reaches(run)
        self.next = 0  # (the next run to come)
        self.on: int | None = None  # (the run the stroke is in)
        self.stage: _Stage | None = None
        self._before = np.zeros(PACKED)
        self._home: tuple = ()
        # (how thick the wet paint the canvas keeps past its edge lay before
        # the stroke, where a knife can reach it)
        self._wet: dict[tuple[int, int], np.ndarray] = {}
        if self.runs and run.bt.rigid and canvas._past_edge:
            T = _KEPT_TILE
            for key, tile in canvas._past_edge.items():
                box = (key[0] * T, key[0] * T + T, key[1] * T, key[1] * T + T)
                if any(_area(_meet(box, r.box)) > 0 for r in self.runs):
                    self._wet[key] = tile[0][..., IV] + tile[1][..., IV]

    def at(self, run: _Run, i: int) -> None:
        """The stroke comes to its step ``i``: leave the run it was in if
        that is over, and enter the one that begins."""
        if self.on is not None and i > self.runs[self.on].last:
            self.leave(run)
        ahead = self.runs[self.next].first if self.next < len(self.runs) else None
        if self.on is None and ahead is not None and i >= ahead:
            self._enter(run)

    def _enter(self, run: _Run) -> None:
        self.on, self.next = self.next, self.next + 1
        stage = self.stage = _Stage(self.canvas, *self.runs[self.on].box)
        if run.bt.rigid:  # (a knife's: see Canvas.edge_loss)
            self._before = _held(run.brush) + _lying(stage.top, stage.und, stage._here)
        self._home = (run.canvas, getattr(run, "blade", None))
        if run.bt.rigid:
            blade = run.blade
            before = stage.wet_before = self._wet_before(stage, blade)
            run.blade = _BladeStart(0, 0, before, blade.bands, blade.band_period)
        run.paint_on(stage, stage.x0, stage.y0)

    def _wet_before(self, stage: _Stage, blade: _BladeStart) -> np.ndarray:
        """How thick the wet paint lay on the ``stage`` before the stroke
        (see :func:`_before_the_blade`): on the canvas as the stroke's
        ``blade`` has it, past the edge as the canvas kept it."""
        before = stage.top_v + stage.und_v
        H, W = self.canvas.height, self.canvas.width
        ys, xs = np.arange(stage.height) + stage.y0, np.arange(stage.width) + stage.x0
        past = ((ys < 0) | (ys >= H))[:, None] | ((xs < 0) | (xs >= W))[None, :]
        before[past] = 0.0
        for key, there, here, _past in stage._tiles():
            wet = self._wet.get(key)
            if wet is not None:
                before[here] = np.where(past[here], wet[there], before[here])
        # (the canvas, as it lay: where the stroke has it)
        h, w = blade.wet_before.shape
        box = _meet(
            (blade.wet_y0, blade.wet_y0 + h, blade.wet_x0, blade.wet_x0 + w),
            (
                max(stage.y0, 0),
                min(stage.y0 + stage.height, H),
                max(stage.x0, 0),
                min(stage.x0 + stage.width, W),
            ),
        )
        if _area(box) > 0:
            before[
                box[0] - stage.y0 : box[1] - stage.y0,
                box[2] - stage.x0 : box[3] - stage.x0,
            ] = blade.wet_before[
                box[0] - blade.wet_y0 : box[1] - blade.wet_y0,
                box[2] - blade.wet_x0 : box[3] - blade.wet_x0,
            ]
        return before

    def leave(self, run: _Run) -> None:
        """The stroke leaves the run it is in, if any (and when it is
        over): what was painted on the stage goes back on the canvas, the
        canvas keeps what lies past its edge, and what the canvas and the
        tool have lost over the run is counted."""
        if self.on is None:
            return
        stage = self.stage
        assert stage is not None
        if run.bt.rigid:
            after = _held(run.brush) + _lying(stage.top, stage.und, stage._here)
            self.canvas.edge_loss += self._before - after
        stage.put_back()
        stage.keep()
        canvas, blade = self._home
        if blade is not None:
            run.blade = blade
        run.paint_on(canvas)
        self._forget(self.runs[self.on].box, self.runs[self.next :])
        self.on = self.stage = None

    def _forget(self, box, later=()) -> None:
        """Of what the canvas keeps in ``box`` further out than it keeps
        anything from one stroke to the next, forget all that none of the
        runs ``later`` can reach."""
        kept = self.canvas._past_edge
        H, W, T = self.canvas.height, self.canvas.width, _KEPT_TILE
        if _area(_kept_band(box, H, W)) == _area(box):
            return
        for key, *_ in list(_kept_tiles(H, W, *box)):
            if key in kept and _kept_far(key, H, W):
                tile = (key[0] * T, key[0] * T + T, key[1] * T, key[1] * T + T)
                if not any(_area(_meet(tile, r.box)) > 0 for r in later):
                    del kept[key]

    def settle(self, run: _Run) -> None:
        """The paint settles after the stroke (see stroke._Run.settle): on
        the canvas; and, where the stroke reached past the edge, or near
        enough to it for paint to slump over it, across the edge, on the
        canvas and what lies past it together, as one surface. What
        crosses the edge so is counted with the rest (a knife's; see
        ``Canvas.edge_loss``).

        (Settling on the canvas alone, the edge was a wall: thick paint
        left near it piled against it, and the heap a blade had pushed past
        it stood as the blade left it. A knife loaded with 4 stopping 6 px
        short of the edge at pressure 0.9, over 3.6 units of wet paint,
        left 310 units on the canvas that slump off it on a larger one:
        murex-w8r.)

        Each piece of the canvas and what lies past its edge where paint
        may cross it (see :func:`_settling_boxes`) settles on its own,
        from the paint as the stroke left it, one piece at a time, and is
        put back, and kept, as far as it came out as the whole would:
        _SETTLE_REACH px in from where it was cut out of it. Where the
        stroke reaches deep into the canvas, the canvas then settles, alone,
        as ever, and what the pieces hold of it is put back after that:
        each holds all that lies within twice _SETTLE_REACH px of where
        paint may cross the edge, so beyond what is put back the canvas
        alone settles as the whole would."""
        canvas = self.canvas
        H, W = canvas.height, canvas.width
        kept = canvas._past_edge
        for key in [key for key in kept if _kept_far(key, H, W)]:
            del kept[key]
        reach = _kept_band(run.settles_over(), H, W)
        if not (reach[0] < 0 or reach[2] < 0 or reach[1] > H or reach[3] > W):
            run.settle(part=reach)  # (on the canvas, where the stroke reached)
            return
        boxes, deep = _settling_boxes(canvas, reach)
        # (whether any paint levels is asked of all it settles on, on the
        # canvas and past its edge, as on a canvas that holds it all:
        # _engine.level asks it of what it is given)
        thick = self._thick(reach, boxes)
        backs = self._settle_pieces(run, boxes, reach, deep, thick)
        if deep:
            run.settle(thick=thick)
            self._put_back(backs, run.bt.rigid)

    def _settle_pieces(self, run: _Run, boxes, reach, deep: bool, thick: bool):
        """The paint settles in each of the ``boxes`` (see :meth:`settle`).
        Returns what is to go back on the canvas once that has settled
        alone, if it does (``deep``)."""
        canvas, r = self.canvas, _SETTLE_REACH
        backs: list[_Stage] = []
        # (the paint as the stroke left it, where a piece to come reads what
        # an earlier one has put back, or the canvas kept, since: for which
        # piece, and the paint)
        before: list[tuple[int, _Stage]] = []
        for k, box in enumerate(boxes):
            mine = [part for j, part in before if j == k]
            before = [b for b in before if b[0] != k]
            if not self._wet_in(box):
                continue  # (nothing to settle there)
            piece = _Stage(canvas, *box, relief=False)
            for part in mine:
                piece.take(part)
            run.settle(piece, (0, piece.height, 0, piece.width), thick)
            # (as the whole comes out: not near where the piece was cut out
            # of it, unless that is where the stroke's reach ends, which the
            # paint does not settle past on any canvas)
            core = (
                box[0] + (r if box[0] > reach[0] else 0),
                box[1] - (r if box[1] < reach[1] else 0),
                box[2] + (r if box[2] > reach[2] else 0),
                box[3] - (r if box[3] < reach[3] else 0),
            )
            if _area(core) == 0:
                continue
            for j in range(k + 1, len(boxes)):
                both = _meet(core, boxes[j])
                if _area(both) > 0:
                    before.append((j, _Stage(canvas, *both, relief=False)))
            self._settled(piece, core, deep, backs, run.bt.rigid)
            del piece
        return backs

    def _settled(self, piece: _Stage, core, deep: bool, backs, counted: bool) -> None:
        """The ``piece`` has settled (see :meth:`settle`): the canvas keeps
        what it holds past the edge within ``core``, and its part of the
        canvas there is put back; once the canvas has settled alone too, if
        it does (``deep``: kept in ``backs`` till then)."""
        canvas = self.canvas
        on = _meet(core, (0, canvas.height, 0, canvas.width))
        if _area(on) > 0 and deep:
            backs.append(piece.part(on))
        elif _area(on) > 0:
            there = (slice(on[0], on[1]), slice(on[2], on[3]))
            here = (
                slice(on[0] - piece.y0, on[1] - piece.y0),
                slice(on[2] - piece.x0, on[3] - piece.x0),
            )
            if counted:
                canvas.edge_loss += _lying(canvas.top, canvas.und, there)
                canvas.edge_loss -= _lying(piece.top, piece.und, here)
            for name in _PAINT:
                getattr(canvas, name)[there] = getattr(piece, name)[here]
        if _area(on) < _area(core):
            piece.keep(core)

    def _put_back(self, parts, counted: bool) -> None:
        """Put the ``parts`` of the canvas back on it as they have settled
        (see :meth:`settle`), with what has crossed the edge ``counted``."""
        canvas = self.canvas
        for part in parts:
            there = (
                slice(part.y0, part.y0 + part.height),
                slice(part.x0, part.x0 + part.width),
            )
            if counted:
                canvas.edge_loss += _lying(canvas.top, canvas.und, there)
                canvas.edge_loss -= _lying(part.top, part.und, ALL)
            for name in _PAINT:
                getattr(canvas, name)[there] = getattr(part, name)

    def _thick(self, reach, boxes) -> bool:
        """Whether any wet paint within ``reach`` on the canvas, or in the
        ``boxes`` past its edge, is thick enough to level (0.3 units: see
        _engine.level)."""
        canvas = self.canvas
        H, W = canvas.height, canvas.width
        kept = canvas._past_edge
        T = _KEPT_TILE
        on = _meet(reach, (0, H, 0, W))
        most = 0.0
        if _area(on) > 0:
            part = (slice(on[0], on[1]), slice(on[2], on[3]))
            most = float((canvas.top_v[part] + canvas.und_v[part]).max())
        for box in boxes:
            for key, ya, yb, xa, xb in _kept_tiles(H, W, *box):
                if key in kept:
                    # (only the part of the tile in the box: thick paint
                    # beside it in the same tile is not what settles here)
                    part = (
                        slice(ya - key[0] * T, yb - key[0] * T),
                        slice(xa - key[1] * T, xb - key[1] * T),
                        IV,
                    )
                    tile = kept[key]
                    most = max(most, float((tile[0][part] + tile[1][part]).max()))
        return not most < 0.3

    def _wet_in(self, box) -> bool:
        """Whether there is any wet paint in the ``box`` (y0, y1, x0, x1),
        on the canvas or past its edge."""
        canvas = self.canvas
        H, W = canvas.height, canvas.width
        on = _meet(box, (0, H, 0, W))
        if _area(on) > 0:
            part = (slice(on[0], on[1]), slice(on[2], on[3]))
            if canvas.top_v[part].any() or canvas.und_v[part].any():
                return True
        kept = canvas._past_edge
        return bool(kept) and any(
            key in kept and (kept[key][0][..., IV].any() or kept[key][1][..., IV].any())
            for key, *_ in _kept_tiles(H, W, *box)
        )


class _BladeStart(NamedTuple):
    """What a knife stroke starts from (see :func:`_before_the_blade`)."""

    wet_y0: int  # where wet_before lies on the canvas
    wet_x0: int
    wet_before: np.ndarray  # the wet paint there before the stroke
    bands: np.ndarray  # the bands the colours on the blade wander in
    band_period: float  # (px along the stroke)


def _before_the_blade(canvas, rng, pts, pad, w_typ, length) -> _BladeStart:
    """What a knife stroke starts from: the wet paint lying on the canvas
    before it, which the blade's ends push aside into lips (a pile it is
    carrying mostly rides along), over the part of the canvas within ``pad``
    px of its path, from (wet_y0, wet_x0); and the bands its colours wander
    in (see :func:`_wandering_bands`) and their period along the stroke (px),
    over the ``length`` of its path (px, see ``stroke._Own``: the same
    bands however it is cut)."""
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
    n_s = eng.whole_floor(length / period) + 3
    bands = value_noise_2d(8 * n_s, 64, 8.0, rng)
    return _BladeStart(wet_y0, wet_x0, wet_before, bands, period)


class _Roll(NamedTuple):
    """What the roll of paint on a skimming blade's edge leaves over a
    stroke: the bead of :func:`_slab` at the lightest touch, as a roll
    (murex-dnj).

    The bead as it lays at a light touch catches where a thread top meets a
    nick of the blade: specks a thread across, on the lattice of the weave.
    A roll of stiff paint is wider than a thread and holds together. It
    reads the surface as it lay before the stroke, smoothed over its own
    width (_ROLL_WIDTH); its edge is straight over a short way along the
    blade (_ROLL_STRAIGHT) and rests on the high places there, so that what
    lies lower is a hollow under it; how far below its edge it reaches goes
    by the pressure (_ROLL_REACH, _ROLL_REACH_P) and wanders over the
    stroke, as the hand wavers and the roll is uneven (_ROLL_WANDER, a
    texture of the stroke's own, against the distance along it and the
    place across it). It lays where it reaches the surface, coming in over
    _ROLL_SOFT of reach, and there it leaves the paint of a bead pressed
    _ROLL_PRESS against the surface: a sheet of one thickness, with holes
    where the surface falls away or the roll lifts.

    All of it is worked out before the stroke, over the stroke: ``lays``,
    the share of a bead's full coat that the roll leaves, in rows 1 px of
    the stroke's way apart from ``row0`` px along it and columns 1 px
    across it, the path in column ``mid``; and ``share``, by the pressure
    at each row: how much of that the roll leaves there (1 up to
    _ROLL_ALONE, 0 from _ROLL_GONE on), and how much of what it left as a
    bead catching on thread tops the bead leaves (0 up to _ROLL_ALONE, 1
    from _ROLL_GONE on). A step reads them where each of its pixels lies
    (see :func:`_rolled`): nothing in them hangs on how the stroke is cut
    into steps, and nothing is kept from one step to the next.

    The sheet is as thick as that only under a blade with paint to spare:
    with a film thinner than _ROLL_FILM on it the roll is pressed that much
    less (see :func:`_roll_thin`), where the blade is and as its film is
    in the step, as the bead's height is.

    Between the two pressures the bead's catching comes in evenly
    (smoothstep) and the roll goes out late (_ROLL_LATE), and at each place
    the bead leaves the larger of what the two would, not their sum: so
    that the paint a pull lays rises with the pressure all the way where a
    blade at _ROLL_GONE lays more than a roll does: over a wet dark, on
    the bare default canvas and, loaded with 8 or more, on the bare
    LINEN_COARSE. Where it does not, no way of going from the one to the
    other rises all the way, and a pull pressed harder lays less: on a
    ground with no tooth (glass, a canvas made with ``texture=0``), where
    the catching comes to next to nothing before 0.06 (by 9 to 25% loaded
    with 8 or 20, 35 to 66% loaded with 3 or 1); and on the bare
    LINEN_COARSE loaded with 3 (3 to 10%). How far varies with the
    stroke's seed. The figures are in docs/huile/README.md, and
    tests/huile/test_skim.py holds some."""

    lays: np.ndarray
    share: np.ndarray
    row0: float
    mid: float


def _roll_of(canvas, rng, bt, own, half: float, far: float) -> _Roll | None:
    """The roll of a knife stroke about to begin on ``canvas`` (see
    :class:`_Roll`), or None if it has none: a comb's teeth carry no roll,
    and a stroke pressed _ROLL_GONE or harder all along lays as it did.

    ``own``: the stroke in its own steps (a ``stroke._Own``: its points,
    the distance along them and the pressure there, and the length of its
    path), whatever steps it is painted in; ``half``: the widest its blade
    reaches across the stroke, and ``far`` from its path at all (px), in
    those steps. ``rng``: the stroke's random numbers; the roll's are
    drawn from a generator of their own made from them, which takes
    nothing from theirs."""
    if bt.clumps > 0 or not (float(own.pressure.min()) < _ROLL_GONE):
        return None
    if not own.arc[-1] > 0:
        return None
    pad = eng.whole_ceil(far) + 4
    n_s = eng.whole_ceil(own.length) + 2 * pad + 1
    n_u = 2 * eng.whole_ceil(half) + 9
    rows = np.arange(n_s, dtype=np.float64) - pad
    wander = _roll_wander(n_s, n_u, rng.spawn(1)[0])
    r = _ROLL_WIDTH // 2
    surface = _roll_surface(canvas, own, rows, n_u, r)
    # (the edge: on the high places along it, and no sharper than the roll)
    edge = _box(np.pad(_max_along(surface, _ROLL_STRAIGHT), r, mode="edge"), r)
    hollow = np.maximum(edge - surface, 0.0)
    p = np.interp(np.clip(rows, 0.0, own.arc[-1]), own.arc, own.pressure)
    reach = (_ROLL_REACH + _ROLL_REACH_P * p)[:, None] - _ROLL_HOLLOW * hollow - wander
    lays = (_ROLL_PRESS * smoothstep(0.0, _ROLL_SOFT, reach)) ** _KNIFE_CATCH
    # (how far the pressure is from the roll alone towards none of it)
    x = np.clip((p - _ROLL_ALONE) / (_ROLL_GONE - _ROLL_ALONE), 0.0, 1.0)
    share = np.stack(
        [1.0 - smoothstep(0.0, 1.0, x**_ROLL_LATE), smoothstep(0.0, 1.0, x)]
    )
    return _Roll(np.ascontiguousarray(lays), share, float(-pad), 0.5 * (n_u - 1))


def _roll_wander(n_s: int, n_u: int, rng) -> np.ndarray:
    """How a roll's reach wanders over the stroke (see :class:`_Roll`), in
    ``n_s`` rows along it and ``n_u`` columns across it, 1 px apart: value
    noise in cells of _ROLL_CELLS px, of standard deviation _ROLL_WANDER
    at every place. As many numbers are drawn as the rows and columns call
    for: for each size of cell its grid, and where in a cell the first row
    and the first column lie.

    Value noise is a number drawn at each corner of a cell and smoothed
    from one corner to the next: at a corner it is that one number, and
    midway between four it is their mean, which strays half as far. So
    each place's value is divided by how far values stray there. (Left as
    it comes, with the cells beginning at the first row of every stroke,
    the wander strayed 0.61 units at the corners of the larger cells and
    0.48 midway, and a hole was 1.56 times likelier at a corner: over 24
    strokes on one ground the share left bare ran from 0.15 to 0.26 along
    the pull, every 16 px.)"""
    out = np.zeros((n_s, n_u))
    strays = np.zeros((n_s, n_u))
    amp = 1.0
    for along, across in _ROLL_CELLS:
        grid = rng.random(
            (eng.whole_floor(n_s / along) + 3, eng.whole_floor(n_u / across) + 3)
        )
        first = rng.random(2)
        a, b = np.arange(n_s) / along + first[0], np.arange(n_u) / across + first[1]
        ia, ib = a.astype(np.int64), b.astype(np.int64)
        fa, fb = (a - ia)[:, None], (b - ib)[None, :]
        fa, fb = fa * fa * (3.0 - 2.0 * fa), fb * fb * (3.0 - 2.0 * fb)
        near = grid[ia][:, ib] * (1.0 - fb) + grid[ia][:, ib + 1] * fb
        far = grid[ia + 1][:, ib] * (1.0 - fb) + grid[ia + 1][:, ib + 1] * fb
        out += amp * (near * (1.0 - fa) + far * fa - 0.5)
        # (the variance of what four numbers so weighted come to, in that of one)
        strays += (amp * amp) * ((1.0 - fa) ** 2 + fa**2) * ((1.0 - fb) ** 2 + fb**2)
        amp *= _ROLL_FINER
    return out * (_ROLL_WANDER / (_EVEN_SD * np.sqrt(strays)))


def _roll_surface(canvas, own, rows, n_u: int, r: int) -> np.ndarray:
    """The surface as it lies on ``canvas`` (the solid surface and the wet
    paint, and what lies past the edge where the stroke goes there), as
    the roll of a stroke reads it (see :class:`_Roll`): smoothed over 2 r
    + 1 px, at the ``rows`` px along the stroke's path (``own``: see
    :func:`_roll_of`; straight on before its start and past its end) and
    in ``n_u`` columns 1 px apart across it.

    Read where each place lies from the stroke's first point, on the grid
    its path lies on (stroke._PATH_GRID), so that the same stroke a whole
    number of pixels further on reads the same; and off the canvas a few
    rows at a time (_ROLL_ROWS), each pixel smoothed from the pixels
    around it alone, so that it takes the memory of those rows however
    long the stroke is, and comes out the same wherever it is cut."""
    arc, end = own.arc, float(own.arc[-1])
    first = own.pts[0]
    rel = own.pts - first
    on = np.clip(rows, 0.0, end)
    ahead, back = np.minimum(on + 1.0, end), np.maximum(on - 1.0, 0.0)
    tx = np.interp(ahead, arc, rel[:, 0]) - np.interp(back, arc, rel[:, 0])
    ty = np.interp(ahead, arc, rel[:, 1]) - np.interp(back, arc, rel[:, 1])
    n = np.maximum(np.hypot(tx, ty), 1e-12)
    tx, ty = tx / n, ty / n
    px = np.interp(on, arc, rel[:, 0]) + (rows - on) * tx
    py = np.interp(on, arc, rel[:, 1]) + (rows - on) * ty
    across = np.arange(n_u) - 0.5 * (n_u - 1)
    # (pixel (i, j) has its centre at (j + 0.5, i + 0.5))
    X = _on_path_grid(px[:, None] - across * ty[:, None]) + (first[0] - 0.5)
    Y = _on_path_grid(py[:, None] + across * tx[:, None]) + (first[1] - 0.5)
    out = np.empty(X.shape)
    for a in range(0, len(rows), _ROLL_ROWS):
        x, y = X[a : a + _ROLL_ROWS], Y[a : a + _ROLL_ROWS]
        ix, iy = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
        x0, y0 = int(ix.min()), int(iy.min())
        box = (y0 - r, int(iy.max()) + 2 + r, x0 - r, int(ix.max()) + 2 + r)
        smooth = _box(_surface_over(canvas, box), r)
        fx, fy = x - ix, y - iy
        ix, iy = ix - x0, iy - y0
        out[a : a + _ROLL_ROWS] = (
            smooth[iy, ix] * (1.0 - fx) + smooth[iy, ix + 1] * fx
        ) * (1.0 - fy) + (
            smooth[iy + 1, ix] * (1.0 - fx) + smooth[iy + 1, ix + 1] * fx
        ) * fy
    return out


# The grid a knife's path lies on (px): stroke._PATH_GRID, written out here
# as _knife cannot read stroke's (a test checks that the two agree).
_PATH_GRID = 2.0**-20


def _on_path_grid(x):
    """The nearest to ``x`` (px) on the grid a knife's path lies on
    (_PATH_GRID)."""
    return np.round(x / _PATH_GRID) * _PATH_GRID


def _surface_over(canvas, box) -> np.ndarray:
    """How high the surface lies over the ``box`` (y0, y1, x0, x1) of
    ``canvas``, the solid surface and the wet paint on it: on the canvas;
    and past its edge, where it goes on (see :class:`_Stage`)."""
    y0, y1, x0, x1 = box
    if y0 >= 0 and x0 >= 0 and y1 <= canvas.height and x1 <= canvas.width:
        at = (slice(y0, y1), slice(x0, x1))
        floor, top, und = canvas._relief().floor[at], canvas.top_v[at], canvas.und_v[at]
    else:
        stage = _Stage(canvas, y0, y1, x0, x1)
        floor, top, und = stage._relief().floor, stage.top_v, stage.und_v
    return floor.astype(np.float64) + top + und


def _box(a: np.ndarray, r: int) -> np.ndarray:
    """The mean of ``a`` over the 2 r + 1 px square around each of its
    pixels that has one (r fewer rows and columns all round): summed pixel
    by pixel in one order, so that a pixel's comes out the same to the bit
    whatever part of a larger array it is worked out in."""
    n = 2 * r + 1
    h, w = a.shape[0] - 2 * r, a.shape[1] - 2 * r
    rows = a[0:h].copy()
    for k in range(1, n):
        rows += a[k : k + h]
    out = rows[:, 0:w].copy()
    for k in range(1, n):
        out += rows[:, k : k + w]
    return out / (n * n)


def _max_along(a: np.ndarray, r: int) -> np.ndarray:
    """The most of ``a`` within ``r`` columns of each of its places, along
    its row."""
    out = a.copy()
    for k in range(1, min(r, a.shape[1] - 1) + 1):
        np.maximum(out[:, k:], a[:, :-k], out=out[:, k:])
        np.maximum(out[:, :-k], a[:, k:], out=out[:, :-k])
    return out


def _rolled(run: _Run, s: _Step):
    """What the roll of paint on the blade's edge leaves over each pixel of
    the step's part of the canvas, as a share of the bead's full coat, and
    the share of what the bead leaves as it did that is left there (two
    planes: see :class:`_Roll` and _engine.roll_at); None for a stroke
    with no roll."""
    roll = run.roll
    if roll is None:
        return None
    if s.roll is None:
        win = s.st.win
        s.roll = eng.roll_at(
            s.F,
            win.wy0,
            win.wx0,
            win.ch,
            win.cw,
            s.st.motion.arc_i,
            roll.lays,
            roll.share,
            roll.row0,
            roll.mid,
        )
    return s.roll


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
        st.motion.arc_i,
        blade.band_period,
        blade.bands,
        _KNIFE_BAND_WANDER,
    )


def _knife_taps(run: _Run, st, F):
    """The bristle taps of a knife's step ``st`` (footprint ``F``) over its
    window (all of it is on what the step is painted on: the canvas, or a
    stage, see :class:`_Stage`)."""
    u = _wandering_bands(run, F, st, st.win)
    return eng.bristle_taps(u, st.hold.span, st.hold.nsub, run.brush.ring, st.hold.rho)


def _flow_subs(run: _Run, st) -> tuple[int, float]:
    """The sub-steps of the flow under a knife's blade that fall in the step
    ``st`` of its stroke (how many, and how far into the step the first is,
    px: see _engine.flow_sub_steps): they are laid along the stroke, which
    keeps how far into one it is (``run.flow_phase``). Asked for every step
    of the stroke in turn, whether the step is painted or not."""
    if run.bt.clumps > 0:  # (a comb's teeth cut the paint: they drag none)
        return 0, 0.0
    n_sub, first, run.flow_phase = eng.flow_sub_steps(
        run.flow_phase, st.motion.ds, st.motion.tx, st.motion.ty
    )
    return n_sub, first


def _knife_step(run: _Run, s: _Step) -> None:
    """One step of a knife, in stages that change the canvas in this order:
    the paint it pushes aside (4), the film it drags (5), the paint squeezed
    out beside it, the slab it lays and the paint it presses out at its ends
    (6), the peaks it pulls up as it lifts off, and the layers it folds
    together (7). (A blade that rides on wet paint of earlier strokes does
    4, 5 and what it lays of 6 together, sub-step by sub-step: see
    :func:`_drag_film`.)"""
    st = s.st
    win = st.win
    area = max(run.area_unit * st.hold.r * st.hold.r, 1e-9)  # of the blade, px
    # (how readily the paint takes stirring, as it lies before this step)
    _f_pick, _f_dep, f_mix, _f_drag = eng.surface_factors(run.cv, run.aux, win, run.K)
    # (The canvas, here and below: what the step is painted on. For the
    # steps of a stroke that reach past the edge of the canvas that is a
    # stage, the canvas and what lies past its edge, see _Stage and _Edge:
    # all of a step's window is on it, and a blade meets no edge.)
    flows = run.bt.clumps == 0  # (a comb's teeth cut the paint: they drag none)

    # 1) All the paint on a knife is on the blade, ready to go down; several
    #    paints loaded side by side blend slowly as it works. (A knife doesn't
    #    pick wet paint up as it goes: it drags it, step 5.)
    eng.work_load(run.br, run.K, st, np.inf)
    col_vol, _load, col_load, _col_body, body = eng.load_stats(
        run.brush.tip, run.brush.reservoir, st.hold.Wn
    )
    gap, hold = _blade_gap(run, st.hold.p)  # 2)
    rested = _blade_rest(run, s)
    held = _held(run.brush, IV)
    # (the film on the blade as it will be midway through the step)
    less = _use_ahead(run, s, gap, area, rested, held)
    film = _film(run, s, area, less)
    level, ride, hang, riding = _blade_riding(run, s, gap, film, rested)  # 3)
    # (a blade riding on wet paint pushes it aside as it goes: see _drag_film)
    ridges = (
        eng.Ridges(np.zeros(PACKED), np.zeros(PACKED), np.zeros(PACKED))
        if flows and riding is not None
        else _push_aside(run, s, level)  # 4)
    )
    # (the gaps under the blade as it met them, or what it laid as it went:
    # see _drag_film)
    as_met = (None, None, None)
    met = _drag_film(run, s, level, hang, film, riding, ridges) if flows else None  # 5)
    if met is not None:
        # (from here on the blade is where the step ends, at the level the
        # paint it has dragged there holds it at)
        as_met, level, hang = met[:3], met.level, met.hang
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
    _fill_under_blade(run, s, level, ride, hang, area, as_met, less)  # 6)
    # A knife lifted off thick paint pulls it up into little peaks and torn ridges.
    if run.eff["lift"] > 0 and st.motion.last:
        _lift_blade(run, s, body)
    _fold_layers(run, s, level, f_mix)  # 7)
    if not (st.motion.first or st.motion.last):
        # (the share the step used of what each column held, and over how
        # long a way)
        used = np.maximum(held - _held(run.brush, IV), 0.0)
        run.last_use = (used / np.maximum(held, 1e-30), st.motion.ds)


def _blade_gap(run: _Run, p: float) -> tuple[float, float]:
    """2) The blade rides above the surface at a gap set by pressure ``p``
    (all its paint is a film under it; what doesn't fit under it rides along
    on it). Returns the gap and how much paint the blade holds (load units)."""
    bt = run.bt
    gap = _KNIFE_GAP * (1.0 - p) ** 1.6 * (0.55 + 0.45 * bt.stiffness) + 0.05
    if bt.clumps > 0:  # the teeth of a comb dig in, down to the threads
        gap *= 0.03
    return gap, gap * run.area_unit / 4.0 + _KNIFE_CARRY


def _film(run: _Run, s: _Step, area: float, less=None):
    """How thick the film of paint on the blade is over each pixel, from the
    paint on it as it stands now (``less``: with that much less on each of
    its columns, see :func:`_use_ahead`): where the blade rides (3) and what
    it fills (6) each read it, before and after it has spread and squeezed
    some out."""
    brush, st = run.brush, s.st
    held = brush.tip[:, IV] + brush.reservoir[:, IV]
    if less is not None:
        held = np.maximum(held - less, 0.0)
    return eng.at_pixels(s.taps, held, st.win.ch, st.win.cw) * COLUMNS / area


def _held(brush, channel: int | None = None) -> np.ndarray:
    """The paint on a blade: channel by channel; or, of one ``channel``,
    column by column (what the blade lays comes from its tips and what
    refills them: a knife's heel holds none)."""
    if channel is None:
        return (brush.tip.astype(np.float64) + brush.reservoir + brush.heel).sum(axis=0)
    return brush.tip[:, channel].astype(np.float64) + brush.reservoir[:, channel]


def _use_ahead(run: _Run, s: _Step, gap: float, area: float, rested, held):
    """Half of what the step is going to use of the paint on each column of
    the blade (``held``: what each holds), as near as can be told before the
    step; None for the step that sets the blade down and the one that lifts
    it off, which lay what is under the blade as it stands.

    How high the blade rides (3) and how far its film reaches down (6) go
    by the film on it, and the step uses that film up as it goes: with a
    loaded blade riding high, a fifth of it over 8 px. Read as the step
    begins and held over the step, the film is too thick all along it, the
    more the longer the step: the blade lays its paint sooner, runs low
    sooner and from then on rides lower, on what lies under it. (A knife
    loaded with 3 and pulled at pressure 0.25 laid a slab 18% thinner
    midway along at a stroke's own steps than in steps of half a pixel, on
    the bare canvas, and over wet paint carried that paint 9 to 12%
    further: murex-5gw.) So the step is worked out for the film as it will
    be midway through it: what it holds now, less half of what the step
    will use.

    That is told by what the step before it used, over as long a way: a
    stroke's use changes little from one step to the next. The first step
    along the stroke has none before it but the set-down, which is no
    measure of it: there it is what the step would lay on the canvas as it
    shows, at the level the film as it is holds the blade at."""
    st = s.st
    if st.motion.first or st.motion.last:
        return None
    if run.last_use is not None:
        share, over = run.last_use
        return 0.5 * np.minimum((st.motion.ds / over) * share, 1.0) * held
    if not (run.brush.tip[:, IV].sum() > 0 and run.bt.deposits):
        return None
    film = _film(run, s, area)
    level, _ride, hang, _riding = _blade_riding(run, s, gap, film, rested)
    d, _skim = _slab(run, s, level, hang, area)
    tip = run.brush.tip[:, IV].astype(np.float64)
    return 0.5 * np.minimum(eng.column_demand(s.taps, d), tip)


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
    rest, old_v, vmax, under_blade, any_under, top_ib = eng.blade_rest(
        canvas.top,
        canvas.und,
        canvas.top_id,
        _mine(run, s),
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
    )
    # Wet paint from earlier strokes holds the blade up too, the heap it pushes
    # included (a knife rides on a wave of paint): it rests on its high points
    # and sinks in the harder it is pressed (less into stiff paint). A light
    # touch lays new paint on top of the old.
    if not (vmax > _KNIFE_RIDES_ON and any_under):
        return rest.astype(np.float64), None
    # (summed by numpy, and summed as numpy always summed it: on the canvas
    # over the strided view of the canvas itself, row by row, which rounds
    # differently from a contiguous copy of the same pixels)
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


def _blade_level(run: _Run, s: _Step, gap: float, film):
    """3) How high the blade's edge rides over each pixel: on what it rests
    on (:func:`_blade_rest`), at ``gap``, less as the paint under it runs low
    (``film``, see :func:`_film`). Returns the level, how high it rides on
    the paint (see _engine.blade_level), and the level the bead on its edge
    hangs from if it skims (see :func:`_slab`; the level if it doesn't)."""
    return _blade_riding(run, s, gap, film)[:3]


def _blade_riding(run: _Run, s: _Step, gap: float, film, rested=None):
    """:func:`_blade_level`, and what the blade rides on if that is wet
    paint of earlier strokes (see :func:`_blade_rest`), else None."""
    st = s.st
    # The blade rides on the paint under it: as that runs low, it sinks and the
    # slab thins out (not a comb's teeth). Nicks and grit on its edge leave
    # fine scratches along the stroke; it wavers as it is pushed (chatter) and
    # is never pressed quite evenly along its length (tilt).
    # (skimming, the blade glides: no chatter; its nicks still streak the paint)
    skim = eng.smoothstep(_KNIFE_SKIM, 0.05, st.hold.p)
    rest, riding = _blade_rest(run, s) if rested is None else rested
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
    adds to it (a Ridges).

    This is for a blade that does not ride on wet paint of earlier strokes
    (a riding blade spills as it goes: see :func:`_drag_film`). The two do
    not take the same paint: what this one spills comes off the top layer
    first (_engine.take), the stroke's own paint if it lies there; what a
    riding blade spills is the earlier strokes' paint first
    (_engine._take_aside). It is left so because this one has next to
    nothing to spill: what it spills is no more than lay there before the
    stroke, and no wet paint of earlier strokes thicker than
    _KNIFE_RIDES_ON lies under it now. (Over 44 pulls on five grounds
    riding blades spilt 19,066 units, and blades that did not ride none:
    the most a pixel would have spilt, 0.0002 units, is under what a step
    spills at all.)"""
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


def _drag_film(run: _Run, s: _Step, level, hang, film, riding=None, ridges=None):
    """5) The blade drags the wet paint it touches, as a thin-film flow:
    between the moving blade and the still canvas the paint shears, so paint
    near the blade travels almost with it and paint at the canvas hardly
    moves; what stands above the blade is bulldozed ahead of it. Each wet
    layer moves at its own speed, so their order is kept (white dragged over
    purple stays on top). The blade glides on its own fresh paint: the
    thicker the film of it, the less it drags what lies under it, and under
    a thick one it pushes on only what is in its way, the paint it has
    brought there and what stands above it (see _engine.glides and
    pushed_under_film; it left that where its own paint began, in a heap:
    murex-6fa).

    On the solid surface alone (``riding`` None) its level stays, and what
    it lays it lays when the step is over: returns, for :func:`_slab`, what
    it met over each pixel as it went (see _engine.flow_under_blade): the
    gap its ``film``, the one it rides on (3), could fill under its level,
    and the surface as the bead hanging from ``hang`` found it, as far down
    as the bead reaches; None if it dragged nothing: the gap and the
    surface are then those the canvas shows.

    Where it rides on wet paint of earlier strokes (``riding``, see
    :func:`_blade_rest`), that paint travels under it as a wave it pushes,
    and all the step does to it hangs together: how high the blade rides,
    what it spills at its ends, what it drags, and what it lays, which is
    the film it then glides on. So the step is worked out sub-step by
    sub-step, in sub-steps laid along the stroke and not along the step
    (``s.subs``, see :func:`_flow_subs` and
    _engine.flow_under_riding_blade; ``level`` and ``hang`` are read from
    the paint under where the step takes the blade, which the wave it
    pushes has not reached yet). What it spills is added to ``ridges``
    (see :func:`_push_aside`, which does that for a blade that does not
    ride). Returns what it laid over each pixel as it went (below 0 where
    it never was), and its level and the level its bead hangs from where
    it ends the step."""
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
        return _Met(gaps, None, None, level, hang) if gaps.size else None
    fill, _skim, _n = _fill_share(run, s)
    coat, rolled, kept = _bead_coat(run, s, film)
    if not (run.brush.tip[:, IV].sum() > 0 and run.bt.deposits):
        # (a blade with no paint on it lays none)
        fill = coat = rolled = kept = _NO_COAT
    spill = (
        np.ascontiguousarray(s.lat_px[wsl]),
        # (the share of what stands above the blade that a pass moves, as
        # _push_aside has it)
        1.0 - np.exp(-4.0 * s.expo[wsl] * (0.15 + 1.7 * hair**2)),
        max(st.hold.r * st.hold.lmax, 1e-6),  # the mark's half-width, px
        _KNIFE_SPILL_PX,
        _KNIFE_SPILL,
    )
    laid, ends, (left, right), reached = eng.flow_under_riding_blade(
        *flow,
        riding,
        s.subs if s.subs is not None else (0, 0.0),
        (fill, coat, _KNIFE_CATCH, rolled, kept),
        spill,
        _mine(run, s),
    )
    if ridges is not None:
        ridges.left[:] += left
        ridges.right[:] += right
    if not reached:
        # (the paint does not reach the blade: its level stays, and it lays
        # its film as on a canvas it does not ride on; only its bead, if it
        # skims, has been worked out as it went)
        return _Met(None, None, laid, level, hang) if laid.size else None
    # (the level the bead hangs from moves with the blade's; the flow was
    # given it raised by the stroke's own paint, _slab is not. A blade that
    # does not skim has no bead: its level is given for it, see
    # _blade_riding, and stays so.)
    hang = ends if hang is level else hang + (ends - level)
    return _Met(None, laid, None, ends, hang)


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
    """What a blade met as it dragged the wet paint under it along (the gaps
    under it, on the solid surface alone), or what it laid as it went
    (riding on wet paint), and how high it ends the step (see
    :func:`_drag_film`)."""

    gaps: np.ndarray | None
    laid: np.ndarray | None
    beaded: np.ndarray | None  # (what its bead alone left as it went)
    level: np.ndarray
    hang: np.ndarray


def _own_paint(run: _Run, s: _Step):
    """The stroke's own paint over each pixel of the step's part of the
    canvas: on top, or in an earlier stroke's top layer (see
    :class:`_Mine`)."""
    canvas, at = run.canvas, s.sl
    top = canvas.top[..., IV][at]
    own = canvas.top_id[at] == run.stroke_id
    if run.mine is None:
        return np.where(own, top, 0.0)
    return np.where(own, top, np.minimum(_mine(run, s), top))


_NO_MINE = np.zeros((0, 0), np.float32)
_NO_COAT = np.zeros((0, 0))


class _Mine:
    """The stroke's own paint that lies in an earlier stroke's top layer:
    how much on each pixel, over all the stroke can reach of the canvas and
    of what lies past its edge as far as anything is kept there (from
    (``y0``, ``x0``) of the canvas).

    Paint a blade lays on a pixel that holds two wet layers joins the top
    one if it is much the same paint (white on white over purple, see
    _engine.deposit), and that layer keeps the earlier stroke's id: so the
    stroke's own paint there passed for the earlier stroke's. The blade
    rested on it, the flow dragged it, and the bead of a skimming blade
    took it for the surface it touches: a knife loaded with 8 skimming at
    pressure 0.03 over an earlier pull of the same white on wet dark laid
    31% more at a stroke's own steps than in steps of half a pixel, where
    it came to rest on its own paint a little at each step (murex-dq0).
    With this the blade rests on what lay there before it (_blade_rest),
    glides on what it has laid there as on a film of its own on top, and
    leaves it where it is (_engine._contact_speed, _shares_moved)."""

    def __init__(self, run: _Run):
        canvas: Any = getattr(run.canvas, "on", run.canvas)  # (a stage's)
        y0, y1, x0, x1 = _kept_band(run._reach(), canvas.height, canvas.width)
        self.y0, self.x0 = y0, x0
        self.plane = np.zeros((max(y1 - y0, 0), max(x1 - x0, 0)), np.float32)

    def _part(self, run: _Run, win: eng.Window):
        """Where the part of the plane lies that a step's part ``win`` of
        what the stroke is painted on holds any of: in the plane, and in
        that part (two slices each)."""
        oy, ox = run.at
        y0, x0 = win.cy0 + oy - self.y0, win.cx0 + ox - self.x0
        h, w = self.plane.shape
        a0, b0 = min(max(y0, 0), h), min(max(x0, 0), w)
        a1, b1 = min(max(y0 + win.ch, a0), h), min(max(x0 + win.cw, b0), w)
        return (
            (slice(a0, a1), slice(b0, b1)),
            (slice(a0 - y0, a1 - y0), slice(b0 - x0, b1 - x0)),
        )

    def over(self, run: _Run, win: eng.Window) -> np.ndarray:
        """The plane over a step's part ``win`` of what the stroke is
        painted on (nothing where the plane does not reach)."""
        there, here = self._part(run, win)
        out = np.zeros((win.ch, win.cw), np.float32)
        out[here] = self.plane[there]
        return out

    def add(self, run: _Run, win: eng.Window, more: np.ndarray) -> None:
        """Add ``more`` (over the step's part ``win``) to the plane."""
        there, here = self._part(run, win)
        self.plane[there] += more[here]


def _mine(run: _Run, s: _Step) -> np.ndarray:
    """The stroke's own paint in an earlier stroke's top layer over each
    pixel of the step's part of the canvas (see :class:`_Mine`); empty if
    there is none anywhere."""
    if run.mine is None:
        return _NO_MINE
    if s.mine is None:
        s.mine = run.mine.over(run, s.st.win)
    return s.mine


def _fill_under_blade(
    run: _Run,
    s: _Step,
    level,
    ride,
    hang,
    area: float,
    met=(None, None, None),
    less=None,
) -> None:
    """6) The blade fills the space under it, up to its ``level``, from the
    film of paint it carries (its bead hanging from ``hang`` if it skims: see
    :func:`_slab`), and presses some out at its ends
    (:func:`_press_out_ends`). If that makes three wet layers, the
    two most alike merge (white laid on white-over-purple joins the white; a
    new colour stays on top of the others: what joins an earlier stroke's
    layer so is noted, see :class:`_Mine`). ``met``: the space under it
    over its part of the canvas as it met it, where it dragged the wet
    paint there along, or what it laid as it went, where it rode on that
    paint (see :func:`_drag_film`). ``less``: see :func:`_film`."""
    if not (run.brush.tip[:, IV].sum() > 0 and run.bt.deposits):
        return
    st, wsl = s.st, s.wsl
    d, skim = _slab(run, s, level, hang, area, met, less)
    if run.bt.clumps == 0:
        _press_out_ends(run, s, ride, skim)
    joined = np.zeros((st.win.ch, st.win.cw), np.float32)
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
        extra=np.empty(0),
        joined=joined,
    )
    if joined.any():
        if run.mine is None:
            run.mine = _Mine(run)
        run.mine.add(run, st.win, joined)
        s.mine = None


def _end_press(ride, s: _Step, skim: float):
    """How much paint the blade presses out near its ends over each pixel of
    the step's part of the canvas (see :func:`_press_out_ends`)."""
    st = s.st
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
    )


def _slab(
    run: _Run, s: _Step, level, hang, area: float, met=(None, None, None), less=None
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
    expo_c = s.expo[s.wsl]
    gaps, laid, beaded_as_met = met
    film = _film(run, s, area, less)  # (the paint on the blade as it is now)
    fill, skim, n = _fill_share(run, s)
    # The gap between the blade and the surface, as far as its film reaches, filled
    # by the share k_fill gives over this step's share of a pass (see
    # _engine.blade_slab). Where the blade dragged the wet paint under it
    # along in this step, the gap, and the surface, as it met them (gaps);
    # where it rode on that paint, what it laid as it went (laid: see
    # _drag_film).
    d, surf = eng.blade_slab(
        canvas.top,
        canvas.und,
        run.relief.floor,
        st.win.cy0,
        st.win.cx0,
        level,
        film,
        fill,
        np.zeros((0, 0, 2)) if gaps is None else gaps,
        _NO_COAT if laid is None else laid,
    )
    if skim > 0 and run.bt.clumps == 0:
        bead = np.minimum(film, _KNIFE_BEAD_HEIGHT)
        # The bead runs along the blade's edge: it passes over a pixel once
        # in a pass, and touches what was there before the stroke, as the
        # blade rests on it (see _blade_rest), not the paint it has just
        # left there. (Touching that too, it caught the more the more it
        # had laid, and laid the more the more steps the pass was cut
        # into: a tenth more in steps of 2 px rather than 8; murex-86z.)
        surf = surf - _own_paint(run, s)
        touch = np.clip((surf - (hang - bead)) / np.maximum(bead, 1e-6), 0.0, 1.0)
        touch = touch * _bead_streaks(run, s)
        caught = touch**_KNIFE_CATCH
        # (at the lightest touch the bead is a roll, which lays where the
        # stroke has it lay: see _Roll)
        roll = _rolled(run, s)
        if roll is not None:
            caught = np.maximum(roll[1] * caught, roll[0] * _roll_thin(film))
        # the bead leaves paint wherever it passes, in proportion to how
        # much of a pass this step is (for the same reason)
        pass_bead = n * (1.0 - np.exp(-4.0 / n))
        beaded = skim * _KNIFE_BEAD * pass_bead * bead * caught * expo_c
        if laid is not None:
            # (where the blade rode on wet paint, what its bead left as it
            # went is laid with its film: see _drag_film)
            beaded = np.where(laid >= 0, 0.0, beaded)
        elif beaded_as_met is not None:
            beaded = np.where(beaded_as_met >= 0, beaded_as_met, beaded)
        d += beaded
    return d, skim


def _bead_streaks(run: _Run, s: _Step):
    """Where the bead on a skimming blade's edge catches, over each pixel
    of the step's part of the canvas (0 to 1): the bead is uneven and the
    paint below still follows the threads of the canvas, so that, barely
    touching, it catches in streaks along the blade's nicks and on the
    thread tops, the fewer the lighter the touch."""
    grain = 0.55 * s.hair[s.wsl] + 0.45 * run.relief.tooth[s.sl]
    thr = _KNIFE_TOUCH - 2.2 * s.st.hold.p
    return smoothstep(thr - 0.1, thr + 0.1, grain)


def _bead_coat(run: _Run, s: _Step, film):
    """What the bead on a skimming blade's edge leaves over each pixel in
    this step where it is pressed flat against the surface (see
    :func:`_slab`), the ``film`` on the blade being what it is; empty if the
    blade does not skim. And, where the bead is a roll (see :class:`_Roll`),
    what the roll leaves over the step and the share of the first that is
    left there; both empty for a stroke with no roll."""
    _fill, skim, n = _fill_share(run, s)
    if not (skim > 0 and run.bt.clumps == 0):
        return _NO_COAT, _NO_COAT, _NO_COAT
    bead = np.minimum(film, _KNIFE_BEAD_HEIGHT)
    pass_bead = n * (1.0 - np.exp(-4.0 / n))
    streaks = _bead_streaks(run, s) ** _KNIFE_CATCH
    coat = skim * _KNIFE_BEAD * pass_bead * bead * streaks * s.expo[s.wsl]
    roll = _rolled(run, s)
    if roll is None:
        return coat, _NO_COAT, _NO_COAT
    whole = skim * _KNIFE_BEAD * pass_bead * bead * s.expo[s.wsl]
    return coat, whole * roll[0] * _roll_thin(film), np.ascontiguousarray(roll[1])


def _roll_thin(film):
    """How much of its sheet the roll of a blade with ``film`` on it leaves
    (0 to 1; see :class:`_Roll` and _ROLL_FILM)."""
    return np.minimum(film / _ROLL_FILM, 1.0) ** _KNIFE_CATCH


def _fill_share(run: _Run, s: _Step) -> tuple[Any, float, Any]:
    """The share of the gap under the blade that the step fills over each
    pixel (see :func:`_slab`), how much the blade skims (0: not at all),
    and, if it skims, how long it is along the stroke over each pixel, in
    lengths of _KNIFE_SKIM_PX (else 1)."""
    if s.fill is not None:
        return s.fill
    st = s.st
    p, wsl = st.hold.p, s.wsl
    expo_c = s.expo[wsl]
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
    s.fill = (1.0 - np.exp(-k_fill * expo_c), skim, n)
    return s.fill


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

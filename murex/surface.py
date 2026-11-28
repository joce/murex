"""The surface: what lies on a paper, whichever medium laid it, and its clock.

This is the shared state of ``docs/aquarelle/design.md`` (layer 4), in its
first step (``murex-cjx.2``): a paper (its tooth and its maps, at the
surface's scale) and the water on it, standing on the paper and held in its
fibres, which soaks in and evaporates as the clock runs, until the sheet is
dry. Water does not yet flow across the sheet, nor wick from pixel to pixel,
and nothing carries pigment: the fluid engine, the wet brush and the
rendering of water are the next step (``murex-cjx.3``). Until then
:meth:`Surface.lay_water` stands in for a brush.

Sizes are in millimetres, times in seconds; a depth of water is in
millimetres (of water over the pixel), a volume in microlitres (mm3).

The numbers here come from the references in ``docs/aquarelle/references.md``,
each named by its key; the rest are estimates, and say so.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ._rounding import whole_ceil
from .paper import PX_PER_MM, Paper

__all__ = ["Air", "Surface"]

#: Standard atmospheric pressure, kPa: the pressure the humidity ratio of the
#: air is worked out at (the standard atmosphere).
ATMOSPHERE = 101.325
#: The ratio of the molar masses of water and of dry air (18.015 / 28.965):
#: a humidity ratio (kg of water per kg of dry air) from a vapour pressure.
WATER_IN_AIR = 0.622
#: The saturation vapour pressure of water over a liquid surface, the Magnus
#: form: MAGNUS_P * exp(MAGNUS_A * T / (T + MAGNUS_B)), kPa, T in degrees C.
#: (alduchov1996, Table II: of its fits over water, the one nearest the
#: three standard formulations from -40 to 50 C; 6.1094 hPa, 17.625,
#: 243.04 C. With it, etoolbox_evap's worked example comes out within 0.6%
#: in its humidity ratios, 0.014662
#: for 0.014659 at 20 C and 0.009858 for 0.0098 at 25 C and 50%, and within
#: 1.4% in its rate, 0.1657 kg/(m2 h) for 0.168: a test checks.)
MAGNUS_P = 0.61094
MAGNUS_A = 17.625
MAGNUS_B = 243.04
#: How fast water evaporates from a free surface, per unit of the humidity
#: ratio it lacks: (EVAPORATION_STILL + EVAPORATION_WIND * v) kg/(m2 h), v
#: the speed of the air over it in m/s (etoolbox_evap, Eq. 1; an empirical
#: formula for a pool: an estimate for a film on paper). A kilogram over a
#: square metre is a millimetre of water (its density taken as 1000 kg/m3;
#: 998 at 25 C, iapws_water). The fibres lose their water at this rate too,
#: to the last of it (an estimate: a real paper dries more slowly as it
#: dries, its falling-rate stage).
EVAPORATION_STILL = 25.0
EVAPORATION_WIND = 19.0
#: The Lucas-Washburn coefficient of water into an unsized paper, mm/s**0.5:
#: the front of the water is this far in at 1 s, and goes as the square root
#: of the time (das2019: 0.38 cm/s**0.5, Whatman grade 1 filter paper; the
#: law as walji2016 Eq. 1 and krainer2018 Eqn 1 have it). Taken for every
#: paper (an estimate: their pores are alike, 2.6 to 4.9 um in krainer2018).
WICKING = 3.8
#: Sizing acts through the contact angle (krainer2018). In Lucas-Washburn
#: the square of the distance goes as its cosine (walji2016 Eq. 1), so the
#: square of the coefficient is multiplied by the cosine of an apparent
#: angle: 1 on an unsized paper, SIZED on one sized through, and
#: SIZED ** sizing between. Both SIZED and that ramp in the logarithm are
#: estimates: no coefficient for a sized paper was found (references.md),
#: only that a drop sits on gonzalez2019's watercolour paper and does not
#: soak in quickly. With them, the fibres of the presets fill (water
#: standing over them) in: HOT_PRESSED 140 s, COLD_PRESSED 83 s, ROUGH
#: 117 s, the default paper 0.22 s, XUAN 0.44 ms.
SIZED = 1e-4
#: The longest time step of a wait, s. Within a step the water soaks in
#: first, then evaporates: what a step gets wrong is which of the two (on the
#: paper, in its fibres) the evaporation of one step takes, never how much.
STEP = 1.0
#: No more water than this, in mm, is no water: far below any depth laid
#: (a wash is tenths of a millimetre) and far above what rounding leaves.
DRY = 1e-9
#: :meth:`Surface.dry` waits this much longer (as a share) than the wettest
#: pixel takes, so that rounding leaves no water anywhere.
DRY_MARGIN = 1e-9
#: The deepest water a pixel may hold, mm: a metre, far deeper than any
#: wash, and shallow enough that it dries in a number of steps that ends.
DEEPEST = 1000.0


@dataclass(frozen=True)
class Air:
    """The air over a surface: how fast water evaporates from it.

    Parameters
    ----------
    humidity:
        Relative humidity, 0..1.
    temperature:
        Of the air, and of the water, in degrees C (0 to 50). (The water is
        taken to be as warm as the air: an estimate; evaporation cools it.)
    speed:
        Of the air over the sheet, m/s: 0 in a still room, a few under a
        hair dryer.
    """

    humidity: float = 0.5
    temperature: float = 20.0
    speed: float = 0.0

    def __post_init__(self):
        if not 0.0 <= self.humidity <= 1.0:
            raise ValueError(f"humidity must be between 0 and 1, got {self.humidity!r}")
        if not 0.0 <= self.temperature <= 50.0:
            raise ValueError(
                f"temperature must be between 0 and 50 C, got {self.temperature!r}"
            )
        if not (math.isfinite(self.speed) and self.speed >= 0.0):
            raise ValueError(f"speed must be 0 or more, got {self.speed!r}")

    @property
    def rate(self) -> float:
        """How fast water evaporates from a wet surface, mm/s."""
        return evaporation(
            self.temperature, self.temperature, self.humidity, self.speed
        )


def humidity_ratio(temperature: float, humidity: float = 1.0) -> float:
    """kg of water per kg of dry air, at ``temperature`` (C) and relative
    ``humidity``: by default saturated."""
    p = (
        humidity
        * MAGNUS_P
        * math.exp(MAGNUS_A * temperature / (temperature + MAGNUS_B))
    )
    return WATER_IN_AIR * p / (ATMOSPHERE - p)


def evaporation(water: float, air: float, humidity: float, speed: float) -> float:
    """How fast water at ``water`` C evaporates into air at ``air`` C of
    relative ``humidity``, moving at ``speed`` m/s, in mm/s (etoolbox_evap,
    Eq. 1). None, rather than condensation, where the air holds more."""
    lacks = humidity_ratio(water) - humidity_ratio(air, humidity)
    per_hour = (EVAPORATION_STILL + EVAPORATION_WIND * speed) * max(lacks, 0.0)
    return per_hour / 3600.0


def steps(seconds: float) -> int:
    """How many steps a wait of ``seconds`` is cut into: as few as keep each
    to :data:`STEP` at most, and one at least. A ratio, so it does not hang
    on the last bit of ``seconds`` (``whole_ceil``)."""
    return max(whole_ceil(seconds / STEP), 1)


class Surface:
    """A sheet of paper, and the water on it (step 1 of the wet media).

    Parameters
    ----------
    width, height:
        Size in pixels.
    paper:
        A :class:`murex.Paper`, e.g. ``papers.COLD_PRESSED``. Default: a
        drawing paper.
    px_per_mm:
        The scale: pixels to a millimetre (4: a 1200 by 800 surface is 30 by
        20 cm). The paper's sizes, given in millimetres, are drawn at it.
    seed:
        Random seed of the paper's tooth (``np.random.default_rng(seed)``, as
        fusain's ``Sheet`` draws it) and of its varying maps, which draw from
        a generator of their own (:func:`murex.paper.maps_rng`).
    air:
        The :class:`Air` over the sheet (``surface.air`` may be changed
        between waits). Default: a still room at 20 C and 50%.

    Per pixel it holds the paper's ``tooth`` (0 valley to 1 peak) and
    ``maps`` (:class:`murex.paper.PaperMaps`), and two depths of water, in
    mm: ``standing`` on the paper and ``wet``, in its fibres. They are
    float64, unlike the rest: a short wait evaporates less than a float32
    depth can tell, and the water would stall there while the books said it
    had gone. Its clock, ``time``, is in seconds.

    Water stays on the pixel it was laid on: it soaks into the fibres there
    and evaporates from there. Flow across the sheet, wicking from pixel to
    pixel along the fibres (``fibre_angle``, ``fibre_ratio``), pigment, the
    wet brush and how water looks are step 2 (``murex-cjx.3``).
    """

    def __init__(
        self,
        width: int,
        height: int,
        paper: Paper | None = None,
        px_per_mm: float = PX_PER_MM,
        seed: int | None = None,
        air: Air | None = None,
    ):
        self.width, self.height = _size("width", width), _size("height", height)
        if not (math.isfinite(px_per_mm) and px_per_mm > 0):
            raise ValueError(f"px_per_mm must be a number above 0, got {px_per_mm!r}")
        self.paper = Paper() if paper is None else paper
        self.px_per_mm = float(px_per_mm)
        self.air = Air() if air is None else air
        H, W = self.height, self.width
        sequence = np.random.SeedSequence(seed)
        self._rng = np.random.default_rng(sequence)
        self.tooth = self.paper.tooth(H, W, self._rng, px_per_mm=self.px_per_mm)
        self.maps = self.paper.maps(H, W, self.px_per_mm, sequence)
        self.standing = np.zeros((H, W))
        self.wet = np.zeros((H, W))
        self.time = 0.0
        # (the water laid, evaporated and soaked into the fibres, summed over
        # the pixels in mm: each counted from the change in what is stored)
        self._laid = 0.0
        self._evaporated = 0.0
        self._soaked = 0.0

    # -- water --------------------------------------------------------------

    def lay_water(self, depth: float, where: np.ndarray | None = None) -> None:
        """Lay ``depth`` mm of water on the paper: over the whole sheet, or
        under ``where``, an (H, W) mask from 0 to 1 (a share of the depth at
        each pixel; a boolean mask too). It stands on the paper until it
        soaks in or evaporates; laying it takes no time. (A stand-in for a
        brush, until the wet brush of step 2.) Raises ValueError if a pixel
        would then hold more than :data:`DEEPEST` mm."""
        depth = float(depth)
        if not (math.isfinite(depth) and depth >= 0.0):
            raise ValueError(f"depth must be a depth of water in mm, got {depth!r}")
        share = self._share(where)
        old = self.standing
        new = old + depth * share
        if not (np.isfinite(new).all() and (new + self.wet).max() <= DEEPEST):
            raise ValueError(
                f"{depth!r} mm of water more would be deeper than {DEEPEST} mm"
            )
        self._laid += float(np.sum(new - old))
        self.standing[...] = new

    def wait(self, seconds: float) -> None:
        """Let ``seconds`` pass. Water standing on the paper soaks into the
        fibres, as fast as the sizing lets it and until they are full; water
        evaporates at the rate the air sets (:attr:`Air.rate`), from what
        stands on the paper first, then from the fibres. Cut into steps of
        :data:`STEP` at most (:func:`steps`); the totals of water do not
        depend on how a wait is cut, to rounding. (The water stays on the
        pixel it is on: it flows and wicks across the sheet from step 2.)"""
        seconds = float(seconds)
        if not (math.isfinite(seconds) and seconds >= 0.0):
            raise ValueError(f"seconds must be 0 or more, got {seconds!r}")
        box = self._wet_box()
        # (nothing changes where nothing stands to soak in and nothing
        # evaporates: in saturated air, once the water has soaked in)
        if box is not None and (self.air.rate > 0.0 or self.standing.any()):
            count = steps(seconds)
            self._run(box, seconds / count, count)
        self.time += seconds

    def dry(self) -> float:
        """Wait until no water is left (none deeper than :data:`DRY`).
        Returns the seconds waited. Raises ValueError if the air is
        saturated and water is left, which would then never dry. In air
        nearly saturated it takes long: as many steps of :data:`STEP` as the
        wettest pixel takes seconds to dry (99.9% at 0 C: 11 million for a
        millimetre). Step 2's kernels take the place of this loop."""
        left = float(np.max(self.standing + self.wet))
        if left <= DRY:
            return 0.0
        rate = self.air.rate
        if rate <= 0.0:
            raise ValueError("the air is saturated: the water on the sheet never dries")
        # (each pixel loses the same depth in each step, wherever it is
        # held, until it is dry: the wettest is dry after left / rate)
        seconds = left / rate * (1.0 + DRY_MARGIN)
        self.wait(seconds)
        return seconds

    # -- totals, in microlitres ---------------------------------------------

    @property
    def water_laid(self) -> float:
        """The water laid on the sheet, in microlitres."""
        return self._laid / self.px_per_mm**2

    @property
    def water_evaporated(self) -> float:
        """The water that has evaporated from the sheet, in microlitres."""
        return self._evaporated / self.px_per_mm**2

    @property
    def water_soaked(self) -> float:
        """The water that has soaked into the fibres, in microlitres (what
        evaporated from them since included)."""
        return self._soaked / self.px_per_mm**2

    @property
    def water_standing(self) -> float:
        """The water standing on the paper, in microlitres."""
        return float(np.sum(self.standing, dtype=np.float64)) / self.px_per_mm**2

    @property
    def water_held(self) -> float:
        """The water in the paper's fibres, in microlitres."""
        return float(np.sum(self.wet, dtype=np.float64)) / self.px_per_mm**2

    @property
    def water_on_sheet(self) -> float:
        """The water on the sheet, standing and in the fibres, in
        microlitres. With what has evaporated, it is what was laid, to
        rounding."""
        return self.water_standing + self.water_held

    # -- internals ----------------------------------------------------------

    def _share(self, where: np.ndarray | None) -> np.ndarray:
        """``where`` as a share of the sheet, (H, W) float64 from 0 to 1."""
        if where is None:
            return np.ones((self.height, self.width))
        share = np.asarray(where, dtype=np.float64)
        if share.shape != (self.height, self.width):
            raise ValueError(
                f"where must be ({self.height}, {self.width}), the sheet's "
                f"size, not {share.shape}"
            )
        if not (np.isfinite(share).all() and share.min() >= 0 and share.max() <= 1):
            raise ValueError("where must be a share of each pixel, from 0 to 1")
        return share

    def _wet_box(self) -> tuple[slice, slice] | None:
        """The rows and columns that hold any water, or None."""
        wet = (self.standing > 0) | (self.wet > 0)
        rows, cols = np.flatnonzero(wet.any(axis=1)), np.flatnonzero(wet.any(axis=0))
        if rows.size == 0:
            return None
        return slice(rows[0], rows[-1] + 1), slice(cols[0], cols[-1] + 1)

    def _run(self, box: tuple[slice, slice], dt: float, count: int) -> None:
        """``count`` steps of ``dt`` seconds over the pixels of ``box``."""
        standing, wet = self.standing[box].copy(), self.wet[box].copy()
        maps = self.maps
        room = maps.capacity[box].astype(np.float64)
        # (how much the square of the water in the fibres grows in a step
        # while water stands over them: Lucas-Washburn, the front going down
        # into the sheet as the square root of the time, with as much water
        # behind it as the pores hold)
        sizing = maps.sizing[box].astype(np.float64)
        porosity = maps.porosity[box].astype(np.float64)
        soak = (porosity * WICKING) ** 2 * SIZED**sizing * dt
        gone = self.air.rate * dt
        soaked = 0.0
        for _ in range(count):
            # soaks in: no more than stands there, nor than the fibres hold
            reach = np.minimum(np.sqrt(wet * wet + soak), room)
            fuller = wet + np.clip(reach - wet, 0.0, standing)
            moved = fuller - wet  # (what the fibres gained, as stored)
            standing, wet = standing - moved, fuller
            soaked += float(moved.sum())
            # evaporates: from what stands first, then from the fibres
            top = np.minimum(standing, gone)
            standing = standing - top
            below = np.minimum(wet, gone - top)
            wet = wet - below
            if not (moved.any() or top.any() or below.any()):
                break  # (each step after it would be this one again)
        # (what left the sheet is what it held less what it holds, counted
        # from what is stored: the books are exact, to the sum's rounding)
        left = (self.standing[box] - standing) + (self.wet[box] - wet)
        self._evaporated += float(left.sum())
        self._soaked += soaked
        self.standing[box] = standing
        self.wet[box] = wet


def _size(name: str, value) -> int:
    """``value`` as a size in pixels: a whole number above 0."""
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)):
        raise TypeError(f"{name} must be a whole number of pixels, got {value!r}")
    if value <= 0:
        raise ValueError(f"{name} must be above 0, got {value!r}")
    return int(value)

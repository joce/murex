"""Paper: the support every medium lays its matter on. What its tooth is
like, its colour, and what it does with water: how far its size keeps water
on the surface, how much its fibres hold, and which way they run.

Its sizes are in millimetres; a surface works them out in pixels from its
scale (:data:`PX_PER_MM` by default). Every property a surface reads is a
map (:meth:`Paper.maps`): a machine-made paper makes them even; a paper whose
sheet varies (a handmade one, to come) names a generator of its own
(``variation``), which draws from a random generator of its own, never from
the tooth's.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

import numpy as np

from . import noise as nz
from . import spectral as sp
from .filters import box_blur
from .pigment import ColorLike

TEXTURES = ("wove", "laid", "rough", "pebbled", "sanded")
#: How a paper's maps vary across the sheet: ``"even"`` (a machine-made
#: paper: the same everywhere) or ``"cloudy"`` (its thickness, and with it
#: the water its fibres hold, and its sizing vary in clouds, as a handmade
#: sheet's formation does).
VARIATIONS = ("even", "cloudy")

#: The scale a surface has unless it is given another, in pixels per
#: millimetre: a 1200 by 800 picture is then 30 by 20 cm.
PX_PER_MM = 4.0
#: Where the random generator of a paper's varying maps is drawn from: the
#: sheet's seed, under this key of its own, so that the tooth's draws (from
#: the seed itself) do not move whatever the maps draw.
MAPS_KEY = 0x6D617073
#: A cloudy sheet: the clouds are about this many millimetres across, its
#: thickness goes from (1 - x/2) to (1 + x/2) of the paper's, and its sizing
#: as far either side of the paper's by half of :data:`CLOUD_SIZING`
#: (estimates: a handmade sheet's formation was not measured in the register).
CLOUD_SIZE = 5.0
CLOUD_THICKNESS = 0.3
CLOUD_SIZING = 0.2

#: Laid paper: the chain lines are this many laid lines apart.
CHAIN_SPACING = 18.0
#: Pebbled paper: its pits are this many ``grain`` apart, centre to centre
#: (a pit is about a grain across; the rest is the rim between two of them).
PIT_SPACING = 1.3
#: How far a pit may sit from its place in the grid, as a share of the
#: spacing: nearly all the way, so that no rows or columns of pits show.
PIT_SCATTER = 0.9
#: How far the walls of a pit reach in from its rim, as a share of the
#: spacing: its floor is what is further in than that.
PIT_WALL = 0.8
#: The shallowest pit, as a share of the deepest.
PIT_SHALLOWEST = 0.3
#: How far the outline of a pit strays from the straight sides its
#: neighbours would give it, as a share of the spacing.
PIT_STRAY = 0.3
#: Pebbled paper: how much of the height is in the lumps of the rims between
#: the pits, and how much in the fibres over everything, beside a depth of 1
#: for the deepest pit.
PEBBLE_LUMPS = 1.0
PEBBLE_FIBRES = 0.2


@dataclass(frozen=True)
class Paper:
    """A paper. Presets live in :mod:`murex.papers`; change one with
    :meth:`with_` or make your own::

        from murex import Paper, papers
        from murex.fusain import Sheet
        sheet = Sheet(1200, 800, paper=papers.INGRES)
        toned = papers.CARTRIDGE.with_(color="#b9a98c")
        mine = Paper(texture="rough", grain=1.5, depth=1.5, bite=0.7)

    Sizes are in millimetres. (fusain draws at 4 px/mm until it moves onto
    the shared surface: there a grain of 0.75 mm is 3 pixels.)

    Parameters
    ----------
    texture:
        ``"wove"`` (felted fibres, the usual drawing paper), ``"laid"`` (fine
        parallel lines crossed by chain lines, as in Ingres paper),
        ``"rough"`` (the bumps of cold-pressed and rough watercolour paper),
        ``"pebbled"`` (the small irregular pits of a charcoal or pastel
        paper, as if pressed with a felt) or ``"sanded"`` (the sharp grit of
        pastel card).
    grain:
        Size of the tooth in millimetres: the distance between neighbouring
        bumps of a wove paper, the spacing of the laid lines, the size of a
        bump of a rough paper, of a pit of a pebbled one or of a grain of
        grit. On drawing paper a pencil line is two or three grains wide.
    depth:
        How deep the tooth is (0 = flat): how far a tip has to reach to touch
        the valleys, how many layers the paper takes, and how strongly the
        texture shows under a light.
    bite:
        0..1: how abrasive the surface is, how much it takes off a stick that
        touches it. Smooth hot-pressed paper bites little, sanded card a lot.
    give:
        0..1: how much the surface yields under a tip. A thin sheet on a hard
        desk, or a board, gives little; a thick soft paper, or a sheet on a
        pad of others, lets the tip sink in and reach further into the tooth.
    color:
        Colour of the paper.
    name:
        Optional label.
    hold:
        How much the tooth holds for its depth: 1 for a paper; more for a
        sanded card, whose grit grips layer after layer of pastel.
    sizing:
        0..1: how far the size (gelatine, starch, AKD) keeps water on the
        surface. 1 for a hard-sized watercolour paper, on which a wash stands
        for minutes; 0 for xuan or blotting paper, which drinks it at once. It
        acts on how readily water enters the pores (an apparent contact
        angle), not on their size (krainer2018).
    thickness:
        Thickness of the sheet, in millimetres.
    porosity:
        0..1: the share of the sheet that is pores, which water fills. With
        the thickness, it sets how much water the fibres hold when full
        (:attr:`capacity`).
    fibre_angle:
        The direction the fibres run, in degrees (0 = along x, across the
        sheet; 90 = down it): the way water wicks fastest.
    fibre_ratio:
        How much faster water wicks along the fibres than across them, as
        the ratio of the times it takes to reach as far each way (1: no
        direction). On a laboratory paper, 1.3 (walji2016, Whatman 17 CHR,
        "30% faster" along the machine direction).
    variation:
        How the paper's maps vary across the sheet: one of
        :data:`VARIATIONS`. ``"even"`` for a machine-made paper.

    The water's properties change nothing for fusain, which does not read
    them: they are for the shared surface (:class:`murex.Surface`).
    """

    texture: str = "wove"
    grain: float = 0.75
    depth: float = 1.0
    bite: float = 0.5
    give: float = 0.5
    color: ColorLike = "#f3f0e6"
    name: str = "paper"
    hold: float = 1.0
    # (a drawing paper: lightly sized, about 130 g/m2 in 0.18 mm; estimates)
    sizing: float = 0.5
    thickness: float = 0.18
    porosity: float = 0.5
    fibre_angle: float = 0.0
    # (a machine-made paper, as walji2016's: its fibres lie along the machine)
    fibre_ratio: float = 1.3
    variation: str = "even"

    def __post_init__(self):
        if self.texture not in TEXTURES:
            raise ValueError(f"unknown texture {self.texture!r}; use one of {TEXTURES}")
        if self.variation not in VARIATIONS:
            raise ValueError(
                f"unknown variation {self.variation!r}; use one of {VARIATIONS}"
            )
        for field in ("grain", "thickness"):
            if not (math.isfinite(getattr(self, field)) and getattr(self, field) > 0):
                raise ValueError(
                    f"{field} must be a size in millimetres above 0: "
                    f"{getattr(self, field)!r}"
                )
        if not (math.isfinite(self.depth) and self.depth >= 0):
            raise ValueError(f"depth must be 0 (flat) or more, got {self.depth!r}")
        for field in ("bite", "give", "sizing"):
            if not 0.0 <= getattr(self, field) <= 1.0:
                raise ValueError(
                    f"{field} must be between 0 and 1, got {getattr(self, field)!r}"
                )
        if not 0.0 < self.porosity < 1.0:
            raise ValueError(
                f"porosity must be above 0 and below 1, got {self.porosity!r}"
            )
        if not (math.isfinite(self.hold) and self.hold > 0):
            raise ValueError(f"hold must be a number above 0, got {self.hold!r}")
        if not math.isfinite(self.fibre_angle):
            raise ValueError(f"fibre_angle must be finite, got {self.fibre_angle!r}")
        if not (math.isfinite(self.fibre_ratio) and self.fibre_ratio >= 1.0):
            raise ValueError(
                "fibre_ratio must be 1 (no direction) or more, "
                f"got {self.fibre_ratio!r}"
            )
        sp.parse_color(self.color)  # refused here rather than at the first sheet

    def with_(self, **changes) -> Paper:
        """A copy with some fields changed."""
        return replace(self, **changes)

    @property
    def capacity(self) -> float:
        """How much water the fibres hold when full, in millimetres of water
        (its depth over the sheet): the volume of the pores."""
        return self.thickness * self.porosity

    def tooth(
        self,
        h: int,
        w: int,
        rng: np.random.Generator,
        px_per_mm: float = PX_PER_MM,
    ) -> np.ndarray:
        """Height of the surface, (h, w) float32 from 0 (valley) to 1 (peak),
        at ``px_per_mm`` pixels to the millimetre, drawn from ``rng``."""
        _check_scale(px_per_mm)
        make = {
            "wove": _wove,
            "laid": _laid,
            "rough": _rough,
            "pebbled": _pebbled,
            "sanded": _sanded,
        }
        grain = self.grain * px_per_mm
        return _unit(make[self.texture](h, w, grain, rng)).astype(np.float32)

    def reflectance(self) -> np.ndarray:
        """Reflectance spectrum of the bare paper, (N_BANDS,)."""
        return sp.srgb_to_reflectance(self.color)

    def maps(
        self,
        h: int,
        w: int,
        px_per_mm: float = PX_PER_MM,
        seed: int | np.random.SeedSequence | None = None,
    ) -> PaperMaps:
        """What a surface (h, w) reads of the paper at each pixel, at
        ``px_per_mm``: its sizing, the water its fibres hold, the way they
        run and its colour. An even paper's maps are views of one number,
        and draw nothing. A varying one's are drawn from a random generator
        of their own (:func:`maps_rng`), from ``seed``: the sheet's seed,
        whose own draws (the tooth's) they leave as they are."""
        _check_scale(px_per_mm)
        shape = (int(h), int(w))

        def even(value: float) -> np.ndarray:
            return np.broadcast_to(np.float32(value), shape)

        maps = PaperMaps(
            sizing=even(self.sizing),
            capacity=even(self.capacity),
            porosity=even(self.porosity),
            fibre_angle=even(math.radians(self.fibre_angle)),
            fibre_ratio=even(self.fibre_ratio),
            reflectance=np.broadcast_to(
                self.reflectance().astype(np.float32), (*shape, sp.N_BANDS)
            ),
        )
        if self.variation == "even":
            return maps
        return _cloudy(self, maps, px_per_mm, maps_rng(seed))


@dataclass(frozen=True, eq=False)
class PaperMaps:
    """What a surface reads of its paper, per pixel, each (h, w) float32
    unless said: ``sizing`` (0..1), ``capacity`` (the water the fibres hold
    when full, mm), ``porosity`` (0..1), ``fibre_angle`` (the way the fibres
    run, in radians), ``fibre_ratio`` (how much faster water wicks along them
    than across) and ``reflectance`` (h, w, N_BANDS): the bare paper's
    colour. An even map is a read-only view of one number."""

    sizing: np.ndarray
    capacity: np.ndarray
    porosity: np.ndarray
    fibre_angle: np.ndarray
    fibre_ratio: np.ndarray
    reflectance: np.ndarray


def maps_rng(
    seed: int | np.random.SeedSequence | None,
) -> np.random.Generator:
    """The random generator a paper's varying maps draw from, for a sheet of
    ``seed``: the seed's own, under :data:`MAPS_KEY`, independent of the
    generator ``np.random.default_rng(seed)`` its tooth is drawn from."""
    if not isinstance(seed, np.random.SeedSequence):
        seed = np.random.SeedSequence(seed)
    own = np.random.SeedSequence(seed.entropy, spawn_key=(*seed.spawn_key, MAPS_KEY))
    return np.random.default_rng(own)


def _check_scale(px_per_mm: float) -> None:
    if not (math.isfinite(px_per_mm) and px_per_mm > 0):
        raise ValueError(f"px_per_mm must be a number above 0, got {px_per_mm!r}")


def _cloudy(
    paper: Paper, even: PaperMaps, px_per_mm: float, rng: np.random.Generator
) -> PaperMaps:
    """A sheet thicker and thinner in clouds (:data:`CLOUD_SIZE` across),
    so that its fibres hold more water in some and less in others, and
    sized unevenly: what a handmade paper's formation does. The rest even."""
    h, w = even.sizing.shape
    cell = CLOUD_SIZE * px_per_mm
    thick = nz.fractal_noise_2d(h, w, cell, rng, octaves=3) - 0.5
    sized = nz.fractal_noise_2d(h, w, cell, rng, octaves=3) - 0.5
    capacity = paper.capacity * (1.0 + CLOUD_THICKNESS * thick)
    sizing = np.clip(paper.sizing + CLOUD_SIZING * sized, 0.0, 1.0)
    return replace(
        even,
        capacity=capacity.astype(np.float32),
        sizing=sizing.astype(np.float32),
    )


def _unit(a: np.ndarray) -> np.ndarray:
    """``a`` stretched to 0..1 (its rarest half percent at each end clipped)."""
    lo, hi = np.percentile(a, [0.5, 99.5])
    return np.clip((a - lo) / max(hi - lo, 1e-9), 0.0, 1.0)


# (the textures take ``grain`` in pixels: the paper's, at the scale of the
# surface it is drawn for)


def _wove(h, w, grain, rng) -> np.ndarray:
    """Felted fibres: small bumps about ``grain`` apart with short fibres
    running through them, and nothing broader: at the scale of a pencil line
    the sheet is even."""
    bumps = nz.value_noise_2d(h, w, max(0.5 * grain, 1.0), rng)
    fibres = sum(
        nz.aniso_noise(h, w, 3.0 * grain, max(0.5 * grain, 1.0), angle, rng, octaves=1)
        for angle in (20, 80, 140)
    )
    return _no_broad(0.6 * bumps + 0.4 * fibres / 3, grain)


def _no_broad(a: np.ndarray, grain: float) -> np.ndarray:
    """``a`` without what varies over more than a few ``grain``."""
    return a - box_blur(a, max(round(1.5 * grain), 1))


def _laid(h, w, grain, rng) -> np.ndarray:
    """Laid lines ``grain`` apart, running across, slightly wavy; the furrows
    of the chain lines down the sheet every :data:`CHAIN_SPACING` of them;
    fibres over both."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    wander = nz.fractal_noise_2d(h, w, grain * 12, rng, octaves=2) - 0.5
    lines = 0.5 + 0.5 * np.cos(2 * np.pi * (y + wander * grain * 0.8) / grain)
    chain = grain * CHAIN_SPACING
    across = (x + wander * grain) % chain
    chains = np.exp(-0.5 * (np.minimum(across, chain - across) / (0.6 * grain)) ** 2)
    fibres = nz.paper(h, w, grain * 0.8, rng)
    # (the chain wires leave shallow furrows, which a stick skips: on a
    # drawing they show as pale lines down the sheet)
    return 0.3 * lines - 0.1 * chains + 0.5 * fibres


def _rough(h, w, grain, rng) -> np.ndarray:
    bumps = nz.fractal_noise_2d(h, w, grain * 2.0, rng, octaves=3)
    fibres = nz.paper(h, w, grain * 0.5, rng)
    return 0.75 * _unit(bumps) + 0.25 * fibres


def _pebbled(h, w, grain, rng) -> np.ndarray:
    """Pits about ``grain`` across, :data:`PIT_SPACING` of it apart and
    scattered, each with its own depth and its own outline; lumpy rims
    between them; fibres over both. Nothing varies over more than a few pits
    and little over less than one: a tone laid lightly is a net of dark rims
    around pale pits, neither the fine flecks of a wove paper nor the blotches
    of a rough one."""
    cell = PIT_SPACING * grain
    y, x = np.mgrid[0:h, 0:w].astype(np.float64)
    # (the pits are looked up a little beside where they are, differently
    # from place to place: their sides are not straight nor their corners
    # sharp, as those of the cells around scattered points would be)
    y += PIT_STRAY * cell * (2.0 * nz.fractal_noise_2d(h, w, 1.5 * cell, rng, 2) - 1.0)
    x += PIT_STRAY * cell * (2.0 * nz.fractal_noise_2d(h, w, 1.5 * cell, rng, 2) - 1.0)
    inside, deep = _pits(y, x, cell, rng)
    wall = np.clip(inside / (PIT_WALL * cell), 0.0, 1.0)
    pits = deep * (1.0 - (1.0 - wall) ** 2)
    lumps = nz.value_noise_2d(h, w, 0.75 * cell, rng)
    lumps -= box_blur(lumps, max(round(1.5 * cell), 1))
    fibres = nz.paper(h, w, max(0.5 * grain, 1.0), rng)
    return PEBBLE_LUMPS * lumps + PEBBLE_FIBRES * fibres - pits


def _pits(y, x, cell, rng) -> tuple[np.ndarray, np.ndarray]:
    """Pits scattered one to a square of side ``cell``, each owning the
    ground nearer to its centre than to any other. For the points (``y``,
    ``x``): how far inside its pit each is (0 on the rim, growing towards the
    middle; in pixels), and how deep that pit is (:data:`PIT_SHALLOWEST` to
    1)."""
    reach = 2  # squares away a point's two nearest centres can be
    pad = reach + 1  # (one more: the points stray off the sheet a little)
    ny = int(np.ceil(y.shape[0] / cell)) + 2 * pad
    nx = int(np.ceil(y.shape[1] / cell)) + 2 * pad
    centre_y = (np.arange(ny)[:, None] + 0.5 - pad) * cell
    centre_x = (np.arange(nx)[None, :] + 0.5 - pad) * cell
    centre_y = centre_y + PIT_SCATTER * cell * (rng.random((ny, nx)) - 0.5)
    centre_x = centre_x + PIT_SCATTER * cell * (rng.random((ny, nx)) - 0.5)
    depth = 1.0 - (1.0 - PIT_SHALLOWEST) * rng.random((ny, nx))
    row = np.clip(np.floor(y / cell).astype(np.intp) + pad, reach, ny - reach - 1)
    col = np.clip(np.floor(x / cell).astype(np.intp) + pad, reach, nx - reach - 1)
    nearest = np.full(y.shape, np.inf)
    second = np.full(y.shape, np.inf)
    deep = np.zeros(y.shape)
    for dy in range(-reach, reach + 1):
        for dx in range(-reach, reach + 1):
            j, i = row + dy, col + dx
            d = np.hypot(y - centre_y[j, i], x - centre_x[j, i])
            nearer = d < nearest
            second = np.where(nearer, nearest, np.minimum(second, d))
            deep = np.where(nearer, depth[j, i], deep)
            nearest = np.where(nearer, d, nearest)
    return second - nearest, deep


def _sanded(h, w, grain, rng) -> np.ndarray:
    """Grit glued to a card: sharp grains about ``grain`` apart, as many high
    as low, and nothing broader, so that a stick bites all over it."""
    grit = nz.value_noise_2d(h, w, max(0.5 * grain, 1.0), rng)
    finer = nz.value_noise_2d(h, w, max(0.25 * grain, 1.0), rng)
    return _no_broad(0.7 * grit + 0.3 * finer, grain)

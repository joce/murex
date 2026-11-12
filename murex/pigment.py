"""Pigments: absorption and scattering spectra per unit volume."""

from __future__ import annotations

import functools
import math
from collections.abc import Iterable, Sequence

import numpy as np

from . import spectral as sp

#: Scattering per unit thickness of a fully opaque white. A unit-thick layer
#: of it over black reflects ~92%: a normal layer covers well but a thin one
#: lets what is underneath show through.
SCATTER_MAX = 12.0


def _scatter_factor(luminance: float) -> float:
    # Light pigments (titanium white, cadmium yellow) scatter strongly, dark
    # ones (phthalo, black) mostly absorb. Without this, white is far too weak
    # in tints compared with the real thing.
    return 0.1 + 0.9 * luminance


def _check_strength(strength) -> float:
    strength = float(strength)
    if not (math.isfinite(strength) and strength > 0.0):
        raise ValueError(
            f"strength must be a positive number (1 = normal), got {strength!r}"
        )
    return strength


def _check_opacity(opacity) -> float:
    opacity = float(opacity)
    if not math.isfinite(opacity):
        raise ValueError(f"opacity must be a number in 0..1, got {opacity!r}")
    return min(max(opacity, 0.0), 1.0)


class Pigment:
    """A coloured material, described by how it looks.

    Parameters
    ----------
    color:
        How it looks laid at normal thickness on white. ``"#rrggbb"``, a
        float triple in 0..1, or an int triple in 0..255 (see
        :func:`murex.spectral.parse_color`).
    opacity:
        0..1. How strongly it hides what is underneath. 1 = opaque body
        color, ~0.3 = glazing color, 0 = pure dye. Values outside 0..1 are
        clipped. Default 1.
    strength:
        Tinting strength, > 0. 2 means half as much of it gives the same
        shift in a mixture. Default 1.
    name:
        Optional label.

    ``color`` may also be an existing pigment: ``Pigment(pigment, ...)`` is a
    copy, with a new ``name`` if given. ``strength`` then multiplies that
    pigment's own, and ``opacity`` derives it again from its colour with the
    new opacity, keeping its strength. A pigment that was mixed or built from
    optics has no colour to derive from, so it refuses ``opacity``.

    Internally a pigment is a Kubelka-Munk material: an absorption spectrum
    ``K`` and a scattering coefficient ``S`` per unit volume. Mixing pigments
    adds those, weighted by volume.
    """

    __slots__ = ("K", "S", "_color", "_strength", "name")

    def __init__(
        self,
        color: ColorLike,
        opacity: float | None = None,
        strength: float | None = None,
        name: str | None = None,
    ):
        if isinstance(color, Pigment):
            self._derive(color, opacity, strength, name)
            return
        self.name = name
        self._from_color(
            color,
            1.0 if opacity is None else _check_opacity(opacity),
            1.0 if strength is None else _check_strength(strength),
        )

    def _from_color(self, color: ColorLike, opacity: float, strength: float) -> None:
        srgb = sp.parse_color(color)
        srgb.flags.writeable = False
        target = sp.linear_rgb_to_reflectance(sp.srgb_to_linear(srgb))
        lum = float(sp.LUMINANCE @ sp.srgb_to_linear(srgb))
        S = SCATTER_MAX * _scatter_factor(lum) * opacity**2
        K = sp.solve_absorption(target, S)
        self.K = K * strength
        self.S = S * strength
        self._color = srgb
        # kept so that Pigment(this, opacity=...) can derive it again
        self._strength: float | None = strength

    def _derive(self, pigment: Pigment, opacity, strength, name) -> None:
        """``Pigment(pigment, ...)``: a copy of ``pigment``, changed as asked."""
        self.name = name or pigment.name
        factor = 1.0 if strength is None else _check_strength(strength)
        if opacity is not None:
            if pigment._strength is None or pigment._color is None:
                raise ValueError(
                    "opacity can only be changed on a pigment made from a colour; "
                    f"{pigment!r} was mixed or built from optics"
                )
            self._from_color(
                pigment._color, _check_opacity(opacity), pigment._strength * factor
            )
            return
        self.K, self.S = pigment.K.copy(), pigment.S
        self._color, self._strength = pigment._color, pigment._strength
        if strength is not None:
            # absorption and scattering scale together
            self.K, self.S = self.K * factor, self.S * factor
            if self._strength is not None:
                # made from a colour: that colour stays its colour
                self._strength *= factor
            else:
                # its colour is how it looks, which the strength changes:
                # worked out again when asked for
                self._color = None

    @classmethod
    def from_optics(cls, K, S, name: str | None = None) -> Pigment:
        """Build a pigment directly from absorption spectrum K (per band,
        sampled at :data:`murex.spectral.WAVELENGTHS`) and scattering S
        (scalar), both per unit volume. Handy for measured pigment data."""
        p = cls.__new__(cls)
        p.K = np.asarray(K, dtype=np.float64).copy()
        p.S = float(S)
        p.name = name
        p._color = None
        p._strength = None
        return p

    @classmethod
    def mix(
        cls,
        *parts: ColorLike | tuple[ColorLike, float],
        name: str | None = None,
    ) -> Pigment:
        """Physically mix pigments.

        ``Pigment.mix((ultramarine, 1), (white, 3))`` mixes one part
        ultramarine with three parts white, by volume. Bare pigments (or
        colours) count as one part each. Parts must not be negative.
        """
        K = np.zeros(sp.N_BANDS)
        S = 0.0
        total = 0.0
        for part in parts:
            pigment, vol = _split_part(part)
            pigment = as_pigment(pigment)
            K += vol * pigment.K
            S += vol * pigment.S
            total += vol
        if total <= 0:
            raise ValueError("mix needs a positive total volume")
        return cls.from_optics(K / total, S / total, name=name)

    def reflectance(
        self, thickness: float = 1.0, over: ColorLike = "#ffffff"
    ) -> np.ndarray:
        """Reflectance spectrum of a layer of this pigment over a ground color
        (any color form, or a reflectance spectrum)."""
        is_spectrum = isinstance(over, np.ndarray) and over.shape[-1] == sp.N_BANDS
        ground = over if is_spectrum else sp.srgb_to_reflectance(over)
        return sp.km_layer(self.K * thickness, self.S * thickness, ground)

    def appearance(
        self, thickness: float = 1.0, over: ColorLike = "#ffffff"
    ) -> np.ndarray:
        """sRGB color (0..1) of a layer of this pigment over a ground color."""
        return sp.reflectance_to_srgb(self.reflectance(thickness, over))

    @property
    def color(self) -> np.ndarray:
        """sRGB color at unit thickness on white."""
        if self._color is None:
            self._color = self.appearance()
            self._color.flags.writeable = False
        # read-only: the pigment's optics were derived from it
        return self._color

    @property
    def masstone(self) -> np.ndarray:
        """sRGB color of the pigment infinitely thick."""
        return sp.reflectance_to_srgb(sp.km_opaque(self.K, self.S))

    @property
    def hex(self) -> str:
        return sp.to_hex(self.color)

    def __repr__(self) -> str:
        label = f"{self.name!r}, " if self.name else ""
        return f"Pigment({label}{self.hex}, S={self.S:.2f})"


# (Defined after Pigment so that it holds the class itself, not its name.)
ColorLike = str | Sequence[float] | np.ndarray | Pigment


def _split_part(part) -> tuple[ColorLike, float]:
    """A part of a :meth:`Pigment.mix`: ``(pigment or colour, parts)``, or a
    bare pigment or colour for one part."""
    is_pair = (
        isinstance(part, (tuple, list))
        and len(part) == 2
        and not isinstance(part[0], (int, float, np.number))
    )
    if not is_pair:
        return part, 1.0
    pigment, vol = part
    try:
        vol = float(vol)
    except (TypeError, ValueError):
        raise TypeError(
            f"mix parts are (pigment, parts) with parts a number, got {part!r}"
        ) from None
    if not (math.isfinite(vol) and vol >= 0.0):
        raise ValueError(
            f"mix parts must be a non-negative number of parts, got {vol!r}"
        )
    return pigment, vol


def as_pigment(p: ColorLike) -> Pigment:
    """``p`` if it is a pigment, else a new opaque pigment of exactly that
    colour.

    The last 1024 colours asked for are remembered, so asking again for one
    costs microseconds. A colour not seen before means fitting a spectrum,
    about a millisecond.
    """
    if isinstance(p, Pigment):
        return p
    # Built once per colour, then copied, so that changing the pigment handed
    # out cannot change the next one.
    key = p if isinstance(p, str) else tuple(sp.parse_color(p).tolist())
    return Pigment(_cached_pigment(key))


@functools.lru_cache(maxsize=1024)
def _cached_pigment(key: str | tuple[float, ...]) -> Pigment:
    return Pigment(key)


def mix_colors(
    colors: Iterable[ColorLike], weights: Iterable[float] | None = None
) -> str:
    """Quick helper: hex color of a mix of plain colors or pigments."""
    colors = list(colors)
    weights = [1.0] * len(colors) if weights is None else list(weights)
    return Pigment.mix(
        *[(as_pigment(c), w) for c, w in zip(colors, weights, strict=True)]
    ).hex

"""Paints: a pigment (absorption and scattering spectra per unit volume) with
a body, which says how the paint behaves under the tool."""

from __future__ import annotations

import functools

import numpy as np

from .. import spectral as sp
from ..pigment import (
    SCATTER_MAX,
    ColorLike,
    Pigment,
    _check_strength,
    _split_part,
    mix_colors,
)

__all__ = [
    "DEFAULT_BODY",
    "SCATTER_MAX",
    "ColorLike",
    "Paint",
    "as_paint",
    "mix_colors",
]

#: Body (stiffness) of paint straight from the tube.
DEFAULT_BODY = 0.7


def _check_body(body) -> float:
    body = float(body)
    if not 0.0 <= body <= 1.0:
        raise ValueError("body must be between 0 (fluid) and 1 (very stiff)")
    return body


class Paint(Pigment):
    """A paint, described by how it looks and how it behaves.

    Parameters
    ----------
    color:
        How the paint looks brushed out at normal thickness on white canvas.
        ``"#rrggbb"``, a float triple in 0..1, or an int triple in 0..255 (a
        triple with a component of 2 or more is on the 0..255 scale; one
        whose largest is between 1 and 2 is refused: see
        :func:`murex.spectral.parse_color`).
    opacity:
        0..1: how well it hides what is underneath. 1 = fully opaque body
        color (cadmiums, titanium white), ~0.3 = glazing color (alizarin,
        phthalo), 0 = pure dye. Values outside 0..1 are clipped. Default 1.
    strength:
        Tinting strength, > 0. 2 means half as much of this paint gives the
        same shift in a mixture (phthalo blue is a famously strong tinter).
        Default 1.
    name:
        Optional label.
    body:
        0..1: how stiff the paint is. Tube oil paint (~0.7) holds the marks
        of the brush or knife: ridges, peaks, bristle grooves. Paint thinned
        with medium (low body) flows and levels out smooth; impasto medium or
        cold wax (body 1) holds sharp peaks. Stiff paint also stacks up
        thicker when a brush is overloaded.

    ``color`` may also be an existing paint: ``Paint(paint, ...)`` is a copy,
    with a new ``name`` or ``body`` if given. ``strength`` then multiplies
    that paint's own (``Paint(PHTHALO_BLUE, strength=0.5)`` is a phthalo half
    as strong), and ``opacity`` re-derives it from its colour with the new
    opacity, keeping its strength. A paint mixed on the palette or built from
    optics has no colour to re-derive from, so it refuses ``opacity``: mix
    it with :data:`~huile.palette.MEDIUM` to make it more transparent. A
    :class:`murex.Pigment` that is no paint is taken the same way, with the
    body of paint from the tube unless ``body`` is given.

    A paint is a :class:`murex.Pigment`: an absorption spectrum ``K`` and a
    scattering coefficient ``S`` per unit volume. Mixing paints adds those,
    which is why the mixtures look like real paint mixtures.
    """

    __slots__ = ("body",)

    def __setstate__(self, state) -> None:
        # Paints pickled before ``_strength`` existed lack it: they are read as
        # paints with no colour to derive them again from.
        self._strength = None
        attributes, slots = state if isinstance(state, tuple) else (state, None)
        for mapping in (attributes, slots):
            for key, value in (mapping or {}).items():
                setattr(self, key, value)

    def __init__(
        self,
        color: ColorLike,
        opacity: float | None = None,
        strength: float | None = None,
        name: str | None = None,
        body: float | None = None,
    ):
        own = color.body if isinstance(color, Paint) else DEFAULT_BODY
        self.body = own if body is None else _check_body(body)
        if isinstance(color, Pigment):
            self._refuse_opacity(color, opacity, strength)
        super().__init__(color, opacity, strength, name)

    @staticmethod
    def _refuse_opacity(paint: Pigment, opacity, strength) -> None:
        """What :class:`murex.Pigment` refuses too, said as a painter is told
        it (a bad ``strength`` is still what is refused first)."""
        if strength is not None:
            _check_strength(strength)
        if opacity is not None and (paint._strength is None or paint._color is None):
            raise ValueError(
                "opacity can only be changed on a paint made from a colour; "
                f"{paint!r} was mixed, built from optics or unpickled from "
                "an older version (mix it with palette.MEDIUM to make it "
                "more transparent)"
            )

    # ------------------------------------------------------------------
    @classmethod
    def from_optics(
        cls, K, S, name: str | None = None, body: float | None = None
    ) -> Paint:
        """Build a paint directly from absorption spectrum K (per band, sampled
        at :data:`murex.spectral.WAVELENGTHS`) and scattering S (scalar),
        both per unit volume. Handy for measured pigment data."""
        p = super().from_optics(K, S, name)
        assert isinstance(p, Paint)
        p.body = DEFAULT_BODY if body is None else _check_body(body)
        return p

    def with_body(self, body: float) -> Paint:
        """The same paint, stiffer or more fluid."""
        return Paint(self, body=body)

    @classmethod
    def mix(
        cls,
        *parts: ColorLike | tuple[ColorLike, float],
        name: str | None = None,
    ) -> Paint:
        """Physically mix paints on the palette.

        ``Paint.mix((ultramarine, 1), (titanium_white, 3))`` mixes one part
        ultramarine with three parts white, by volume. Bare paints (or
        colours) count as one part each. Parts must not be negative.
        """
        K = np.zeros(sp.N_BANDS)
        S = 0.0
        body = 0.0
        total = 0.0
        for part in parts:
            paint, vol = _split_part(part, "paint")
            paint = as_paint(paint)
            K += vol * paint.K
            S += vol * paint.S
            body += vol * paint.body
            total += vol
        if total <= 0:
            raise ValueError("mix needs a positive total volume")
        return cls.from_optics(K / total, S / total, name=name, body=body / total)


def as_paint(p: ColorLike) -> Paint:
    """``p`` if it is a paint, else a new opaque paint of exactly that colour
    (or, of a :class:`murex.Pigment` that is no paint, a paint of that
    pigment with the body of paint from the tube).

    The last 1024 colours asked for are remembered, so asking again for one
    (a hex string a stroke is given, say) costs microseconds. A colour not
    seen before means fitting a spectrum, about a millisecond: when painting
    many slightly different colours (sampled from a reference, say), make a
    :class:`Paint` per step of colour you care about and reuse it, as
    ``examples/huile/_studies.py`` does.
    """
    if isinstance(p, Paint):
        return p
    if isinstance(p, Pigment):
        return Paint(p)
    # The paint is built once per colour (it means fitting a spectrum, about
    # a millisecond, and a stroke given a colour string asks for it every
    # time), then copied, so that changing the paint handed out cannot change
    # the next one.
    key = p if isinstance(p, str) else tuple(sp.parse_color(p).tolist())
    return Paint(_cached_paint(key))


@functools.lru_cache(maxsize=1024)
def _cached_paint(key: str | tuple[float, ...]) -> Paint:
    return Paint(key)

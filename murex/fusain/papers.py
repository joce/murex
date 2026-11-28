"""The papers, which every medium shares: :mod:`murex.papers`, under the name
fusain has always given them (``from murex.fusain import papers``).

Only ``ALL`` is fusain's own: the papers it drew on before the wet media's
joined them (all but hot-pressed and xuan), so that what goes through them
(its example of the papers, its thorough fingerprint) stays as it was."""

from __future__ import annotations

from .. import papers as _shared
from ..paper import Paper
from ..papers import (
    BLACK,
    BRISTOL,
    CARTRIDGE,
    CHARCOAL,
    COLD_PRESSED,
    HOT_PRESSED,
    INGRES,
    NEWSPRINT,
    PRINTER,
    ROUGH,
    SANDED,
    TONED_GREY,
    TONED_TAN,
    WATERCOLOUR,
    XUAN,
)

ALL = tuple(paper for paper in _shared.ALL if paper not in (HOT_PRESSED, XUAN))

__all__ = [
    "ALL",
    "BLACK",
    "BRISTOL",
    "CARTRIDGE",
    "CHARCOAL",
    "COLD_PRESSED",
    "HOT_PRESSED",
    "INGRES",
    "NEWSPRINT",
    "PRINTER",
    "ROUGH",
    "SANDED",
    "TONED_GREY",
    "TONED_TAN",
    "WATERCOLOUR",
    "XUAN",
    "Paper",
]

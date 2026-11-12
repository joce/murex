"""murex: what simulations of artists' media share.

Colour as pigments that mix like the real thing (spectral Kubelka-Munk),
stroke paths, noise for textures, reference images and PNG output. Used by
``oilpaint`` and ``fusain``.
"""

from . import filters, noise, reference, spectral
from ._about import __version__
from .pigment import ColorLike, Pigment, as_pigment, mix_colors
from .png import write_png
from .reference import Reference
from .spline import Bezier, CatmullRom, Path, Polyline, Profile

__all__ = [
    "Bezier",
    "CatmullRom",
    "ColorLike",
    "Path",
    "Pigment",
    "Polyline",
    "Profile",
    "Reference",
    "__version__",
    "as_pigment",
    "filters",
    "mix_colors",
    "noise",
    "reference",
    "spectral",
    "write_png",
]

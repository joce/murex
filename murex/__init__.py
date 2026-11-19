"""murex: simulations of artists' media, and what they share.

Here, what they share: colour as pigments that mix like the real thing
(spectral Kubelka-Munk), stroke paths, noise for textures, reference images
and PNG output. The media are subpackages, imported only when asked for:
``murex.fusain`` draws with dry media (pencils, charcoal, pastel, crayon).
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

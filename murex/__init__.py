"""murex: simulations of artists' media, and what they share.

Here, what they share: colour as pigments that mix like the real thing
(spectral Kubelka-Munk), stroke paths, noise for textures, reference images
and PNG output; the papers (``Paper``, ``papers``), and the surface the wet
media will lay their water on (``Surface``, with the ``Air`` over it). The
media are subpackages, imported only when asked for: ``murex.fusain`` draws
with dry media (pencils, charcoal, pastel, crayon) and ``murex.huile`` paints
in oils.
"""

from . import filters, noise, papers, reference, spectral
from ._about import __version__
from .paper import Paper
from .pigment import ColorLike, Pigment, as_pigment, mix_colors
from .png import write_png
from .reference import Reference
from .spline import Bezier, CatmullRom, Path, Polyline, Profile
from .surface import Air, Surface

__all__ = [
    "Air",
    "Bezier",
    "CatmullRom",
    "ColorLike",
    "Paper",
    "Path",
    "Pigment",
    "Polyline",
    "Profile",
    "Reference",
    "Surface",
    "__version__",
    "as_pigment",
    "filters",
    "mix_colors",
    "noise",
    "papers",
    "reference",
    "spectral",
    "write_png",
]

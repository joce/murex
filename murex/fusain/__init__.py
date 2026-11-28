"""fusain: a drawing simulator for dry media (pencils, charcoal, pastel, crayon).

Quick start::

    from murex.fusain import Sheet, papers

    sheet = Sheet(800, 600, paper=papers.INGRES, seed=1)
    sheet.save("paper.png", light=(-0.6, -0.8, 0.5))   # a raking light
"""

from ..paper import Paper
from . import charcoal, conte, crayons, papers, pastels, pencils, pens, tools
from .medium import Medium
from .pens import HeldPen, Pen
from .sheet import Sheet
from .smudger import Smudger
from .stick import Stick
from .tools import Tool

__all__ = [
    "HeldPen",
    "Medium",
    "Paper",
    "Pen",
    "Sheet",
    "Smudger",
    "Stick",
    "Tool",
    "charcoal",
    "conte",
    "crayons",
    "papers",
    "pastels",
    "pencils",
    "pens",
    "tools",
]

"""Papers: ``Sheet(1200, 800, paper=papers.INGRES)``, ``Surface(1200, 800,
paper=papers.COLD_PRESSED)``. Sizes are in millimetres.

What water does in a paper is set by its sizing, its thickness and porosity
(the water its fibres hold when full) and its fibres. Where a number comes
from a reference, its key in ``docs/aquarelle/references.md`` is named;
the rest are estimates. The watercolour papers are 300 g/m2 (140 lb), as
gonzalez2019's Fabriano is; their porosity is what is left of the sheet's
thickness once its weight of cellulose is taken out, at 1.5 g/cm3 (from
walji2016's Table 1: 87 g/m2 in 0.18 mm at a porosity of 67.8%, and 325
g/m2 in 0.70 mm at 69.1%, both give 1.50). Their thicknesses are estimates.
"""

from __future__ import annotations

from .paper import Paper

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
]

#: The everyday drawing paper: a fine, even tooth.
CARTRIDGE = Paper(
    "wove", grain=0.75, depth=1.0, bite=0.5, color="#f3f0e6", name="cartridge"
)
#: Plain office paper: bright white, smooth and thin-toothed. It takes a
#: pencil line well but few layers.
PRINTER = Paper(
    "wove",
    grain=0.375,
    depth=0.4,
    bite=0.4,
    give=0.3,
    color="#fafbfb",
    name="printer paper",
)
#: Smooth board for fine pencil work: hardly any tooth, few layers.
BRISTOL = Paper(
    "wove", grain=0.5, depth=0.25, bite=0.3, give=0.2, color="#f8f7f2", name="bristol"
)
#: Thin, soft and greyish: quick charcoal studies.
NEWSPRINT = Paper(
    "wove",
    grain=0.625,
    depth=0.6,
    bite=0.45,
    give=0.6,
    color="#dcd6c6",
    name="newsprint",
)
#: Laid paper for charcoal and pastel: its lines show through a light tone.
INGRES = Paper("laid", grain=0.75, depth=1.0, bite=0.55, color="#efe9da", name="Ingres")
#: Charcoal paper: a pebbled tooth with no lines to it, on a thick, soft
#: sheet; warm cream. A light tone on it is a net of dark around pale pits.
CHARCOAL = Paper(
    "pebbled",
    grain=1.0,
    depth=0.9,
    bite=0.55,
    give=0.6,
    color="#eee8d7",
    name="charcoal paper",
)
#: Watercolour paper, hot-pressed: smooth, and hard-sized, so that a wash
#: stands on it longest. (Estimates: 0.45 mm, sized through.)
HOT_PRESSED = Paper(
    "wove",
    grain=0.5,
    depth=0.3,
    bite=0.35,
    give=0.5,
    color="#f5f2ea",
    name="hot-pressed",
    sizing=1.0,
    thickness=0.45,
    porosity=0.56,
    # (mould-made: its fibres lie less in one direction than a laboratory
    # paper's, 1.3 in walji2016; not measured on watercolour paper)
    fibre_ratio=1.15,
)
#: Watercolour paper, cold-pressed: a marked, bumpy tooth; hard-sized.
#: (Estimates: 0.55 mm, sizing 0.9.)
COLD_PRESSED = Paper(
    "rough",
    grain=1.25,
    depth=1.3,
    bite=0.6,
    give=0.7,
    color="#f2eee2",
    name="cold-pressed",
    sizing=0.9,
    thickness=0.55,
    porosity=0.64,
    fibre_ratio=1.15,
)
#: Rough watercolour paper: deep hollows that a light stroke skips.
#: (Estimates: 0.65 mm, sizing 0.9.)
ROUGH = Paper(
    "rough",
    grain=2.0,
    depth=1.8,
    bite=0.7,
    give=0.7,
    color="#f1ede0",
    name="rough",
    sizing=0.9,
    thickness=0.65,
    porosity=0.69,
    fibre_ratio=1.15,
)
#: Xuan, the Chinese paper for ink and wash: thin, soft and unsized, it
#: drinks water at once. (Estimates: 30 g/m2 in 0.08 mm, which at 1.5 g/cm3
#: leaves a porosity of 0.75; its long fibres run one way as a laboratory
#: paper's do, walji2016.)
XUAN = Paper(
    "wove",
    grain=0.5,
    depth=0.3,
    bite=0.3,
    give=0.6,
    color="#f3f1ea",
    name="xuan",
    sizing=0.0,
    thickness=0.08,
    porosity=0.75,
    fibre_ratio=1.3,
)
#: Sanded pastel card: sharp grit that takes many layers.
SANDED = Paper(
    "sanded",
    grain=0.5,
    depth=1.2,
    bite=0.95,
    give=0.3,
    color="#d9cdb8",
    name="sanded card",
    hold=2.5,
)
#: Toned papers, to draw the lights as well as the darks.
TONED_GREY = CARTRIDGE.with_(color="#a9a8a4", name="toned grey")
TONED_TAN = CARTRIDGE.with_(color="#c3a680", name="toned tan")
#: Black paper, for pastel and white chalk.
BLACK = CARTRIDGE.with_(color="#1c1b1a", name="black")

#: Every preset.
ALL = (
    CARTRIDGE,
    PRINTER,
    BRISTOL,
    NEWSPRINT,
    INGRES,
    CHARCOAL,
    COLD_PRESSED,
    ROUGH,
    SANDED,
    TONED_GREY,
    TONED_TAN,
    BLACK,
    HOT_PRESSED,
    XUAN,
)
#: The papers for watercolour and ink.
WATERCOLOUR = (HOT_PRESSED, COLD_PRESSED, ROUGH, XUAN)

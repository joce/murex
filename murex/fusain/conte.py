"""Conté crayons and the chalk colours: ``conte.BLACK``, ``conte.SANGUINE``,
``conte.SEPIA``, ``conte.BISTRE``, ``conte.WHITE``, or ``conte.crayon(...)``
of any colour.

A Conté crayon is a thin square stick of pigment and clay with a little
binder, pressed and baked. It is firmer than a hard pastel and than
compressed charcoal: it lays less at a pass than either and keeps a sharp
edge; more of what it lays is held by the paper, so it dusts less, a
finger smudges it less, and an eraser lifts it less cleanly. It is
opaque, with no wax and no sheen. Black, sanguine and white on a toned
paper (``papers.TONED_TAN``, ``papers.TONED_GREY``) are the *trois crayons*
of the old masters' studies: the paper is the middle tone, the red and the
black the shadows, the white the lights.
"""

from __future__ import annotations

from .. import ColorLike, Pigment
from .medium import Medium

#: How soft a Conté crayon is and what share of it the paper holds at once:
#: firmer than a hard pastel (0.6, 0.35) and than a charcoal pencil (0.55,
#: 0.6), and held nearly as well as the pencil. Guessed from how the sticks
#: behave, not measured against real ones.
SOFTNESS = 0.5
BINDING = 0.55
#: A stick is 6 mm square and 63 mm long, and is mostly used broken: half a
#: stick laid flat marks a band five times as wide as its end.
SIDE = 5.0


def crayon(color: ColorLike, name: str | None = None) -> Medium:
    """A Conté crayon of that colour (or of that :class:`murex.Pigment`).
    Drawn with a corner or an end of the stick it makes a firm line; laid
    on its side, an even band that ends where the stick does."""
    pigment = Pigment(color, name=name)
    label = name or f"{pigment.hex} Conté crayon"
    return Medium(
        pigment,
        softness=SOFTNESS,
        binding=BINDING,
        side=SIDE,
        flat_side=True,
        name=label,
    )


#: Black: carbon and clay. Much less dusty than charcoal, and a firm stick
#: fills the tooth less than compressed charcoal does: at a firm pressure
#: (0.7) two layers of it, and four, are still a dark grey with the paper's
#: flecks in it; pressed as hard as it goes, two are nearly black. For the
#: darkest accents and the firm lines.
BLACK = crayon("#1b1a19", "black Conté")
#: Sanguine: red iron oxide, the red chalk of the old masters. A warm
#: brick red that stays light enough to model flesh with.
SANGUINE = crayon("#a8492f", "sanguine")
#: Sepia: a cool, dark brown, for shadows gentler than black.
SEPIA = crayon("#4f3a2c", "sepia")
#: Bistre: a warm, yellowish mid brown, between sanguine and sepia.
BISTRE = crayon("#74532f", "bistre")
#: White chalk: opaque, for the lights on a toned paper, which two firm
#: layers of it cover but for the flecks of the tooth.
WHITE = crayon("#f4f1ea", "white Conté")

#: The classic colours, darkest first.
ALL = (BLACK, SEPIA, BISTRE, SANGUINE, WHITE)

"""Counts worked out from lengths, kept from hanging on a last bit.

How many steps a path is cut into, how many random numbers a texture draws:
such counts are worked out from lengths and widths, and the ratio is often a
whole number in exact arithmetic (a stroke 80 px long in steps of 8 px),
which rounding leaves a hair either side of it. Rounded up or down as it
fell, the count (and with it every random number drawn after it) hung on the
last bit of the input.
"""

from __future__ import annotations

import math

#: A ratio within this much of a whole number counts as that number: far
#: above rounding (such ratios come out within 1e-13 of the whole number)
#: and below any other ratio met in the media's benchmark scenes and tests
#: (the nearest, 6e-6 from one). Compiled kernels cannot read it from here
#: (numba would not see it change): ``spline`` and ``murex.huile._engine``
#: write it out again, and a test checks that the three agree.
WHOLE_SLACK = 1e-6


def whole_floor(x: float) -> int:
    """floor(x) for a count worked out from lengths: a ratio within
    WHOLE_SLACK below a whole number counts as that number."""
    return math.floor(x + WHOLE_SLACK)


def whole_ceil(x: float) -> int:
    """ceil(x) for a count worked out from lengths: a ratio within
    WHOLE_SLACK above a whole number counts as that number."""
    return math.ceil(x - WHOLE_SLACK)

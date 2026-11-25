"""What several of huile's test files share."""

import inspect
from typing import Any

import numpy as np
import pytest

from murex.huile import Brush, Canvas, Paint, brushes, surfaces
from murex.huile import _engine as eng


@pytest.fixture
def by_name():
    """Returns what gives the arguments of a call of one of the engine's
    compiled kernels by their names (a spy put in a kernel's place is handed
    them by position, which a new argument would shift)."""

    def arguments(kernel, args):
        return inspect.signature(kernel.py_func).bind(*args).arguments

    return arguments


@pytest.fixture
def riding_flow():
    """Returns what works out one step of a blade that rides on wet paint
    (_engine.flow_under_riding_blade) from the arguments of
    _engine.flow_under_blade (``args``) and what the blade rides on
    (``ride``): a step of a stroke that was ``phase`` of the way into a
    sub-step of the flow when the step began (see _engine.flow_sub_steps),
    by a blade that fills the share ``fill`` of the gap under it over each
    pixel (None: it has no paint to lay), does not skim, and is far from
    the ends of its mark, where it would spill paint out sideways. Returns
    what the kernel does, and how far into a sub-step the stroke is when
    the step ends."""

    def flow(args, ride, phase=0.0, fill=None):
        level, ds, tx, ty = args[5], args[10], args[11], args[12]
        n_sub, first, phase = eng.flow_sub_steps(phase, ds, tx, ty)
        none = np.zeros((0, 0))
        spill = (np.zeros(level.shape), np.zeros(level.shape), 1e9, 8.0, 0.3)
        every: Any = (
            *args,
            ride,
            (n_sub, first),
            (none if fill is None else fill, none, 0.7, none, none),
            spill,
            np.zeros((0, 0), np.float32),
        )
        out = eng.flow_under_riding_blade(*every)
        return (*out, phase)

    return flow


#: The wet dark of :func:`dark_ground`.
DARK = "#1c1a24"


def _knifed_thin(canvas):
    """A thin wet dark knifed onto ``canvas``: short pulls of a wide knife
    side by side, then one scrape across with a clean blade as long as the
    canvas is high (the pulls alone leave some of the ground bare)."""
    w, h = canvas.width, canvas.height
    knife = brushes.knife("straight", 160, flex=0.5)
    blade: Any = {"angle": 0, "follow_path": False, "pressure": 0.7, "lift": 0.0}
    for x in range(60, w + 120, 120):
        for y in range(10, h - 10, 150):
            loaded = Brush(knife).load(Paint(DARK), 1.5)
            canvas.stroke([(x, y), (x, min(y + 170, h - 10))], brush=loaded, **blade)
    scraper = Brush(brushes.knife("straight", h + 60, flex=0.5))
    canvas.stroke(
        [(10, h / 2), (w - 10, h / 2)],
        brush=scraper,
        angle=90,
        follow_path=False,
        pressure=0.85,
        lift=0.0,
    )


def _brushed_rough(canvas, seed):
    """A wet dark brushed onto ``canvas`` criss-cross with a hog flat: thick
    and uneven, with the furrows and ridges of the bristles."""
    rng = np.random.default_rng(seed)
    for y in range(-10, canvas.height + 30, 20):
        x = -10.0
        while x < canvas.width + 10:
            length, tilt = float(rng.uniform(70, 120)), float(rng.uniform(-14, 14))
            canvas.stroke(
                [(x, y + tilt), (x + length, y - tilt)],
                Paint(DARK),
                amount=5.0,
                brush=brushes.FLAT_HOG,
                pressure=0.55,
            )
            x += 0.8 * length


def _dark_grounds():
    """What :func:`dark_ground` returns."""
    made: dict = {}

    def ground(surface=None, base="knifed", seed=1):
        key = (surface, base, seed)
        if key not in made:
            canvas = Canvas(
                330, 280, seed=seed, surface=surface and getattr(surfaces, surface)
            )
            if base == "knifed":
                _knifed_thin(canvas)
            else:
                _brushed_rough(canvas, 4 + seed)
            made[key] = canvas
        return made[key].copy()

    return ground


@pytest.fixture(scope="session")
def dark_ground():
    """Returns what gives a canvas 330 by 280 px with a wet dark on it, for
    a knife to skim white over: on the default canvas or on a ``surface``
    of huile.surfaces (by its name), the dark ``"knifed"`` thin or
    ``"brushed"`` rough and textured, the canvas made with ``seed``. A
    copy: each is laid once, in its own steps."""
    return _dark_grounds()

"""What several of huile's test files share."""

import inspect
from typing import Any

import numpy as np
import pytest

import murex.huile.stroke as stm
from murex.huile import _engine as eng


@pytest.fixture
def same_textures(monkeypatch):
    """Returns what gives the strokes painted from then on, until the test
    ends, the same textures whatever the steps they are cut into
    (``stroke._MAX_STEP``).

    The wobble of a stroke's width counts its noise in steps, so a stroke
    cut into shorter ones draws more random numbers there, and its blade
    tilts and its bands wander otherwise: as a different seed does, up to a
    fifth more or less paint for a light pull. With this the width does not
    wobble, and as many numbers are drawn in its place whatever the step.
    (A ground the strokes go over is laid before it is called, with the
    textures as they are: a ground kept from one test to the next must not
    depend on which test laid it.)"""

    def match():
        wobble = stm.value_noise_1d

        def no_wobble(n, cell, rng):
            if cell == 1.0:  # (the knife's chatter and lips, counted in px)
                return wobble(n, cell, rng)
            rng.random(8)
            return np.full(n, 0.5)

        monkeypatch.setattr(stm, "value_noise_1d", no_wobble)

    return match


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
            (none if fill is None else fill, none, 0.7),
            spill,
            np.zeros((0, 0), np.float32),
        )
        out = eng.flow_under_riding_blade(*every)
        return (*out, phase)

    return flow

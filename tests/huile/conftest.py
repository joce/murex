"""What several of huile's test files share."""

import inspect

import numpy as np
import pytest

import murex.huile.stroke as stm


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

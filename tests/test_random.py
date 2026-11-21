"""murex's own random draws (``murex._random``): NumPy's, from the same
generator and as NumPy leaves it, and the same numbers on every machine,
which the pins below hold."""

import hashlib

import numpy as np
import pytest

from murex import _random


def digest(array) -> str:
    data = np.ascontiguousarray(array, dtype="<f8").tobytes()
    return hashlib.sha256(data).hexdigest()


def test_numpys_normal_draws_and_the_generator_left_as_numpy_leaves_it():
    for seed in (1, 2, 3):
        ours, numpys = np.random.default_rng(seed), np.random.default_rng(seed)
        drawn = _random.standard_normal(ours, 200_000)
        wanted = numpys.standard_normal(200_000)
        # (all of them, but where the C library's last bit would tip one of
        # the rare draws that take a logarithm or an exponential: on another
        # machine, a few)
        assert (drawn == wanted).mean() > 0.999
        assert ours.random() == numpys.random()
    ours, numpys = np.random.default_rng(4), np.random.default_rng(4)
    drawn = [_random.normal(ours, 0.5, 2.0) for _ in range(500)]
    wanted = [numpys.normal(0.5, 2.0) for _ in range(500)]
    assert np.isclose(drawn, wanted, rtol=1e-15, atol=0).all()
    assert _random.normal(ours, size=(3, 2)).shape == (3, 2)
    assert numpys.normal(size=(3, 2)).shape == (3, 2)
    drawn = [_random.gamma(ours, 2.0, 0.5) for _ in range(5000)]
    wanted = [numpys.gamma(2.0, 0.5) for _ in range(5000)]
    assert np.isclose(drawn, wanted, rtol=1e-15, atol=0).all()
    drawn = [_random.lognormal(ours, 0.0, 0.6) for _ in range(5000)]
    wanted = [numpys.lognormal(0.0, 0.6) for _ in range(5000)]
    assert np.isclose(drawn, wanted, rtol=1e-15, atol=0).all()
    assert ours.random() == numpys.random()


def test_the_tail_and_the_wedges_are_drawn_too():
    drawn = _random.standard_normal(np.random.default_rng(5), 400_000)
    assert abs(drawn.mean()) < 0.01 and abs(drawn.std() - 1.0) < 0.01
    # beyond the last layer of the ziggurat (3.65), and more than one draw
    # out to a large array (the raw numbers asked for at a time run out)
    assert (np.abs(drawn) > 3.7).sum() > 20
    for beyond, share in ((1.0, 0.3173), (2.0, 0.0455), (3.0, 0.0027)):
        assert abs((np.abs(drawn) > beyond).mean() - share) < 0.05 * share


def test_numbers_shapes_and_generators():
    rng = np.random.default_rng(6)
    assert isinstance(_random.normal(rng), float)
    assert isinstance(_random.lognormal(rng), float)
    assert isinstance(_random.gamma(rng, 3.0), float)
    assert _random.normal(rng, size=5).shape == (5,)
    assert _random.standard_normal(rng, 0).shape == (0,)
    with pytest.raises(ValueError):
        _random.gamma(rng, 1.0)
    for kind in (np.random.PCG64DXSM, np.random.Philox, np.random.SFC64):
        ours, numpys = np.random.Generator(kind(7)), np.random.Generator(kind(7))
        drawn = _random.standard_normal(ours, 1000)
        assert (drawn == numpys.standard_normal(1000)).mean() > 0.99
    with pytest.raises(TypeError, match="64-bit"):
        _random.normal(np.random.Generator(np.random.MT19937(1)))


def test_the_same_numbers_everywhere():
    rng = np.random.default_rng(20261121)
    drawn = np.concatenate(
        [
            _random.standard_normal(rng, 100_000),
            [_random.gamma(rng, 2.0, 0.5) for _ in range(500)],
            [_random.lognormal(rng, 0.0, 0.6) for _ in range(500)],
        ]
    )
    assert digest(drawn) == (
        "aef98c8d9c22bfeb6ae2c064847211aaeee0d0355695b354c2a0cb56db9f25aa"
    )

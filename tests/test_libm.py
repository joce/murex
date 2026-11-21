"""murex's own elementary functions (``murex._libm``): as accurate as the C
library, to a unit in the last place (three for ``tanh``), and the same bits on
every machine, which the pins below hold (CI checks them on ARM too)."""

import hashlib
import math
import struct

import numpy as np
import pytest
from numba import njit

from murex import _libm


def _ordinal(x: float) -> int:
    """Doubles in order as integers: adjacent doubles differ by one."""
    i = struct.unpack("<q", struct.pack("<d", x))[0]
    return -(i & 0x7FFFFFFFFFFFFFFF) if i < 0 else i


def ulps(a: float, b: float) -> int:
    if a == b or (math.isnan(a) and math.isnan(b)):
        return 0
    return abs(_ordinal(a) - _ordinal(b))


def digest(array) -> str:
    data = np.ascontiguousarray(array, dtype="<f8").tobytes()
    return hashlib.sha256(data).hexdigest()


@njit(cache=True)
def _expm1_array(x, out):
    for i in range(x.shape[0]):
        out[i] = _libm.expm1(x[i])


def np_expm1(x):
    x = np.asarray(x, dtype=np.float64)
    out = np.empty_like(x)
    _expm1_array(x, out)
    return out


RNG = np.random.default_rng(20261121)
CASES = {
    # name: (ours, the C library's, inputs, the most units in the last place)
    "exp": (
        _libm.np_exp,
        math.exp,
        np.concatenate(
            [
                RNG.uniform(-745.0, 709.7, 20000),
                RNG.uniform(-746.0, -707.0, 5000),  # results below normal
                RNG.uniform(-3.0, 3.0, 20000),
                RNG.uniform(-1e-6, 1e-6, 2000),
            ]
        ),
        1,
    ),
    "expm1": (
        np_expm1,
        math.expm1,
        np.concatenate(
            [
                RNG.uniform(-60.0, 60.0, 20000),
                RNG.uniform(-1e-3, 1e-3, 5000),
                RNG.uniform(-2.0, 2.0, 20000),
            ]
        ),
        1,
    ),
    "tanh": (
        _libm.np_tanh,
        math.tanh,
        np.concatenate(
            [
                RNG.uniform(-25.0, 25.0, 20000),
                RNG.uniform(-1.0, 1.0, 20000),
                RNG.uniform(-1e-5, 1e-5, 2000),
            ]
        ),
        3,  # (fdlibm's tanh: exact nearly always, 3 in 10,000 off by 3)
    ),
    "cbrt": (
        _libm.np_cbrt,
        np.cbrt,
        np.concatenate(
            [RNG.uniform(1e-6, 1.2, 20000), RNG.uniform(-8.0, 8.0, 5000), [1e-310]]
        ),
        1,
    ),
}
for _y in (2.4, 1.0 / 2.4, 1.0 / 3.0, 0.5, 3.0, 1.5):
    CASES[f"power {_y:.4g}"] = (
        lambda x, y=_y: _libm.np_power(x, y),
        lambda x, y=_y: math.pow(x, y),
        np.concatenate(
            [RNG.uniform(1e-4, 1.0, 10000), RNG.uniform(0.04, 1.0, 10000), [1e-300]]
        ),
        1,
    )


@pytest.mark.parametrize("name", CASES)
def test_as_accurate_as_the_c_library(name):
    ours, reference, inputs, most = CASES[name]
    got = ours(inputs)
    worst = max(
        ulps(float(g), float(reference(float(x))))
        for x, g in zip(inputs, got, strict=True)
    )
    assert worst <= most, f"{name}: {worst} units in the last place"


def test_special_values():
    inf, nan = np.inf, np.nan
    assert list(_libm.np_exp(np.array([inf, -inf, 1000.0, -1000.0, 0.0]))) == [
        inf,
        0.0,
        inf,
        0.0,
        1.0,
    ]
    assert np.isnan(_libm.np_exp(nan))
    assert list(_libm.np_tanh(np.array([inf, -inf, 30.0, -30.0, 0.0]))) == [
        1.0,
        -1.0,
        1.0,
        -1.0,
        0.0,
    ]
    assert math.copysign(1.0, _libm.np_tanh(-0.0)) == -1.0
    assert list(np_expm1(np.array([inf, -inf, 0.0]))) == [inf, -1.0, 0.0]
    # power: positive bases only (what the colour science raises)
    assert _libm.np_power(1.0, 2.4) == 1.0
    assert _libm.np_power(0.7, 0.0) == 1.0
    assert all(np.isnan(_libm.np_power(np.array([0.0, -1.0, inf, nan]), 2.4)))
    assert _libm.np_power(4.0, 0.5) == 2.0
    assert list(_libm.np_cbrt(np.array([0.0, 27.0, -8.0, inf, -inf]))) == [
        0.0,
        3.0,
        -2.0,
        inf,
        -inf,
    ]
    assert math.copysign(1.0, _libm.np_cbrt(-0.0)) == -1.0
    assert np.isnan(_libm.np_cbrt(nan))


def test_a_number_in_gives_a_number_out_and_shapes_are_kept():
    assert isinstance(_libm.np_exp(1.0), float)
    assert _libm.np_tanh(np.zeros((2, 3, 4))).shape == (2, 3, 4)
    # a narrower float stays as it was given, as with NumPy's own functions
    x = np.linspace(0.1, 2.0, 50, dtype=np.float32)
    assert _libm.np_tanh(x).dtype == np.float32
    np.testing.assert_array_equal(
        _libm.np_tanh(x), _libm.np_tanh(x.astype(np.float64)).astype(np.float32)
    )
    assert _libm.np_exp(np.arange(3)).dtype == np.float64  # (integers: float64)
    columns = np.arange(12.0).reshape(3, 4)[:, ::2]  # not contiguous
    np.testing.assert_array_equal(
        _libm.np_exp(columns), _libm.np_exp(np.ascontiguousarray(columns))
    )


# What each function gives on a fixed grid, to the bit: the same on every
# machine, which is the point of them.
GRIDS = {
    "exp": (_libm.np_exp, np.linspace(-40.0, 40.0, 4001)),
    "expm1": (np_expm1, np.linspace(-4.0, 4.0, 4001)),
    "tanh": (_libm.np_tanh, np.linspace(-6.0, 6.0, 4001)),
    "cbrt": (_libm.np_cbrt, np.linspace(1e-4, 1.2, 4001)),
    "power 2.4": (lambda x: _libm.np_power(x, 2.4), np.linspace(1e-3, 1.0, 4001)),
    "power 1/2.4": (
        lambda x: _libm.np_power(x, 1.0 / 2.4),
        np.linspace(1e-3, 1.0, 4001),
    ),
}
PINNED = {
    "exp": "fec47515159db554adbaea391f872a7789671f277bb45f987e058a9091f30641",
    "expm1": "4bb356fd9fec1cd868397a204a7976ae15a06d963bd663d67a613d35d6f91936",
    "tanh": "a9d1fe46741fb164bb38b97ae1bf12c8701b678f9dff53455511931098bfa74e",
    "cbrt": "493afc1ae0b78e57cbae884165ecd3ba3a37705993162f206874b34d72c7141f",
    "power 2.4": "9994b5f692d09980fb31f8de53fcc27f297a284ec8bc8d5dec678b874fd94f38",
    "power 1/2.4": "baf806ab6a768c4bb460b8cba96ec7f21653b71bf5cde1a257776f89112f9083",
}


@pytest.mark.parametrize("name", GRIDS)
def test_the_same_bits_everywhere(name):
    function, grid = GRIDS[name]
    assert digest(function(grid)) == PINNED[name]

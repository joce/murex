"""murex's own elementary functions (``murex._libm``): within a unit in the
last place of the exact value (two for ``tanh`` and ``tan``), and the same
bits on every machine, which the pins below hold (CI checks them on ARM and on
Windows too)."""

import hashlib
import math
import re
import struct
from decimal import Decimal, getcontext
from pathlib import Path

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


# The exact values, from decimal arithmetic (correctly rounded at 60 digits,
# the same on every machine): not from the C library or NumPy, which are
# themselves off by a unit now and then, and by different units on another
# machine (NumPy's cbrt on ARM, by three).
getcontext().prec = 60


def _exact_exp(x: float) -> float:
    return float(Decimal(x).exp())


def _exact_expm1(x: float) -> float:
    return float(Decimal(x).exp() - 1)


def _exact_tanh(x: float) -> float:
    e = (2 * Decimal(x)).exp()
    return float((e - 1) / (e + 1))


def _exact_cbrt(x: float) -> float:
    if x == 0.0:
        return x
    return math.copysign(float((Decimal(abs(x)).ln() / 3).exp()), x)


def _exact_power(x: float, y: float) -> float:
    return float((Decimal(x).ln() * Decimal(y)).exp())


def _exact_log(x: float) -> float:
    return float(Decimal(x).ln())


def _exact_log1p(x: float) -> float:
    if abs(x) > 1e-3:
        return float((1 + Decimal(x)).ln())
    total, power, k = Decimal(0), Decimal(x), 1  # (1 + x would lose x's digits)
    while abs(power) > abs(Decimal(x)) * Decimal(10) ** (-getcontext().prec):
        total += power / k
        power *= -Decimal(x)
        k += 1
    return float(total)


def _pi() -> Decimal:
    """pi to the context's precision (the recipe of the decimal module's
    documentation)."""
    getcontext().prec += 2
    three = Decimal(3)
    lasts, t, s, n, na, d, da = Decimal(0), three, three, 1, 0, 0, 24
    while s != lasts:
        lasts = s
        n, na = n + na, na + 8
        d, da = d + da, da + 32
        t = (t * n) / d
        s += t
    getcontext().prec -= 2
    return +s


PI = _pi()


def _sin_cos(x: float) -> tuple[Decimal, Decimal]:
    """The sine and cosine of ``x``, from their series about the nearest
    multiple of pi/2."""
    half = PI / 2
    n = int((Decimal(x) / half).to_integral_value())
    r = Decimal(x) - n * half
    sin, cos = Decimal(0), Decimal(0)
    term, i = Decimal(1), 0
    while True:  # term = r**i / i!
        part = term if i % 4 < 2 else -term
        if i % 2:
            sin += part
        else:
            cos += part
        i += 1
        term = term * r / i
        if i > 1 and abs(term) <= abs(r) * Decimal(10) ** (-getcontext().prec - 5):
            break
    return [(sin, cos), (cos, -sin), (-sin, -cos), (-cos, sin)][n % 4]


def _exact_sin(x: float) -> float:
    return float(_sin_cos(x)[0])


def _exact_cos(x: float) -> float:
    return float(_sin_cos(x)[1])


def _exact_tan(x: float) -> float:
    s, c = _sin_cos(x)
    return float(s / c)


def _atan(x: Decimal) -> Decimal:
    """The arc tangent, its argument halved until small, then its series."""
    if x < 0:
        return -_atan(-x)
    if x > 1:
        return PI / 2 - _atan(1 / x)
    halvings = 0
    while x > Decimal("0.01"):
        x = x / (1 + (1 + x * x).sqrt())
        halvings += 1
    total, power, k = Decimal(0), x, 0
    while abs(power) > Decimal(10) ** (-getcontext().prec - 5):
        total += power / (2 * k + 1) if k % 2 == 0 else -power / (2 * k + 1)
        power *= x * x
        k += 1
    return total * 2**halvings


def _exact_atan2(y: float, x: float) -> float:
    if x > 0:
        return float(_atan(Decimal(y) / Decimal(x)))
    turned = _atan(Decimal(y) / Decimal(x))
    return float(turned + PI if y >= 0 else turned - PI)


RNG = np.random.default_rng(20261121)
CASES = {
    # name: (ours, the exact value, inputs, the most units in the last place)
    "exp": (
        _libm.np_exp,
        _exact_exp,
        np.concatenate(
            [
                RNG.uniform(-745.0, 709.7, 3000),
                RNG.uniform(-746.0, -707.0, 1000),  # results below normal
                RNG.uniform(-3.0, 3.0, 3000),
                RNG.uniform(-1e-6, 1e-6, 500),
            ]
        ),
        1,
    ),
    "expm1": (
        np_expm1,
        _exact_expm1,
        np.concatenate(
            [
                RNG.uniform(-40.0, 40.0, 3000),
                RNG.uniform(-1e-3, 1e-3, 1000),
                RNG.uniform(-2.0, 2.0, 3000),
            ]
        ),
        1,
    ),
    "tanh": (
        _libm.np_tanh,
        _exact_tanh,
        np.concatenate(
            [
                RNG.uniform(-22.0, 22.0, 3000),
                RNG.uniform(-1.0, 1.0, 5000),
                RNG.uniform(-1e-5, 1e-5, 500),
            ]
        ),
        2,  # (fdlibm's tanh: 2 at most over 140,000 values)
    ),
    "cbrt": (
        _libm.np_cbrt,
        _exact_cbrt,
        np.concatenate(
            [RNG.uniform(1e-6, 1.2, 4000), RNG.uniform(-8.0, 8.0, 2000), [1e-310]]
        ),
        1,
    ),
}
CASES["log"] = (
    _libm.np_log,
    _exact_log,
    np.concatenate(
        [
            RNG.uniform(1e-8, 1e4, 3000),
            RNG.uniform(0.5, 2.0, 3000),
            RNG.uniform(1.0 - 1e-6, 1.0 + 1e-6, 500),
            np.exp(RNG.uniform(-740.0, 700.0, 1000)),
            [5e-324, 1e-310, 1.0 + 2**-52],
        ]
    ),
    1,
)
CASES["log1p"] = (
    _libm.np_log1p,
    _exact_log1p,
    np.concatenate(
        [
            RNG.uniform(-0.999, 4.0, 3000),
            RNG.uniform(-0.3, 0.42, 3000),
            RNG.uniform(-1e-6, 1e-6, 500),
            RNG.uniform(1e5, 1e18, 500),
            [1e-300, -1e-20, 2**-30],
        ]
    ),
    1,
)
_ANGLES = np.concatenate(
    [
        RNG.uniform(-0.8, 0.8, 2000),
        RNG.uniform(-7.0, 7.0, 3000),
        RNG.uniform(-5000.0, 5000.0, 2000),
        RNG.uniform(-1e-7, 1e-7, 200),
        np.pi / 2 * np.arange(-40, 41),  # (where the reduction cancels most)
        [1e6, -3.5e5, 1e-300],
    ]
)
CASES["sin"] = (_libm.np_sin, _exact_sin, _ANGLES, 1)
CASES["cos"] = (_libm.np_cos, _exact_cos, _ANGLES, 1)
CASES["tan"] = (
    lambda x: np.array([_libm.tan(v) for v in x]),
    _exact_tan,
    RNG.uniform(-1.5, 1.5, 2000),
    2,  # (a sine over a cosine)
)
_TURNS = RNG.uniform(-np.pi, np.pi, 4000)
_RADII = np.exp(RNG.uniform(-30.0, 30.0, 4000))
_Y = np.concatenate([np.sin(_TURNS) * _RADII, RNG.uniform(-3.0, 3.0, 2000), [1.0]])
_X = np.concatenate([np.cos(_TURNS) * _RADII, RNG.uniform(-3.0, 3.0, 2000), [-1e-5]])
CASES["atan2"] = (
    lambda points: _libm.np_atan2(points.imag, points.real),
    lambda point: _exact_atan2(point.imag, point.real),
    _X + 1j * _Y,
    1,
)
for _y in (2.4, 1.0 / 2.4, 1.0 / 3.0, 0.5, 3.0, 1.5, 0.6, 0.3, 6.0, 0.8):
    CASES[f"power {_y:.4g}"] = (
        lambda x, y=_y: _libm.np_power(x, y),
        lambda x, y=_y: _exact_power(x, y),
        np.concatenate(
            [RNG.uniform(1e-4, 1.0, 2000), RNG.uniform(0.04, 1.0, 2000), [1e-300]]
        ),
        1,
    )


@pytest.mark.parametrize("name", CASES)
def test_within_a_unit_or_two_of_the_exact_value(name):
    ours, exact, inputs, most = CASES[name]
    got = ours(inputs)
    if inputs.dtype.kind != "c":
        inputs = inputs.astype(float)
    worst = max(ulps(float(g), exact(x)) for x, g in zip(inputs, got, strict=True))
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
    # power: no negative bases (murex raises amounts and lengths)
    assert _libm.np_power(1.0, 2.4) == 1.0
    assert _libm.np_power(0.7, 0.0) == 1.0
    assert all(np.isnan(_libm.np_power(np.array([-1.0, -inf, nan]), 2.4)))
    assert np.isnan(_libm.np_power(0.5, nan))
    assert np.isnan(_libm.np_power(0.5, inf))
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


def test_special_values_of_the_rest():
    inf, nan = np.inf, np.nan
    # power at zero and infinity, and the powers worked out exactly
    assert list(_libm.np_power(np.array([0.0, inf]), 0.7)) == [0.0, inf]
    assert list(_libm.np_power(np.array([0.0, inf]), -0.7)) == [inf, 0.0]
    x = RNG.uniform(0.0, 9.0, 100)
    np.testing.assert_array_equal(_libm.np_power(x, 2.0), x * x)
    np.testing.assert_array_equal(_libm.np_power(x, 0.5), np.sqrt(x))
    np.testing.assert_array_equal(_libm.np_power(x, 1.0), x)
    np.testing.assert_array_equal(_libm.np_power(x, -1.0), 1.0 / x)
    np.testing.assert_array_equal(
        _libm.np_power(x, np.full(100, 0.5)), _libm.np_power(x, 0.5)
    )
    # logarithms
    assert list(_libm.np_log(np.array([0.0, 1.0, inf]))) == [-inf, 0.0, inf]
    assert all(np.isnan(_libm.np_log(np.array([-1.0, -inf, nan]))))
    assert list(_libm.np_log1p(np.array([-1.0, 0.0, inf]))) == [-inf, 0.0, inf]
    assert all(np.isnan(_libm.np_log1p(np.array([-1.5, -inf, nan]))))
    assert math.copysign(1.0, _libm.np_log1p(-0.0)) == -1.0
    # sine and cosine
    assert list(_libm.np_sin(np.array([0.0, 1e-300]))) == [0.0, 1e-300]
    assert math.copysign(1.0, _libm.np_sin(-0.0)) == -1.0
    assert _libm.np_cos(0.0) == 1.0
    assert all(np.isnan(_libm.np_sin(np.array([inf, -inf, nan]))))
    assert all(np.isnan(_libm.np_cos(np.array([inf, -inf, nan]))))
    # the angle of a point on an axis, or at infinity, as the C library's
    ys = [0.0, -0.0, 0.0, -0.0, 1.0, -1.0, inf, inf, -inf, -inf, 2.0, -2.0, inf]
    xs = [1.0, 1.0, -1.0, -1.0, 0.0, -0.0, inf, -inf, inf, -inf, inf, -inf, 3.0]
    got = _libm.np_atan2(np.array(ys), np.array(xs))
    for y, x, angle in zip(ys, xs, got, strict=True):
        assert angle == math.atan2(y, x)
        assert math.copysign(1.0, angle) == math.copysign(1.0, math.atan2(y, x))
    assert np.isnan(_libm.np_atan2(nan, 1.0))
    assert _libm.np_atan2(1e300, 1e-300) == math.atan2(1e300, 1e-300)
    assert _libm.np_atan2(1e-300, -1e300) == math.atan2(1e-300, -1e300)
    assert _libm.np_hypot(3.0, 4.0) == 5.0


def test_interp_is_numpys():
    xp = np.array([0.0, 1.0, 1.0, 3.0, 7.0])
    fp = np.array([1.0, 2.0, 5.0, -1.0, 4.0])
    x = np.array([-1.0, 0.0, 0.5, 1.0, 2.0, 3.0, 6.9, 7.0, 8.0, np.nan])
    np.testing.assert_array_equal(_libm.np_interp(x, xp, fp), np.interp(x, xp, fp))
    x = RNG.uniform(-1.0, 8.0, 10000)
    xp = np.sort(RNG.uniform(0.0, 7.0, 50))
    fp = RNG.normal(size=50)
    np.testing.assert_array_equal(_libm.np_interp(x, xp, fp), np.interp(x, xp, fp))
    assert _libm.np_interp(0.5, [0.0, 1.0], [2.0, 4.0]) == 3.0
    assert _libm.np_interp(np.ones((2, 3)), [0.0, 2.0], [0.0, 1.0]).shape == (2, 3)
    with pytest.raises(ValueError):
        _libm.np_interp(0.5, [0.0, 1.0], [2.0])


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
    "log": (_libm.np_log, np.linspace(1e-3, 40.0, 4001)),
    "log1p": (_libm.np_log1p, np.linspace(-0.9, 4.0, 4001)),
    "sin": (_libm.np_sin, np.linspace(-40.0, 40.0, 4001)),
    "cos": (_libm.np_cos, np.linspace(-40.0, 40.0, 4001)),
    "atan2": (
        lambda t: _libm.np_atan2(_libm.np_sin(t) * 3.0, _libm.np_cos(t) * 3.0 - 0.5),
        np.linspace(-3.0, 3.0, 4001),
    ),
}
PINNED = {
    "exp": "fec47515159db554adbaea391f872a7789671f277bb45f987e058a9091f30641",
    "expm1": "4bb356fd9fec1cd868397a204a7976ae15a06d963bd663d67a613d35d6f91936",
    "tanh": "a9d1fe46741fb164bb38b97ae1bf12c8701b678f9dff53455511931098bfa74e",
    "cbrt": "493afc1ae0b78e57cbae884165ecd3ba3a37705993162f206874b34d72c7141f",
    "power 2.4": "9994b5f692d09980fb31f8de53fcc27f297a284ec8bc8d5dec678b874fd94f38",
    "power 1/2.4": "baf806ab6a768c4bb460b8cba96ec7f21653b71bf5cde1a257776f89112f9083",
    "log": "eb190b04521712f7fc7029db35ec41c8e5b28cae3f7f5c0a055db151700c7a11",
    "log1p": "0a048f638226986e6c1cfc40753c296f89c51d945062a34738c2ff03e2a8e846",
    "sin": "36ef904303a21c24452cedc045db3512a54453540921199406bdb7fa97dfe390",
    "cos": "40b0525fd378173522d5fdaccb188328f5a9c2c96f7672e12d8d4fe4b8796a52",
    "atan2": "850189b536543ab6def555dabf8b654c8ea15538b7c48e16be75297c798b3af0",
}


@pytest.mark.parametrize("name", GRIDS)
def test_the_same_bits_everywhere(name):
    function, grid = GRIDS[name]
    assert digest(function(grid)) == PINNED[name]


ROOT = Path(_libm.__file__).parent
#: A call of one of _libm's functions of a number, which a kernel compiles in.
_CALL = re.compile(
    r"_libm\.(exp|expm1|tanh|power|cbrt|log|log1p|sin|cos|tan|atan|atan2|hypot)\("
)


def libm_digest() -> str:
    """The digest of ``murex/_libm.py`` that a file of kernels names."""
    text = (ROOT / "_libm.py").read_text(encoding="utf-8").replace("\r\n", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def test_kernels_that_compile_libm_in_name_the_one_they_were_compiled_with():
    """numba makes a cached kernel again only when its own file changes, and a
    kernel that calls a function of ``_libm`` holds its code. So a file of
    such kernels names the digest of ``_libm.py``: a change there fails here
    until each of those files is changed too, which has numba compile them
    again. (``python tests/test_libm.py`` prints the digest.)"""
    files = []
    for path in sorted(ROOT.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if path.name != "_libm.py" and "njit" in text and _CALL.search(text):
            files.append(path.relative_to(ROOT).as_posix())
            wanted = f'LIBM = "{libm_digest()}"'
            assert wanted in text, f"{path.name} does not name this _libm.py: {wanted}"
    assert {
        "fusain/_engine.py",
        "huile/_engine.py",
        "huile/_render.py",
        "huile/_dab.py",
    } <= set(files)


if __name__ == "__main__":
    for name, (function, grid) in GRIDS.items():
        print(f'    "{name}": "{digest(function(grid))}",')
    print(f'LIBM = "{libm_digest()}"')

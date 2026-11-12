"""Input handling of the colour, path and reference helpers: what is accepted,
what is refused, and with what message."""

import math
from typing import Any

import numpy as np
import pytest

from murex import spectral as sp
from murex import spline
from murex.reference import Reference


def test_spectrum_to_rgb_can_be_rebuilt():
    # The illuminant spectrum and the XYZ white point used to share a name, so
    # the matrix could only be built once, at import.
    np.testing.assert_allclose(
        sp._build_spectrum_to_rgb(sp.WAVELENGTHS), sp.SPECTRUM_TO_RGB, rtol=0, atol=0
    )
    other = sp._build_spectrum_to_rgb(np.linspace(400.0, 700.0, 16))
    assert other.shape == (3, 16)
    np.testing.assert_allclose(other.sum(axis=1), 1.0)


@pytest.mark.parametrize(
    "color, expected",
    [
        ("#ff8000", (1.0, 128 / 255, 0.0)),
        ((1, 1, 1), (1.0, 1.0, 1.0)),  # all at most 1: the 0..1 scale
        ((0, 0, 1), (0.0, 0.0, 1.0)),
        ((255, 128, 0), (1.0, 128 / 255, 0.0)),
        (np.array([255, 128, 0], np.uint8), (1.0, 128 / 255, 0.0)),
        ((255.0, 128.0, 0.0), (1.0, 128 / 255, 0.0)),  # whole floats: 0..255
        ((0.5, 0.25, 1.0), (0.5, 0.25, 1.0)),
        ((1.0 + 1e-9, 0.5, 0.5), (1.0, 0.5, 0.5)),  # rounding overshoot
        ((-0.1, 0.5, 1.0), (0.0, 0.5, 1.0)),  # out of range: clipped
        ((-5, 100, 300), (0.0, 100 / 255, 1.0)),
        # floats on the 0..255 scale, as before
        ((123.4, 56.7, 89.1), (123.4 / 255, 56.7 / 255, 89.1 / 255)),
        ((255, 128.0, 0.5), (1.0, 128 / 255, 0.5 / 255)),
        ((2.0, 0.5, 0.0), (2 / 255, 0.5 / 255, 0.0)),
        # numpy uint8 (an image's pixel) is always 0..255; other ints are not
        (np.array([1, 1, 1], np.uint8), (1 / 255, 1 / 255, 1 / 255)),
        ((np.uint8(1), np.uint8(0), np.uint8(1)), (1 / 255, 0.0, 1 / 255)),
        (np.array([1, 1, 1], np.int64), (1.0, 1.0, 1.0)),
        (np.array([1, 0, 1], np.uint16), (1.0, 0.0, 1.0)),
    ],
)
def test_parse_color_scales(color, expected):
    np.testing.assert_allclose(sp.parse_color(color), expected, rtol=0, atol=1e-12)


@pytest.mark.parametrize(
    "color", [(1.02, 0.5, 0.5), (1.0000011, 0.5, 0.2), (1.99, 0.0, 0.0)]
)
def test_parse_color_refuses_an_ambiguous_scale(color):
    # (1.02, 0.5, 0.5) used to be read on the 0..255 scale: almost black.
    with pytest.raises(ValueError, match=r"0\.\.1 .* 0\.\.255"):
        sp.parse_color(color)


@pytest.mark.parametrize(
    "color, error, message",
    [
        ((np.nan, 0.5, 0.5), ValueError, "finite"),
        ((0.1, 0.2), ValueError, "3 color components"),
        ("red", ValueError, "#rrggbb"),
        (("a", "b", "c"), TypeError, "#rrggbb"),
    ],
)
def test_parse_color_errors(color, error, message):
    with pytest.raises(error, match=message):
        sp.parse_color(color)


@pytest.mark.parametrize("make", [spline.as_path, spline.Polyline, spline.Bezier])
def test_path_needs_points(make):
    with pytest.raises(ValueError, match="at least one point"):
        make([])


@pytest.mark.parametrize("make", [spline.as_path, spline.Polyline])
@pytest.mark.parametrize("bad", [np.nan, np.inf])
def test_path_points_must_be_finite(make, bad):
    with pytest.raises(ValueError, match=r"finite numbers; point 1 is"):
        make([(0, 0), (bad, 3), (10, 10)])


def test_path_points_must_be_pairs():
    with pytest.raises(ValueError, match="pairs, got 3 numbers"):
        spline.as_path([1, 2, 3])
    with pytest.raises(TypeError, match="pairs of numbers"):
        spline.as_path([("a", 1)])


def _samples():
    _, _, u, knot = spline.as_path([(0, 0), (100, 0)]).sample(2.0)
    return u, knot


def test_profile_callables_may_take_one_number():
    u, knot = _samples()
    w = spline.evaluate_profile(lambda u: 30 if u < 0.5 else 10, u, knot, 2)
    np.testing.assert_array_equal(w, np.where(u < 0.5, 30.0, 10.0))
    w = spline.evaluate_profile(lambda u: 10 + 5 * math.sin(u), u, knot, 2)
    np.testing.assert_allclose(w, 10 + 5 * np.sin(u), rtol=1e-15)


def test_vectorised_profile_callables_are_called_once():
    u, knot = _samples()
    calls = []

    def width(v):
        calls.append(v)
        return 10 + 5 * np.sin(v)

    np.testing.assert_array_equal(
        spline.evaluate_profile(width, u, knot, 2), 10 + 5 * np.sin(u)
    )
    assert len(calls) == 1 and calls[0] is u


def test_profile_callable_errors_are_not_hidden():
    u, knot = _samples()
    missing: dict = {}

    def broken(v):  # a genuine error: raised as it is, after one call
        return missing["width"]

    with pytest.raises(KeyError):
        spline.evaluate_profile(broken, u, knot, 2)

    def broken_scalar(v):  # fails on the array, then on each number
        return 30 if v < 0.5 else 1 / 0

    with pytest.raises(ZeroDivisionError) as info:
        spline.evaluate_profile(broken_scalar, u, knot, 2)
    assert "with the array of all u" in str(info.value.__notes__)
    assert isinstance(info.value.__cause__, ValueError)


def test_profile_function_results_are_checked():
    u, knot = _samples()
    n = len(u)
    # a number, one per u, or something that spreads to one per u: as before
    for f in (lambda v: 3, lambda v: np.array([3.0]), lambda v: np.full(n, 3.0)):
        np.testing.assert_array_equal(
            spline.evaluate_profile(f, u, knot, 2), np.full(n, 3.0)
        )

    def mixed_types(v) -> Any:  # a numpy int or a float, by u
        return np.int8(2) if v < 0.5 else 1.0

    np.testing.assert_array_equal(
        spline.evaluate_profile(mixed_types, u, knot, 2),
        np.where(u < 0.5, 2.0, 1.0),
    )
    for f in (
        lambda v: np.atleast_1d(30 if v < 0.5 else 10),  # one array per u
        lambda v: v[:, None] * 10,
        lambda v: np.zeros(n + 1),
    ):
        with pytest.raises(ValueError, match="one number per u"):
            spline.evaluate_profile(f, u, knot, 2)
    not_numbers: list[Any] = [
        lambda v: None,
        lambda v: None if v < 0.5 else 1,
        lambda v: "wide",
    ]
    for f in not_numbers:
        with pytest.raises(TypeError, match="must return numbers"):
            spline.evaluate_profile(f, u, knot, 2)


def test_reference_keeps_a_bounded_number_of_maps():
    rng = np.random.default_rng(2)
    ref = Reference(rng.random((30, 40, 3)), 40, 30)
    xs, ys = rng.random(50) * 39, rng.random(50) * 29
    # 1.936 and 1.9399 share a map (both round to 1.94), but blurred at each
    # they differ: the box radius changes in between
    first = [ref.color(xs, ys, s) for s in (1.936, 3.0)]
    for k in range(60):
        ref.value(xs, ys, 1.0 + 0.1 * k)
        ref.direction(xs, ys, 1.0 + 0.1 * k)
    assert len(ref._cache) == Reference.max_maps
    # made again after being dropped: the same map, at the scale first used
    again = [ref.color(xs, ys, s) for s in (1.9399, 3.0)]
    for a, b in zip(first, again, strict=True):
        np.testing.assert_array_equal(a, b)
    ref.max_maps = 2
    ref.detail(xs, ys, 5.0)
    assert len(ref._cache) == 2


def test_fast_layer_over_white_matches_km_layer_exactly():
    # solve_absorption's inner loop must give K bit for bit as before
    rng = np.random.default_rng(3)
    for _ in range(200):
        kappa = np.exp(rng.uniform(-14.0, 12.0, sp.N_BANDS))
        kappa[:3] = [0.0, 1e-9, 5e-5]  # the small-B branch
        sigma = float(rng.choice([0.0, 1e-7, rng.uniform(0.0, 15.0)]))
        np.testing.assert_array_equal(
            sp._layer_over_white(kappa, sigma), sp.km_layer(kappa, sigma, 1.0)
        )

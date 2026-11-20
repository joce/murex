"""Paints, and mixing them on the palette."""

import numpy as np
import pytest

from murex import spectral as sp
from murex.huile import Paint, mix_colors
from murex.huile import palette as P


@pytest.mark.parametrize(
    "color", ["#c8201e", "#1b3fa0", "#f5d000", "#808080", "#ffffff"]
)
@pytest.mark.parametrize("opacity", [1.0, 0.3])
def test_paint_looks_like_its_color_on_white(color, opacity):
    paint = Paint(color, opacity=opacity)
    assert np.abs(paint.appearance() - sp.parse_color(color)).max() < 2e-3


def test_blue_and_yellow_make_green():
    r, g, b = sp.parse_color(mix_colors(["#1b3fa0", "#f5d000"]))
    assert g > r and g > b
    # whereas averaging RGB gives a grey-ish color with g < r
    avg = (sp.parse_color("#1b3fa0") + sp.parse_color("#f5d000")) / 2
    assert avg[1] < avg[0]


def test_mixing_a_paint_with_itself_changes_nothing():
    p = P.CADMIUM_RED
    m = Paint.mix((p, 1), (p, 3))
    assert np.allclose(m.K, p.K) and np.isclose(m.S, p.S)


def test_white_lightens_and_black_darkens():
    red = P.CADMIUM_RED
    tint = Paint.mix((red, 1), (P.TITANIUM_WHITE, 1))
    shade = Paint.mix((red, 1), (P.IVORY_BLACK, 1))

    def lum(c):
        return float(sp.LUMINANCE @ sp.srgb_to_linear(c))

    assert lum(tint.color) > lum(red.color) > lum(shade.color)


def test_glaze_is_transparent_body_color_is_not():
    over_black = "#000000"
    glaze = Paint.mix((P.ALIZARIN_CRIMSON, 1), (P.MEDIUM, 3))

    def lum(c):
        return float(sp.LUMINANCE @ sp.srgb_to_linear(c))

    # A thin glaze over black stays dark; an opaque light paint covers it.
    assert lum(glaze.appearance(1.0, over_black)) < 0.05
    assert lum(P.TITANIUM_WHITE.appearance(1.0, over_black)) > 0.7


def test_a_paint_is_a_pigment_and_a_pigment_makes_a_paint():
    from murex import Pigment
    from murex.huile.paint import DEFAULT_BODY, Paint, as_paint

    red = Pigment("#c0281e", opacity=0.6, name="a red")
    paint = Paint("#c0281e", opacity=0.6)
    assert isinstance(paint, Pigment)
    np.testing.assert_array_equal(paint.K, red.K)
    assert paint.S == red.S and paint.hex == red.hex
    # a pigment of murex's is taken as paint from the tube, and keeps its name
    taken = as_paint(red)
    assert type(taken) is Paint and taken.body == DEFAULT_BODY
    assert taken.name == "a red"
    np.testing.assert_array_equal(taken.K, red.K)
    assert Paint(red, body=0.2).body == 0.2
    assert Paint(red, opacity=0.3).S == Pigment(red, opacity=0.3).S
    # and mixes with paints: by volume, body and all
    mixed = Paint.mix((red, 1), (Paint("#ffffff", body=0.1), 1))
    assert type(mixed) is Paint and mixed.body == pytest.approx(0.4)
    assert repr(paint).startswith("Paint(") and repr(red).startswith("Pigment(")

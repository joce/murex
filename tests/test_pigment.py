"""Pigments: how they look, mix and are derived from one another."""

from typing import Any

import numpy as np
import pytest

from murex import Pigment, as_pigment, mix_colors
from murex import spectral as sp

RED = Pigment("#c8201e", name="red")
WHITE = Pigment("#fbfbf8")
BLACK = Pigment("#0b0b0c")


def _lum(c):
    return float(sp.LUMINANCE @ sp.srgb_to_linear(c))


@pytest.mark.parametrize(
    "color", ["#c8201e", "#1b3fa0", "#f5d000", "#808080", "#ffffff"]
)
@pytest.mark.parametrize("opacity", [1.0, 0.3])
def test_pigment_looks_like_its_color_on_white(color, opacity):
    pigment = Pigment(color, opacity=opacity)
    assert np.abs(pigment.appearance() - sp.parse_color(color)).max() < 2e-3


def test_blue_and_yellow_make_green():
    r, g, b = sp.parse_color(mix_colors(["#1b3fa0", "#f5d000"]))
    assert g > r and g > b
    # whereas averaging RGB gives a grey-ish color with g < r
    avg = (sp.parse_color("#1b3fa0") + sp.parse_color("#f5d000")) / 2
    assert avg[1] < avg[0]


def test_mix_colors_takes_weights():
    assert mix_colors(["#1b3fa0", "#f5d000"], [1, 0]) == "#1b3fa0"


def test_mixing_a_pigment_with_itself_changes_nothing():
    m = Pigment.mix((RED, 1), (RED, 3))
    assert np.allclose(m.K, RED.K) and np.isclose(m.S, RED.S)


def test_white_lightens_and_black_darkens():
    tint = Pigment.mix((RED, 1), (WHITE, 1))
    shade = Pigment.mix((RED, 1), (BLACK, 1))
    assert _lum(tint.color) > _lum(RED.color) > _lum(shade.color)


def test_a_glaze_is_transparent_and_a_body_color_is_not():
    glaze = Pigment("#8e1b2c", opacity=0.2)
    # A thin glaze over black stays dark; an opaque light pigment covers it.
    assert _lum(glaze.appearance(1.0, "#000000")) < 0.05
    assert _lum(WHITE.appearance(1.0, "#000000")) > 0.7
    # the ground may also be a reflectance spectrum
    np.testing.assert_allclose(
        WHITE.reflectance(1.0, sp.srgb_to_reflectance("#000000")),
        WHITE.reflectance(1.0, "#000000"),
    )


def test_masstone_is_the_pigment_infinitely_thick():
    glaze = Pigment("#8e1b2c", opacity=0.3)
    np.testing.assert_allclose(glaze.masstone, glaze.appearance(1e6), atol=1e-6)
    assert _lum(glaze.masstone) < _lum(glaze.color)


def test_a_pigment_from_a_pigment_applies_opacity_and_strength():
    base = Pigment("#3050c0", opacity=0.6, strength=1.5, name="blue")
    # opacity: derived again from the colour, keeping the pigment's strength
    glaze = Pigment(base, opacity=0.2)
    direct = Pigment("#3050c0", opacity=0.2, strength=1.5)
    np.testing.assert_array_equal(glaze.K, direct.K)
    assert glaze.S == direct.S
    assert glaze.name == "blue"
    assert Pigment(base, name="other").name == "other"
    # strength: relative to the pigment's own
    strong = Pigment(base, strength=2)
    np.testing.assert_allclose(strong.K, 2 * base.K, rtol=1e-15)
    np.testing.assert_allclose(strong.S, 2 * base.S, rtol=1e-15)
    both = Pigment(base, opacity=0.2, strength=2)
    np.testing.assert_allclose(
        both.K, Pigment("#3050c0", opacity=0.2, strength=3).K, rtol=1e-15
    )
    np.testing.assert_allclose(Pigment(strong, opacity=0.2).K, both.K, rtol=1e-15)
    # nothing given: an exact copy
    copy = Pigment(base)
    np.testing.assert_array_equal(copy.K, base.K)
    assert copy.S == base.S and copy.K is not base.K


def test_strength_of_a_mix_and_opacity_refused():
    mixed = Pigment.mix(("#3050c0", 1), ("#ffffff", 2))
    np.testing.assert_allclose(Pigment(mixed, strength=3).K, 3 * mixed.K, rtol=1e-15)
    with pytest.raises(ValueError, match="opacity can only be changed"):
        Pigment(mixed, opacity=0.5)


def test_a_stronger_mix_has_its_own_colour():
    def mixed():
        return Pigment.mix(("#103a8c", 1), (Pigment("#ffffff", opacity=0.05), 4))

    seen = mixed()
    _ = seen.color  # its colour worked out (and kept) before the copy
    for base in (mixed(), seen):
        strong = Pigment(base, strength=3)
        np.testing.assert_array_equal(strong.color, strong.appearance())
        assert strong.hex != base.hex
    assert Pigment(seen, strength=3).hex == Pigment(mixed(), strength=3).hex
    # a pigment made from a colour keeps that colour
    assert Pigment(RED, strength=2).hex == RED.hex


@pytest.mark.parametrize("strength", [0, -1, float("nan"), float("inf")])
def test_strength_must_be_positive(strength):
    with pytest.raises(ValueError, match="strength must be a positive number"):
        Pigment("#3050c0", strength=strength)
    with pytest.raises(ValueError, match="strength must be a positive number"):
        Pigment(RED, strength=strength)


def test_opacity_is_clipped_but_must_be_a_number():
    np.testing.assert_array_equal(
        Pigment("#3050c0", opacity=1.5).K, Pigment("#3050c0", opacity=1.0).K
    )
    with pytest.raises(ValueError, match="opacity must be a number"):
        Pigment("#3050c0", opacity=float("nan"))


def test_mix_accepts_bare_colours_and_refuses_negative_parts():
    bare = Pigment.mix("#ffffff", "#000000")
    paired = Pigment.mix(("#ffffff", 1), ("#000000", 1))
    np.testing.assert_array_equal(bare.K, paired.K)
    assert bare.S == paired.S
    triple = Pigment.mix((1.0, 1.0, 1.0), [0, 0, 0])
    np.testing.assert_array_equal(triple.K, paired.K)
    np.testing.assert_array_equal(Pigment.mix(RED, (WHITE, 0)).K, RED.K)
    with pytest.raises(ValueError, match="non-negative"):
        Pigment.mix(("#3050c0", 2), ("#ffffff", -1))
    with pytest.raises(TypeError, match=r"\(pigment, parts\)"):
        bad: Any = ("#3050c0", "two")
        Pigment.mix(bad)
    with pytest.raises(ValueError, match="positive total volume"):
        Pigment.mix(("#3050c0", 0))


def test_as_pigment_gives_exactly_the_colour_asked_for():
    first = as_pigment((0.5001, 0.2, 0.3))
    second = as_pigment((0.5019, 0.2, 0.3))  # the same 8-bit hex
    np.testing.assert_array_equal(second.color, (0.5019, 0.2, 0.3))
    np.testing.assert_array_equal(second.K, Pigment((0.5019, 0.2, 0.3)).K)
    assert not np.array_equal(first.K, second.K)
    # each call hands out its own pigment: changing one leaves the next alone
    a = as_pigment("#102030")
    a.K *= 2
    a.name = "changed"
    b = as_pigment("#102030")
    np.testing.assert_array_equal(b.K, Pigment("#102030").K)
    assert b.name is None
    assert as_pigment(RED) is RED


def test_a_pigments_color_is_read_only():
    for pigment in (Pigment("#102030"), Pigment.mix("#102030", "#ffffff")):
        with pytest.raises(ValueError):
            pigment.color[0] = 1.0
    colour = np.array([0.1, 0.2, 0.3])
    Pigment(colour)
    colour[0] = 0.5  # the caller's array stays theirs


def test_from_optics_and_repr():
    p = Pigment.from_optics(RED.K, RED.S, name="measured")
    np.testing.assert_allclose(p.color, RED.color, atol=2e-3)
    assert repr(p).startswith("Pigment('measured', #")
    assert repr(Pigment("#102030")) == f"Pigment(#102030, S={Pigment('#102030').S:.2f})"

"""Papers: what is accepted, what each texture's tooth is like, and the maps
a surface reads of them. Sizes are in millimetres; the teeth here are drawn
at 4 px/mm, as fusain draws them."""

import math

import numpy as np
import pytest

import murex
from murex import Paper, papers
from murex.paper import MAPS_KEY, PIT_SPACING, TEXTURES, maps_rng

PX = 4.0  # (pixels to a millimetre)


def _tooth(paper, seed=3, h=120, w=160):
    return paper.tooth(h, w, np.random.default_rng(seed))


@pytest.mark.parametrize("texture", TEXTURES)
def test_tooth_is_a_height_from_0_to_1_that_repeats_with_its_seed(texture):
    paper = Paper(texture=texture)
    tooth = _tooth(paper)
    assert tooth.shape == (120, 160) and tooth.dtype == np.float32
    assert tooth.min() == 0.0 and tooth.max() == 1.0
    assert tooth.std() > 0.1  # it uses the range: there are peaks and valleys
    np.testing.assert_array_equal(tooth, _tooth(paper))
    assert not np.array_equal(tooth, _tooth(paper, seed=4))


def test_laid_paper_has_lines_across_the_sheet():
    tooth = _tooth(Paper(texture="laid", grain=1.0))
    # going down the sheet crosses the laid lines; going across follows them
    down = np.abs(np.diff(tooth, axis=0)).mean()
    across = np.abs(np.diff(tooth, axis=1)).mean()
    assert down > 2 * across
    # and the lines come back every grain: 4 pixels
    column = tooth[:, 40] - tooth[:, 40].mean()
    spectrum = np.abs(np.fft.rfft(column))
    assert np.argmax(spectrum[1:]) + 1 == round(len(column) / 4.0)


def test_grain_sets_the_size_of_the_tooth():
    for texture in TEXTURES:
        fine = _tooth(Paper(texture=texture, grain=0.5))
        coarse = _tooth(Paper(texture=texture, grain=2.0))
        step = [np.abs(np.diff(t, axis=0)).mean() for t in (fine, coarse)]
        assert step[0] > 1.5 * step[1], texture


def test_wove_paper_is_even_at_the_scale_of_a_pencil_line():
    # (broad patches of high and low tooth made shading come out in blotches
    # wider than the pencil that drew it)
    tooth = _tooth(Paper(texture="wove", grain=0.75)).astype(np.float64)
    blocks = tooth[:120, :160].reshape(10, 12, 16, 10).mean(axis=(1, 3))
    assert blocks.std() < 0.02 and tooth.std() > 0.15
    # its bumps are about a grain across: the runs of high ground along a row
    high = np.pad(tooth > 0.5, ((0, 0), (1, 1)))
    starts = (~high[:, :-1] & high[:, 1:]).sum()
    assert 2.0 < high.sum() / starts < 4.5


def test_rough_paper_has_broader_bumps_than_wove_of_the_same_grain():
    wove = _tooth(Paper(texture="wove", grain=1.0))
    rough = _tooth(Paper(texture="rough", grain=1.0))
    assert np.abs(np.diff(wove, axis=1)).mean() > np.abs(np.diff(rough, axis=1)).mean()


def _share_by_scale(tooth, grain):
    """The share of the tooth's variation at wavelengths under 0.8 grain
    (``grain`` in pixels), from there to 4 grains, and above."""
    a = tooth.astype(np.float64) - tooth.mean()
    power = np.abs(np.fft.fft2(a)) ** 2
    fy = np.fft.fftfreq(a.shape[0])[:, None]
    fx = np.fft.fftfreq(a.shape[1])[None, :]
    waves = grain * np.hypot(fy, fx)  # per grain
    fine = power[waves > 1 / 0.8].sum()
    broad = power[waves < 1 / 4.0].sum()
    return fine / power.sum(), 1 - (fine + broad) / power.sum(), broad / power.sum()


@pytest.mark.parametrize("grain", [0.75, 1.0, 1.25])
def test_pebbled_paper_varies_at_the_scale_of_its_pits_and_little_beside(grain):
    # (a wove paper has no more broad variation but is all fine flecks; a
    # rough one of this grain is blotchy)
    def shares(texture):
        tooth = _tooth(Paper(texture=texture, grain=grain), h=256, w=256)
        return _share_by_scale(tooth, grain * PX)

    fine, medium, broad = shares("pebbled")
    assert medium > 0.75 and fine < 0.1 and broad < 0.15
    assert shares("rough")[2] > 3 * broad
    # no patches of high or low ground several pits wide
    tooth = _tooth(Paper(texture="pebbled", grain=0.75)).astype(np.float64)
    blocks = tooth[:120, :160].reshape(4, 30, 4, 40).mean(axis=(1, 3))
    assert blocks.std() < 0.02


def test_pebbled_paper_is_pits_in_a_net_of_rims():
    grain = 1.25
    tooth = _tooth(Paper(texture="pebbled", grain=grain), h=200, w=200)
    low = tooth < 0.35
    # the low ground is separate pits, most of the one to a square 1.3 grains
    # wide that there are (the shallowest stay above it, and some run together)
    pits = _count_patches(low)
    assert 0.45 < pits * (PIT_SPACING * grain * PX) ** 2 / low.size < 1.1
    # and the high ground between them mostly hangs together
    high = tooth > 0.5
    assert _largest_patch(high) > 0.6 * high.sum()
    # there is no grain to it: across and down are alike
    down = np.abs(np.diff(tooth, axis=0)).mean()
    across = np.abs(np.diff(tooth, axis=1)).mean()
    assert 0.9 < down / across < 1.1


def test_the_pits_of_a_pebbled_paper_differ_in_depth():
    tooth = _tooth(Paper(texture="pebbled", grain=1.5), h=240, w=240)
    floors = [tooth[where].min() for where in _patches(tooth < 0.45) if where[0].size]
    assert len(floors) > 300
    assert np.percentile(floors, 90) - np.percentile(floors, 10) > 0.25


def _patches(mask):
    """The patches of ``mask`` that hang together by their sides, as index
    arrays."""
    label = np.where(mask, np.arange(mask.size).reshape(mask.shape), -1)
    while True:  # every cell takes the highest label among its neighbours
        grown = label.copy()
        grown[1:] = np.maximum(grown[1:], label[:-1])
        grown[:-1] = np.maximum(grown[:-1], label[1:])
        grown[:, 1:] = np.maximum(grown[:, 1:], label[:, :-1])
        grown[:, :-1] = np.maximum(grown[:, :-1], label[:, 1:])
        grown[~mask] = -1
        if np.array_equal(grown, label):
            break
        label = grown
    return [np.nonzero(label == name) for name in np.unique(label[mask])]


def _count_patches(mask):
    return len(_patches(mask))


def _largest_patch(mask):
    return max(where[0].size for where in _patches(mask))


def test_sanded_card_is_an_even_field_of_sharp_grit():
    sanded = _tooth(Paper(texture="sanded", grain=0.75)).astype(np.float64)
    wove = _tooth(Paper(texture="wove", grain=0.75)).astype(np.float64)
    # as many grains high as low, and no broad patches of either
    assert abs(np.median(sanded) - 0.5) < 0.05
    blocks = sanded[:120, :160].reshape(10, 12, 16, 10).mean(axis=(1, 3))
    assert blocks.std() < 0.02
    # sharper than the bumps of a wove paper of the same grain
    assert (
        np.abs(np.diff(sanded, axis=1)).mean()
        > 1.1 * np.abs(np.diff(wove, axis=1)).mean()
    )


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"texture": "canvas"}, "unknown texture"),
        ({"grain": 0}, "grain must be"),
        ({"grain": float("nan")}, "grain must be"),
        ({"depth": -0.1}, "depth must be"),
        ({"depth": float("inf")}, "depth must be"),
        ({"bite": 1.5}, "bite must be"),
        ({"give": -0.5}, "give must be"),
        ({"hold": 0.0}, "hold must be"),
        ({"hold": float("nan")}, "hold must be"),
        ({"color": "paper white"}, "#rrggbb"),
        ({"variation": "marbled"}, "unknown variation"),
        ({"thickness": 0.0}, "thickness must be"),
        ({"thickness": float("inf")}, "thickness must be"),
        ({"sizing": 1.5}, "sizing must be"),
        ({"porosity": 0.0}, "porosity must be"),
        ({"porosity": 1.0}, "porosity must be"),
        ({"fibre_angle": float("nan")}, "fibre_angle must be"),
        ({"fibre_ratio": 0.9}, "fibre_ratio must be"),
        ({"fibre_ratio": float("inf")}, "fibre_ratio must be"),
    ],
)
def test_a_paper_checks_its_numbers(changes, message):
    with pytest.raises(ValueError, match=message):
        Paper(**changes)


def test_with_changes_a_copy():
    toned = papers.CARTRIDGE.with_(color="#b9a98c", name="toned")
    assert (toned.color, toned.name) == ("#b9a98c", "toned")
    assert toned.grain == papers.CARTRIDGE.grain
    assert papers.CARTRIDGE.color != "#b9a98c"
    with pytest.raises(ValueError, match="bite must be"):
        papers.CARTRIDGE.with_(bite=2)


def test_presets_are_named_and_distinct():
    names = [paper.name for paper in papers.ALL]
    assert len(set(names)) == len(names) == 14
    assert len(set(papers.ALL)) == len(papers.ALL)
    for paper in papers.ALL:
        assert paper.reflectance().shape == (24,)


def test_paper_is_shared_and_exported_by_murex():
    assert murex.Paper is Paper and murex.papers is papers
    assert papers.WATERCOLOUR == (
        papers.HOT_PRESSED,
        papers.COLD_PRESSED,
        papers.ROUGH,
        papers.XUAN,
    )


@pytest.mark.parametrize("texture", TEXTURES)
def test_the_tooth_is_drawn_at_the_scale_it_is_asked_for(texture):
    # a grain in millimetres is that many times the scale in pixels: 0.75 mm
    # at 8 px/mm is the tooth of 1.5 mm at 4 px/mm, draw for draw
    def at(grain, px):
        paper = Paper(texture=texture, grain=grain)
        return paper.tooth(90, 70, np.random.default_rng(5), px_per_mm=px)

    np.testing.assert_array_equal(at(0.75, 8.0), at(1.5, 4.0))
    # (4 px/mm unless asked)
    tooth = Paper(texture=texture).tooth(90, 70, np.random.default_rng(5))
    np.testing.assert_array_equal(at(0.75, 4.0), tooth)
    with pytest.raises(ValueError, match="px_per_mm"):
        at(0.75, 0.0)


def test_the_water_a_paper_holds_is_its_pores():
    paper = Paper(thickness=0.5, porosity=0.6)
    assert paper.capacity == pytest.approx(0.3)
    # a heavy sheet holds several times what a light one does (design.md)
    assert papers.ROUGH.capacity > 5 * papers.XUAN.capacity
    assert papers.XUAN.sizing == 0.0 and papers.HOT_PRESSED.sizing == 1.0
    for paper in papers.WATERCOLOUR:
        # 300 g/m2 (gonzalez2019's Fabriano), but xuan's 30, at the 1.5 g/cm3
        # of cellulose that walji2016's Table 1 gives
        weight = 30.0 if paper is papers.XUAN else 300.0
        assert 1.0 - weight / (paper.thickness * 1500.0) == pytest.approx(
            paper.porosity, abs=0.006
        )


def test_walji2016_s_papers_give_the_density_of_cellulose_used():
    # Table 1: 87 g/m2, 0.18 mm, 67.8%; 325 g/m2, 0.70 mm, 69.1%
    for weight, thickness, porosity in ((87.0, 0.18, 0.678), (325.0, 0.70, 0.691)):
        density = weight / (thickness * (1.0 - porosity))  # kg/m3
        assert density == pytest.approx(1500.0, rel=0.005)


@pytest.mark.parametrize("paper", papers.ALL, ids=lambda paper: paper.name)
def test_a_machine_made_paper_s_maps_are_even_and_draw_nothing(paper):
    maps = paper.maps(30, 40, px_per_mm=2.0, seed=9)
    assert paper.variation == "even"
    expect = {
        "sizing": paper.sizing,
        "capacity": paper.capacity,
        "porosity": paper.porosity,
        "fibre_angle": math.radians(paper.fibre_angle),
        "fibre_ratio": paper.fibre_ratio,
    }
    for name, value in expect.items():
        array = getattr(maps, name)
        assert array.shape == (30, 40) and array.dtype == np.float32, name
        assert (array == np.float32(value)).all(), name
        assert not array.flags.writeable, name  # (a view of one number)
    assert maps.reflectance.shape == (30, 40, 24)
    np.testing.assert_array_equal(
        maps.reflectance[7, 11], paper.reflectance().astype(np.float32)
    )
    # even maps draw nothing: the seed is not even looked at
    again = paper.maps(30, 40, px_per_mm=2.0, seed=10)
    np.testing.assert_array_equal(again.capacity, maps.capacity)


def test_a_cloudy_paper_s_maps_vary_from_a_generator_of_their_own():
    paper = papers.COLD_PRESSED.with_(variation="cloudy")
    maps = paper.maps(120, 160, seed=4)
    # thicker and thinner in clouds, and sized unevenly
    capacity = maps.capacity.astype(np.float64) / paper.capacity
    assert capacity.std() > 0.02 and abs(capacity.mean() - 1.0) < 0.1
    assert 0.85 - 1e-6 <= capacity.min() <= capacity.max() <= 1.15 + 1e-6
    assert maps.sizing.std() > 0.005
    assert 0.0 <= maps.sizing.min() <= maps.sizing.max() <= 1.0
    # the rest even
    assert (maps.porosity == np.float32(paper.porosity)).all()
    # the same seed, the same sheet; another seed, another
    np.testing.assert_array_equal(paper.maps(120, 160, seed=4).capacity, maps.capacity)
    assert not np.array_equal(paper.maps(120, 160, seed=5).capacity, maps.capacity)
    # its draws are not the tooth's: the generator of the seed's own key
    ours = maps_rng(4).random(5)
    assert not np.array_equal(ours, np.random.default_rng(4).random(5))
    own = np.random.SeedSequence(4, spawn_key=(MAPS_KEY,))
    np.testing.assert_array_equal(ours, np.random.default_rng(own).random(5))
    np.testing.assert_array_equal(maps_rng(np.random.SeedSequence(4)).random(5), ours)

"""The shared surface, step 1 of the wet media (murex-cjx.2): water laid on a
paper soaks into its fibres and evaporates as the clock runs, until it is
dry; it is conserved, and it measures the same in millimetres and seconds
at every scale and however a wait is cut."""

import math

import numpy as np
import pytest

import murex
from murex import Air, Paper, Surface, papers
from murex import surface as sf
from murex.fusain import Sheet

#: A room as gonzalez2019's: 22 C, 35% relative humidity, still air.
ROOM = Air(humidity=0.35, temperature=22.0)


def _disc(surface: Surface, radius_mm: float) -> np.ndarray:
    """A disc of ``radius_mm`` in the middle of ``surface``, as a share of
    each pixel (by sixteen points in each)."""
    px = surface.px_per_mm
    k = (np.arange(4) + 0.5) / 4
    y = (np.arange(surface.height)[:, None] + k[None, :]).ravel() / px
    x = (np.arange(surface.width)[:, None] + k[None, :]).ravel() / px
    cy, cx = surface.height / px / 2, surface.width / px / 2
    inside = (y[:, None] - cy) ** 2 + (x[None, :] - cx) ** 2 <= radius_mm**2
    return inside.reshape(surface.height, 4, surface.width, 4).mean(axis=(1, 3))


def _balance(surface: Surface) -> float:
    """What conservation leaves over, as a share of what was laid."""
    left = surface.water_laid - surface.water_on_sheet - surface.water_evaporated
    return abs(left) / surface.water_laid


# -- the sheet ---------------------------------------------------------------


def test_murex_exports_the_surface_and_the_air():
    assert murex.Surface is Surface and murex.Air is Air


def test_the_tooth_is_the_paper_s_from_the_seed_as_fusain_draws_it():
    for paper in (papers.INGRES, papers.COLD_PRESSED):
        surface = Surface(70, 50, paper=paper, seed=3)
        sheet = Sheet(70, 50, paper=paper, seed=3)
        np.testing.assert_array_equal(surface.tooth, sheet.tooth)
    # and at another scale, the paper's grain in pixels of that scale
    fine = Surface(70, 50, paper=papers.INGRES, px_per_mm=8.0, seed=3)
    rng = np.random.default_rng(3)
    expect = papers.INGRES.tooth(50, 70, rng, px_per_mm=8.0)
    np.testing.assert_array_equal(fine.tooth, expect)


def test_a_varying_map_leaves_the_tooth_s_draws_as_they_are():
    even = Surface(90, 60, paper=papers.COLD_PRESSED, seed=8)
    cloudy = Surface(
        90, 60, paper=papers.COLD_PRESSED.with_(variation="cloudy"), seed=8
    )
    np.testing.assert_array_equal(cloudy.tooth, even.tooth)
    # the generator left after the tooth is where it was too
    assert cloudy._rng.random() == even._rng.random()
    assert cloudy.maps.capacity.std() > 0 == even.maps.capacity.std()
    # and the maps are the paper's, from the sheet's seed
    np.testing.assert_array_equal(
        cloudy.maps.sizing, cloudy.paper.maps(60, 90, seed=8).sizing
    )


def test_a_surface_checks_what_it_is_given():
    with pytest.raises(TypeError, match="width"):
        Surface(10.0, 10)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="height"):
        Surface(10, True)
    with pytest.raises(ValueError, match="width"):
        Surface(0, 10)
    with pytest.raises(ValueError, match="px_per_mm"):
        Surface(10, 10, px_per_mm=0.0)
    with pytest.raises(ValueError, match="px_per_mm"):
        Surface(10, 10, px_per_mm=math.inf)
    surface = Surface(10, 8)
    assert surface.paper == Paper() and surface.air == Air() and surface.time == 0.0
    assert surface.standing.dtype == surface.wet.dtype == np.float32
    for depth in (-0.1, math.nan, math.inf):
        with pytest.raises(ValueError, match="depth"):
            surface.lay_water(depth)
    with pytest.raises(ValueError, match="where must be"):
        surface.lay_water(0.1, np.ones((8, 9)))
    with pytest.raises(ValueError, match="share"):
        surface.lay_water(0.1, np.full((8, 10), 1.5))
    for seconds in (-1.0, math.nan, math.inf):
        with pytest.raises(ValueError, match="seconds"):
            surface.wait(seconds)


@pytest.mark.parametrize(
    "changes, message",
    [
        ({"humidity": 1.2}, "humidity"),
        ({"humidity": math.nan}, "humidity"),
        ({"temperature": -5.0}, "temperature"),
        ({"temperature": 80.0}, "temperature"),
        ({"speed": -1.0}, "speed"),
        ({"speed": math.inf}, "speed"),
    ],
)
def test_the_air_checks_its_numbers(changes, message):
    with pytest.raises(ValueError, match=message):
        Air(**changes)


# -- water laid, and conserved -----------------------------------------------


def test_water_laid_stands_on_the_paper_and_is_counted_in_microlitres():
    surface = Surface(40, 20, px_per_mm=4.0)  # 10 by 5 mm
    surface.lay_water(0.25)
    assert surface.water_laid == pytest.approx(0.25 * 50.0)
    assert surface.water_standing == pytest.approx(12.5) and surface.water_held == 0
    mask = np.zeros((20, 40), bool)
    mask[:, :20] = True  # (half of it)
    surface.lay_water(0.5, mask)
    assert surface.water_laid == pytest.approx(12.5 + 12.5)
    assert surface.standing[0, 0] == np.float32(0.75)
    assert surface.standing[0, 30] == np.float32(0.25)
    assert surface.time == 0.0  # (laying takes no time)
    assert isinstance(surface._laid, float) and isinstance(surface._evaporated, float)


@pytest.mark.parametrize(
    "paper",
    [
        papers.HOT_PRESSED,
        papers.COLD_PRESSED,
        papers.XUAN,
        papers.CARTRIDGE.with_(variation="cloudy"),
    ],
    ids=lambda paper: f"{paper.name}-{paper.variation}",
)
def test_water_is_conserved_through_laying_waiting_and_drying(paper):
    surface = Surface(60, 48, paper=paper, seed=2, air=ROOM)
    surface.lay_water(0.2, _disc(surface, 4.0))
    for seconds in (0.5, 3.0, 40.0):
        surface.wait(seconds)
        assert _balance(surface) < 1e-6
    surface.lay_water(0.05)
    surface.wait(100.0)
    assert _balance(surface) < 1e-6
    assert surface.water_evaporated > 0 and surface.water_held > 0
    waited = surface.dry()
    assert waited > 0 and surface.time == pytest.approx(143.5 + waited)
    assert surface.water_on_sheet == 0.0
    assert not surface.standing.any() and not surface.wet.any()
    assert surface.water_evaporated == pytest.approx(surface.water_laid, rel=1e-6)


# -- soaking in --------------------------------------------------------------


def _soaked(sizing: float, seconds: float, **changes) -> float:
    """How much of 0.3 mm laid on a paper of ``sizing`` is in its fibres after
    ``seconds``, as a share of what they hold."""
    paper = papers.COLD_PRESSED.with_(sizing=sizing, **changes)
    surface = Surface(4, 4, paper=paper, air=ROOM)
    surface.lay_water(0.3)
    surface.wait(seconds)
    return float(surface.wet[0, 0]) / paper.capacity


def test_sizing_slows_soaking_in():
    shares = [_soaked(sizing, 5.0) for sizing in (0.0, 0.25, 0.5, 0.75, 0.9, 1.0)]
    assert shares == sorted(shares, reverse=True)
    # (all of it, but what 5 s evaporated from the fibres)
    all_in = (0.3 - 5.0 * ROOM.rate) / papers.COLD_PRESSED.capacity
    assert shares[0] == pytest.approx(all_in, rel=1e-5)
    assert shares[-1] < 0.25 * shares[0]
    # an unsized paper drinks it at once (das2019: through 0.18 mm of filter
    # paper in 2.43 ms); a hard-sized one takes minutes (gonzalez2019: a drop
    # does not soak in quickly)
    # (the front is through 0.55 mm of it in 0.02 s)
    assert _soaked(0.0, 0.05) == pytest.approx(
        0.3 / papers.COLD_PRESSED.capacity, rel=1e-4
    )
    assert _soaked(1.0, 10.0) < 0.25 < 0.7 < _soaked(1.0, 300.0)


def test_water_goes_into_the_paper_as_the_square_root_of_the_time():
    # (Lucas-Washburn, with das2019's coefficient: 0.38 cm/s**0.5 on an
    # unsized paper; a thick sheet, so that its fibres are not full)
    paper = Paper(sizing=0.0, thickness=20.0, porosity=0.6)
    early, late = [
        _soaked_on(paper, seconds) for seconds in (0.01, 0.04)
    ]  # (mm of water in the fibres)
    assert late / early == pytest.approx(2.0, rel=1e-3)
    assert early == pytest.approx(0.6 * 3.8 * math.sqrt(0.01), rel=1e-3)


def _soaked_on(paper: Paper, seconds: float) -> float:
    surface = Surface(3, 3, paper=paper, air=Air(humidity=1.0))
    surface.lay_water(5.0)
    surface.wait(seconds)
    return float(surface.wet[1, 1])


def test_full_fibres_take_no_more():
    surface = Surface(5, 5, paper=papers.XUAN, air=ROOM)
    surface.lay_water(0.5)  # (xuan holds 0.06 mm)
    capacity = np.float32(papers.XUAN.capacity)
    surface.wait(1.0)
    assert (surface.wet == capacity).all()
    standing = surface.water_standing
    surface.wait(100.0)
    # the fibres stay full while water stands over them: it evaporates from
    # what stands first
    assert (surface.wet == capacity).all()
    lost = standing - surface.water_standing
    assert lost == pytest.approx(ROOM.rate * 100.0 * 25 / 16, rel=1e-5)


def test_humidity_does_not_change_how_fast_water_soaks_in():
    # (walji2016: wicking took the same time from 30% to 85%)
    dry, damp = Air(humidity=0.3), Air(humidity=0.85)
    soaked = []
    for air in (dry, damp):
        surface = Surface(3, 3, paper=papers.HOT_PRESSED, air=air)
        surface.lay_water(0.4)
        surface.wait(30.0)
        soaked.append(surface.wet[1, 1])
    assert soaked[0] == soaked[1]


# -- drying ------------------------------------------------------------------


def test_the_air_evaporates_water_as_etoolbox_evap_works_it_out():
    # its worked example: water at 20 C, air at 25 C and 50%, 0.5 m/s
    assert sf.humidity_ratio(20.0) == pytest.approx(0.014659, rel=1e-3)
    assert sf.humidity_ratio(25.0, 0.5) == pytest.approx(0.0098, rel=0.01)
    per_hour = sf.evaporation(20.0, 25.0, 0.5, 0.5) * 3600  # kg/(m2 h), mm/h
    assert per_hour == pytest.approx(0.168, rel=0.02)
    # air that holds more than the water gives off condenses nothing
    assert sf.evaporation(10.0, 30.0, 0.9, 0.0) == 0.0
    assert Air(humidity=1.0).rate == 0.0


def _drying_time(paper: Paper, air: Air, depth: float = 0.2) -> float:
    surface = Surface(6, 4, paper=paper, air=air)
    surface.lay_water(depth)
    return surface.dry()


def test_humidity_and_air_speed_change_drying_as_etoolbox_evap_says():
    paper = papers.COLD_PRESSED
    still = _drying_time(paper, ROOM)
    # the rate goes as the humidity the air lacks: halve it, twice the time
    lacks = sf.humidity_ratio(22.0) - sf.humidity_ratio(22.0, 0.35)
    damp = Air(humidity=0.35 + 0.5 * lacks / sf.humidity_ratio(22.0), temperature=22.0)
    assert sf.humidity_ratio(22.0) - sf.humidity_ratio(22.0, damp.humidity) == (
        pytest.approx(0.5 * lacks, rel=1e-3)
    )
    assert _drying_time(paper, damp) == pytest.approx(2 * still, rel=2e-3)
    # and rises by 19/25 per m/s of air
    windy = Air(humidity=0.35, temperature=22.0, speed=1.0)
    assert still / _drying_time(paper, windy) == pytest.approx(44 / 25, rel=1e-9)
    # warmer air dries faster
    warm = Air(humidity=0.35, temperature=30.0)
    assert _drying_time(paper, warm) < 0.7 * still


def test_a_sheet_dries_in_the_time_of_gonzalez2019_s_drop():
    # 50 uL on a 300 g/m2 cold-pressed paper at 22 C and 35%: about 2500 s.
    # Here the drop's water is in as much of the paper as holds it (a disc
    # of 50 / 0.352 mm2): it dries in of the order of that (4600 s)
    paper = papers.COLD_PRESSED
    surface = Surface(120, 120, paper=paper, px_per_mm=4.0, air=ROOM)
    area = 50.0 / paper.capacity
    surface.lay_water(paper.capacity, _disc(surface, math.sqrt(area / math.pi)))
    assert surface.water_laid == pytest.approx(50.0, rel=0.01)
    waited = surface.dry()
    assert 1000.0 < waited < 10000.0
    assert surface.water_on_sheet == 0.0


def test_dry_ends_and_refuses_air_that_never_dries():
    surface = Surface(4, 4, air=Air(humidity=1.0))
    assert surface.dry() == 0.0  # (nothing to dry)
    surface.lay_water(0.1)
    surface.wait(10.0)  # (it soaks in, and nothing evaporates)
    assert surface.water_on_sheet == pytest.approx(surface.water_laid)
    with pytest.raises(ValueError, match="saturated"):
        surface.dry()
    surface.air = ROOM
    assert 0 < surface.dry() < math.inf
    # what is left below the tolerance of dry is no water
    surface.lay_water(sf.DRY / 2)
    assert surface.dry() == 0.0


# -- the same in millimetres and seconds -------------------------------------


def test_the_same_water_measures_the_same_at_every_scale():
    found = []
    for px in (2.0, 4.0, 8.0):
        # 20 by 15 mm
        surface = Surface(int(20 * px), int(15 * px), papers.COLD_PRESSED, px, air=ROOM)
        surface.lay_water(0.2)
        surface.lay_water(0.3, _disc(surface, 5.0))
        surface.wait(20.0)
        found.append(
            (
                surface.water_laid,
                surface.water_standing,
                surface.water_held,
                surface.dry(),
                surface.water_evaporated,
            )
        )
    laid, standing, held, drying, evaporated = np.array(found).T
    # (the disc covers pixels by sixteenths: a little more or less of it)
    disc = 0.3 * math.pi * 25.0
    assert laid == pytest.approx(0.2 * 300.0 + disc, rel=1e-3)
    assert standing == pytest.approx(standing[1], rel=2e-3)
    assert held == pytest.approx(held[1], rel=2e-3)
    assert drying == pytest.approx(drying[1], rel=1e-9)
    assert evaporated == pytest.approx(laid, rel=1e-6)


@pytest.mark.parametrize("paper", [papers.HOT_PRESSED, papers.XUAN])
def test_a_wait_cut_into_short_waits_is_the_same_wait(paper):
    def after(cuts):
        surface = Surface(10, 8, paper=paper, air=ROOM)
        surface.lay_water(0.08)
        surface.lay_water(0.1, np.linspace(0.0, 1.0, 80).reshape(8, 10))
        for seconds in cuts:
            surface.wait(seconds)
        return surface

    whole = after([600.0])
    for cuts in ([1.0] * 600, [0.37] * 1621 + [600 - 0.37 * 1621], [7.5] * 80):
        cut = after(cuts)
        assert cut.time == pytest.approx(600.0, rel=1e-12)
        assert cut.water_evaporated == pytest.approx(whole.water_evaporated, rel=1e-6)
        # (to the rounding of float32, once a wait: 5e-5 after 1600 of them)
        total = cut.standing.astype(np.float64) + cut.wet
        np.testing.assert_allclose(total, whole.standing + whole.wet, rtol=1e-4)
        # which of the two holds it can differ by what a step evaporates
        np.testing.assert_allclose(cut.wet, whole.wet, atol=1.5 * ROOM.rate * sf.STEP)


def test_how_many_steps_a_wait_takes_does_not_hang_on_its_last_bit():
    def nudged(x):
        return math.nextafter(x, -math.inf), x, math.nextafter(x, math.inf)

    for count in (1, 3, 7, 600, 2500):
        assert {sf.steps(s) for s in nudged(count * sf.STEP)} == {count}
    # 0.1 s thirty times is 3.0000000000000004 s: three steps, not four
    assert sf.steps(sum([0.1] * 30)) == 3
    assert sf.steps(0.0) == 1 and sf.steps(1e-300) == 1
    assert sf.steps(2.5 * sf.STEP) == 3

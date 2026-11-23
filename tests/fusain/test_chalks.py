"""Pastel pencils and Conté crayons: what they are next to the pastels and
pencils they are akin to, measured."""

import numpy as np
import pytest

from murex import spectral as sp
from murex.fusain import Sheet, Stick, conte, papers, pastels, pencils, tools
from murex.fusain._engine import IV, IW

BOX = (20, 20, 180, 130)
INSIDE = (slice(50, 100), slice(50, 150))
RED = "#a8492f"
LEVEL = papers.CARTRIDGE.with_(depth=0.0)
CHALKS = [pastels.pencil(RED), *conte.ALL]


def _shaded(medium, paper=papers.CARTRIDGE, layers=2) -> tuple[Sheet, float]:
    sheet = Sheet(200, 150, paper=paper, seed=1)
    laid = sum(
        sheet.shade(BOX, medium, 0.7, 8.0, angle=30 + 50 * layer)
        for layer in range(layers)
    )
    return sheet, laid


def _total(sheet) -> float:
    return float(sheet.pigment().sum(dtype=np.float64))


def _dust(sheet) -> float:
    """The share of what is on the sheet that lies there as dust."""
    return float(sheet.loose[..., IV].sum() + sheet.under[..., IV].sum()) / _total(
        sheet
    )


def _luminance(sheet, where=INSIDE) -> float:
    spectrum = sheet.reflectance()[where].astype(np.float64).mean(axis=(0, 1))
    return float(sp.reflectance_to_linear_rgb(spectrum) @ sp.LUMINANCE)


def _carried_out(sheet) -> float:
    """The share of a patch that a finger rubbed across it carries past its
    edge."""
    before = float(sheet.pigment()[:, 185:].sum())
    for k in range(3):
        sheet.smudge([(40, 60 + 8 * k), (198, 60 + 8 * k)], tools.FINGER, 0.7)
    return (float(sheet.pigment()[:, 185:].sum()) - before) / _total(sheet)


def _left_by_an_eraser(sheet) -> float:
    """The share left where a kneaded eraser was pulled three times."""
    where = (slice(65, 85), slice(60, 140))
    before = float(sheet.pigment()[where].sum())
    for _ in range(3):
        sheet.erase([(30, 75), (190, 75)], tools.KNEADED, 0.9, 20)
    return float(sheet.pigment()[where].sum()) / before


def _across(sheet) -> np.ndarray:
    """What lies across a band drawn along y = 100, per row, smoothed over
    five rows, as a share of its middle."""
    raw = sheet.pigment()[:, 120:280].astype(np.float64).mean(axis=1)
    smooth = np.convolve(raw, np.ones(5) / 5, "same")
    return smooth / smooth[97:104].mean()


def _full_share(across: np.ndarray, side: float) -> float:
    """The share of a band ``side`` rows wide that has 0.9 of its middle."""
    return float((across >= 0.9).sum() / side)


# --------------------------------------------------------------------------
# what they are


def test_names():
    assert pastels.pencil(RED).name == "#a8492f pastel pencil"
    assert pastels.pencil(RED, "sanguine").name == "sanguine"
    assert pastels.pencil(RED, "sanguine").pigment.name == "sanguine"
    assert conte.crayon(RED).name == "#a8492f Conté crayon"
    assert conte.crayon(RED, "red chalk").pigment.name == "red chalk"
    assert [m.name for m in conte.ALL] == [
        "black Conté",
        "sepia",
        "bistre",
        "sanguine",
        "white Conté",
    ]
    with pytest.raises(ValueError, match="#rrggbb"):
        conte.crayon("sanguine")


@pytest.mark.parametrize("medium", CHALKS, ids=lambda m: m.name)
def test_what_leaves_the_stick_is_on_the_paper(medium):
    sheet, laid = _shaded(medium)
    assert laid > 0
    assert _total(sheet) == pytest.approx(laid, rel=1e-6)
    # dry media: no wax, nothing that shines
    assert medium.wax == 0 and medium.sheen == 0 and medium.melts == 0
    assert sheet.held[..., IW].sum() == 0


@pytest.mark.parametrize("tool", [tools.FINGER, tools.STUMP, tools.KNEADED])
def test_what_a_tool_takes_of_them_is_on_the_tool(tool):
    for medium in (pastels.pencil(RED), conte.SANGUINE):
        sheet, laid = _shaded(medium)
        ends = [(30, 75), (170, 75)]
        if tool is tools.KNEADED:
            taken = sheet.erase(ends, tool, 0.9, 20)
        else:
            taken = sheet.smudge(ends, tool, 0.7, 20.0)
        assert taken > 0
        assert _total(sheet) + taken == pytest.approx(laid, rel=1e-5)


# --------------------------------------------------------------------------
# a pastel pencil: a hard pastel's core, with a pencil's point


def test_a_pastel_pencil_lays_and_dusts_a_little_less_than_a_hard_pastel():
    pencil, laid = _shaded(pastels.pencil(RED))
    hard, laid_hard = _shaded(pastels.hard(RED))
    assert 0.6 * laid_hard < laid < 0.95 * laid_hard
    assert _dust(hard) - 0.2 < _dust(pencil) < _dust(hard) - 0.04
    # but it is a pastel still, far dustier than a coloured pencil: a finger
    # moves it and a kneaded eraser lifts most of it
    waxy, _ = _shaded(pencils.coloured(RED))
    assert _dust(pencil) > 0.4 > 0.15 > _dust(waxy)
    assert _carried_out(pencil.copy()) > 1.5 * _carried_out(waxy.copy())
    assert _left_by_an_eraser(pencil) < 0.5 < _left_by_an_eraser(waxy)


def test_a_pastel_pencil_covers_as_a_pastel_does():
    def lightened(make) -> float:
        """How many times lighter a layer of white makes two of a dark."""
        sheet, _ = _shaded(make("#1f2a44"))
        dark = _luminance(sheet)
        sheet.shade(BOX, make("#f4f1ea"), 0.8, 8.0, angle=-30)
        return _luminance(sheet) / dark

    # opaque: a white one lightens a dark one, as no coloured pencil does
    assert lightened(pastels.pencil) > 1.5
    assert lightened(pastels.pencil) > 1.25 * lightened(pencils.coloured)


def test_the_side_of_a_pastel_pencil_is_a_cone_and_its_band_fades():
    pencil, stick = pastels.pencil(RED), pastels.hard(RED)
    assert not pencil.flat_side and pencil.side == pencils.HB.side
    assert stick.flat_side

    def band(medium) -> np.ndarray:
        sheet = Sheet(400, 200, paper=LEVEL, seed=3)
        sheet.stroke([(60, 100), (340, 100)], medium, 0.6, 4.0, 1.0)
        return _across(sheet)

    faded, even = band(pencil), band(stick)
    assert _full_share(faded, 4.0 * pencil.side) < 0.6
    assert _full_share(even, 4.0 * stick.side) > 0.7
    # darkest down the middle, and less and less towards each edge
    assert faded[100] > faded[95] > faded[92] and faded[100] > faded[105] > faded[108]
    # held upright it draws with its point
    upright = Sheet(400, 200, paper=LEVEL, seed=3)
    upright.stroke([(60, 100), (340, 100)], Stick(pencil, width=3, lead=8), 0.6)
    rows = np.count_nonzero(upright.pigment()[:, 70:90].sum(axis=1))
    assert 3 <= rows <= 6


# --------------------------------------------------------------------------
# a Conté crayon: firmer than a hard pastel, and it stays put


def test_a_conte_crayon_is_firmer_than_a_hard_pastel_and_stays_put():
    crayon, laid = _shaded(conte.SANGUINE)
    hard, laid_hard = _shaded(pastels.hard(RED))
    soft, laid_soft = _shaded(pastels.soft(RED))
    assert laid < 0.8 * laid_hard < 0.5 * laid_soft
    assert _dust(crayon) < _dust(hard) - 0.1 < _dust(soft) - 0.2
    # a finger carries off less of it, and an eraser leaves more
    carried = [_carried_out(s.copy()) for s in (crayon, hard, soft)]
    assert carried[0] < 0.85 * carried[1] and carried[0] < 0.7 * carried[2]
    left = [_left_by_an_eraser(s) for s in (crayon, hard, soft)]
    assert left[0] > left[1] + 0.05 > left[2] + 0.1


def test_a_conte_crayon_laid_on_its_side_marks_an_even_band():
    assert all(m.flat_side and m.side == conte.SIDE for m in conte.ALL)
    sheet = Sheet(400, 200, paper=LEVEL, seed=3)
    stick = Stick(conte.SANGUINE, width=6, lead=6)
    assert stick.side == 30
    sheet.stroke([(60, 100), (340, 100)], stick, 0.6, tilt=1.0)
    assert _full_share(_across(sheet), 30) > 0.7


def test_the_colours_run_from_black_to_white():
    tones = [_luminance(_shaded(m)[0]) for m in conte.ALL]
    assert tones == sorted(tones)
    assert tones[0] < 0.2 < 0.6 < tones[-1]

    # sanguine is red, bistre a yellower brown and sepia a duller one
    def colour(medium) -> np.ndarray:
        spectrum = _shaded(medium)[0].reflectance()[INSIDE].mean(axis=(0, 1))
        return sp.reflectance_to_linear_rgb(spectrum.astype(np.float64))

    red, brown, dull = colour(conte.SANGUINE), colour(conte.BISTRE), colour(conte.SEPIA)
    assert red[0] / red[1] > brown[0] / brown[1] > dull[0] / dull[1] > 1.0


@pytest.mark.parametrize("paper", [papers.TONED_TAN, papers.TONED_GREY])
def test_trois_crayons_on_a_toned_paper(paper):
    # the paper is the middle tone: white is well above it in one layer and
    # more so in two, sanguine below it, black far below
    bare = _luminance(Sheet(200, 150, paper=paper, seed=1))
    once = _luminance(_shaded(conte.WHITE, paper, 1)[0])
    white = _luminance(_shaded(conte.WHITE, paper)[0])
    red = _luminance(_shaded(conte.SANGUINE, paper)[0])
    black = _luminance(_shaded(conte.BLACK, paper)[0])
    assert once > 1.4 * bare and white > 1.7 * bare
    assert black < 0.5 * red < 0.3 * bare
    # white over black greys it, and is far from white on the paper
    sheet, _ = _shaded(conte.BLACK, paper)
    sheet.shade(BOX, conte.WHITE, 0.8, 8.0, angle=-30)
    assert 1.3 * black < _luminance(sheet) < 0.5 * white

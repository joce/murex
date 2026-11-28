"""fusain on the shared paper: its names for it, its sizes restated in
millimetres at exactly 4 px/mm (the same tooth to the bit), and a tone on a
pebbled paper."""

import numpy as np

import murex
from murex import paper as shared
from murex.fusain import Paper, Sheet, charcoal, papers
from murex.fusain.sheet import PX_PER_MM

#: Each preset's grain as it was, in pixels, before sizes were millimetres.
GRAIN_IN_PIXELS = {
    "cartridge": 3.0,
    "printer paper": 1.5,
    "bristol": 2.0,
    "newsprint": 2.5,
    "Ingres": 3.0,
    "charcoal paper": 4.0,
    "cold-pressed": 5.0,
    "rough": 8.0,
    "sanded card": 2.0,
    "toned grey": 3.0,
    "toned tan": 3.0,
    "black": 3.0,
}
MAKE = {
    "wove": shared._wove,
    "laid": shared._laid,
    "rough": shared._rough,
    "pebbled": shared._pebbled,
    "sanded": shared._sanded,
}


def test_fusain_s_names_point_to_the_shared_paper():
    assert Paper is murex.Paper
    assert papers.INGRES is murex.papers.INGRES
    assert papers.Paper is murex.Paper
    # its list is the papers it drew on before the wet media's joined them
    assert [p.name for p in papers.ALL] == list(GRAIN_IN_PIXELS)
    assert {*papers.ALL, papers.HOT_PRESSED, papers.XUAN} == set(murex.papers.ALL)


def test_fusain_draws_at_4_px_per_mm_and_its_grains_are_a_quarter_of_its_pixels():
    assert PX_PER_MM == 4.0
    for paper in papers.ALL:
        assert paper.grain * PX_PER_MM == GRAIN_IN_PIXELS[paper.name], paper.name
        assert paper.grain == GRAIN_IN_PIXELS[paper.name] / 4, paper.name
    assert Paper().grain * PX_PER_MM == 3.0


def test_a_sheet_s_tooth_is_the_tooth_it_had_in_pixels_to_the_bit():
    # what the textures drew from a grain in pixels, they draw from the
    # paper's grain at fusain's scale: the same arrays, bit for bit
    for paper in papers.ALL:
        for seed in (1, 6):
            sheet = Sheet(83, 57, paper=paper, seed=seed)
            rng = np.random.default_rng(seed)
            raw = MAKE[paper.texture](57, 83, GRAIN_IN_PIXELS[paper.name], rng)
            before = shared._unit(raw).astype(np.float32)
            np.testing.assert_array_equal(sheet.tooth, before)


def test_a_charcoal_tone_on_pebbled_paper_is_neither_flecked_nor_blotchy():
    def tone(texture):
        paper = papers.CHARCOAL.with_(texture=texture)
        sheet = Sheet(260, 200, paper=paper, seed=2)
        for angle in (35, -30):
            sheet.shade((10, 10, 250, 190), charcoal.VINE, 0.3, 14.0, angle)
        grey = sheet.render(lighting=False)[30:170, 30:230].mean(axis=2)
        return grey - grey.mean()

    def patches(grey, size):
        """How much the tone differs between squares ``size`` wide."""
        h, w = grey.shape[0] // size, grey.shape[1] // size
        cut = grey[: h * size, : w * size]
        return cut.reshape(h, size, w, size).mean(axis=(1, 3)).std()

    wove, rough, pebbled = tone("wove"), tone("rough"), tone("pebbled")
    # the paper shows as much in each
    assert 0.8 < pebbled.std() / wove.std() < 1.2
    # squares five grains wide differ far less than on a rough paper...
    assert patches(pebbled, 20) < 0.6 * patches(rough, 20)
    # ...and neighbouring pixels are no less alike than on a wove one
    step = [np.abs(np.diff(t, axis=1)).mean() for t in (wove, pebbled)]
    assert step[1] < step[0]

"""A stroke's random textures do not show how it is cut into steps
(murex-9t4): the wobble of its width, a knife's chatter, the swell of its
lips, the tilt of its blade, its colour bands and the hair are drawn against
the distance along the path, as many random numbers as the length of the
path calls for, and read where each point lies.

The wobble counted its noise in steps, so a stroke cut otherwise drew more
or fewer numbers there, and every texture drawn after it was another: as a
different seed makes it.
"""

import numpy as np
import pytest

import murex.huile.stroke as stm
from murex.huile import Brush, Canvas, brushes
from murex.huile import palette as P

CAPS = (8.0, 4.0, 2.0, 1.0)
CURVE = [(60.0, 70.0), (200.0, 120.0), (350.0, 225.0)]
BEND = [(60.0, 60.0), (230.0, 80.0), (250.0, 230.0)]

#: The tools: (brush type, the stroke's other settings).
TOOLS = {
    "knife": (brushes.knife("straight", 60, flex=0.5), {"lift": 0.0}),
    "wide knife": (
        brushes.knife("straight", 110, flex=0.5),
        {"lift": 0.0, "angle": -40, "follow_path": False, "pressure": 0.05},
    ),
    "flat": (brushes.FLAT_HOG.sized(30), {}),
    # (a soft round splays under pressure, and this one is pressed harder
    # and grows wider along its way)
    "round": (
        brushes.ROUND_SABLE.sized(16),
        {"pressure": [0.2, 0.9, 0.4], "width": [10.0, 22.0, 14.0], "taper": 0.2},
    ),
}


def _textures(monkeypatch, canvas, cap, tool, path, **how):
    """Paint a stroke of ``tool`` along ``path`` on ``canvas`` in steps of
    ``cap`` px at most, and return its textures: what it drew, where its
    points lie along it, and the state of its random numbers once all but
    the peaks of its end are drawn."""
    seen = {}
    textures, init = stm._stroke_textures, stm._Run.__init__

    def spy(rng, bt, smp):
        seen["tex"] = textures(rng, bt, smp)
        return seen["tex"]

    def begun(self, *args):
        init(self, *args)
        seen["run"] = self
        seen["drawn"] = self.rng.bit_generator.state

    bt, settings = TOOLS[tool]
    brush = Brush(bt)
    if bt.rigid:
        brush.load(P.TITANIUM_WHITE, 1.0)
    with monkeypatch.context() as m:
        m.setattr(stm, "_MAX_STEP", cap)
        m.setattr(stm, "_stroke_textures", spy)
        m.setattr(stm._Run, "__init__", begun)
        canvas.stroke(
            path,
            None if bt.rigid else P.TITANIUM_WHITE,
            brush=brush,
            **{"amount": 5.0, **settings, **how},
        )
    run, tex = seen["run"], seen["tex"]
    return {
        "arc": np.asarray(run.arc),
        "wobble": tex.wobble,
        "chatter": tex.chatter,
        "lip": tex.lip,
        "tilt": tex.blade_tilt,
        "bands": run.blade.bands if bt.rigid else None,
        "hair": np.asarray(run.tex2),
        "hair_at": (run.K.hair_s0, run.K.hair_x0, run.K.hair_ds, run.K.hair_dx),
        "lift_var": run.lift_var,
        "lift_reach": run.lift_reach,
        "width": brush.width,
        "w_typ": run.w_typ,
        "drawn": seen["drawn"],
    }


def _same_draws(a, b):
    """The textures ``a`` and ``b`` of two strokes are the same draws: the
    same numbers taken from the generator, the same tilt, bands and hair,
    lying at the same place."""
    assert a["drawn"] == b["drawn"]
    assert a["tilt"] == b["tilt"]
    assert a["lift_var"] == b["lift_var"]
    assert a["hair_at"] == b["hair_at"]
    assert np.array_equal(a["hair"], b["hair"])
    if a["bands"] is not None:
        assert np.array_equal(a["bands"], b["bands"])


@pytest.mark.parametrize("path", [CURVE, BEND], ids=["curve", "bend"])
@pytest.mark.parametrize("tool", list(TOOLS))
def test_a_stroke_has_the_same_textures_at_every_cut(monkeypatch, tool, path):
    """The same stroke with its steps capped at 8, 4, 2 and 1 px (and half
    a pixel, a knife's): it draws the same random numbers, its blade tilts
    as much, its bands and its hair are the same arrays at the same place,
    it starts lifting off as far before its end, and a load is measured in
    the same width. Its wobble, chatter and lips are the same along its
    length: at each point of a coarse cut, what the finest cut has there,
    as near as the noise changes over three quarters of a pixel (the points
    of the finest cut lie half a pixel or a pixel apart, and a path cut
    finer is a little longer where it bends), where another draw would be
    anything up to 1 away."""
    caps = (*CAPS, 0.5) if TOOLS[tool][0].rigid else CAPS
    got = {
        cap: _textures(monkeypatch, Canvas(420, 300, seed=1), cap, tool, path, seed=5)
        for cap in caps
    }
    fine = got[caps[-1]]
    assert len(fine["arc"]) >= len(got[8.0]["arc"])
    assert np.ptp(fine["wobble"]) > 0.2 and np.ptp(fine["chatter"]) > 0.2
    for cap in caps[:-1]:
        cut = got[cap]
        _same_draws(cut, fine)
        assert cut["lift_reach"] == fine["lift_reach"]
        assert cut["width"] == fine["width"]
        # (a path cut finer is a little longer where it bends: the end of
        # the stroke lies within a fraction of a pixel of where it lay)
        assert cut["arc"][-1] == pytest.approx(fine["arc"][-1], abs=0.5)
        w = fine["w_typ"]
        # (how far each goes from one random number to the next, px: see
        # stroke._stroke_textures; at its steepest it changes by 1.5 over that)
        cells = {"wobble": 0.8 * w, "chatter": 0.4 * w, "lip": 0.8 * w}
        for name, cell in cells.items():
            there = np.interp(cut["arc"], fine["arc"], fine[name])
            near = 1.5 / cell * 0.75
            assert near < 0.2
            assert np.abs(cut[name] - there).max() < near, (cap, name)


@pytest.mark.parametrize("tool", ["knife", "flat"])
def test_a_second_stroke_does_not_show_how_the_first_was_cut(monkeypatch, tool):
    """Two strokes on a canvas, neither with a seed of its own: the second
    has the same textures whether the first was painted in steps of 8 px or
    of 1 px."""
    second = []
    for cap in (8.0, 1.0):
        canvas = Canvas(420, 300, seed=3)
        _textures(monkeypatch, canvas, cap, tool, CURVE)
        second.append(_textures(monkeypatch, canvas, 8.0, tool, BEND))
    _same_draws(*second)
    for name in ("arc", "wobble", "chatter", "lip"):
        assert np.array_equal(second[0][name], second[1][name]), name


@pytest.mark.parametrize("tool", ["wide knife", "flat"])
def test_a_stroke_draws_as_many_numbers_whichever_way_its_length_rounds(
    monkeypatch, tool
):
    """A stroke 40 px wide and 328 px long, which with the three steps of
    8 px its wobble is drawn for past its end is a whole number of the
    wobble's cells (32 px), and one 320 px long, a whole number of the
    cells of its chatter (16 px), of its lips (32 px) and of a knife's
    bands (20 px): with its end an ulp nearer or further each draws the
    same random numbers."""
    for end in (348.0, 340.0):
        drawn = set()
        for x in (end, np.nextafter(end, 0.0), np.nextafter(end, 999.0)):
            path = [(20.0, 150.0), (float(x), 150.0)]
            canvas = Canvas(420, 300, seed=1)
            got = _textures(monkeypatch, canvas, 8.0, tool, path, seed=5, width=40)
            drawn.add(str(got["drawn"]))
        assert len(drawn) == 1, end


def test_a_stroke_is_painted_in_its_own_steps_unless_it_is_cut_shorter():
    """The longest step a stroke is painted in is the longest of its own
    (see stroke._MAX_STEP for what would go wrong if they parted)."""
    assert stm._MAX_STEP == stm._OWN_STEP == 8.0


def _sampled(stroke):
    _, bt, eff = stm._resolve(stroke)
    return bt, stm._sample_stroke(stm.as_path(stroke.path), stroke, bt, eff)


def test_a_stroke_in_its_own_steps_is_its_own_reference(monkeypatch):
    """A stroke painted in its own steps is not sampled twice: what its
    textures are sized by is its samples themselves. Cut shorter, it is
    sized by the same."""
    stroke = stm.Stroke(
        [(20.0, 30.0), (100.0, 80.0), (180.0, 60.0)],
        P.TITANIUM_WHITE,
        brush=brushes.ROUND_HOG.sized(24),
    )
    _, own = _sampled(stroke)
    assert own.own.arc is own.arc and own.own.widths is own.widths
    monkeypatch.setattr(stm, "_MAX_STEP", 1.0)
    _, cut = _sampled(stroke)
    assert len(cut.pts) > 4 * len(own.pts)
    for a, b in zip(cut.own, own.own, strict=True):
        assert np.array_equal(a, b)
    # (the length its textures cover is the path's: no cut is longer)
    assert own.arc[-1] < cut.arc[-1] <= own.own.length + 1e-9


def test_the_wobble_is_as_long_in_pixels_as_it_was():
    """The width's wobble turns every 0.8 widths, as it did in a stroke's
    own steps when it was counted in them: a brush 40 px wide draws a
    number for every 32 px of its way (and of three steps of 8 px more, and
    three to spare), and reads them there."""
    drawn = []

    class Counting:
        def random(self, n):
            drawn.append(n)
            return np.linspace(0.0, 1.0, n)

        def normal(self, *_):
            return 0.0

    stroke = stm.Stroke(
        [(10.0, 20.0), (250.0, 20.0)],
        P.TITANIUM_WHITE,
        brush=brushes.FLAT_HOG.sized(40),
    )
    bt, smp = _sampled(stroke)
    tex = stm._stroke_textures(Counting(), bt, smp)
    assert drawn[0] == (240 + 24) // 32 + 3 == 11
    # (the numbers go up by a tenth from one to the next: so does the
    # wobble, every 32 px)
    at = [list(smp.arc).index(s) for s in (32.0, 64.0, 160.0)]
    assert tex.wobble[at] + 0.5 == pytest.approx([0.1, 0.2, 0.5], abs=1e-12)

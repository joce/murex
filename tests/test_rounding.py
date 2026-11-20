"""Counts worked out from lengths do not hang on the last bit of an input
(``murex._rounding``): a path's points, the numbers a noise draws."""

import math

import numpy as np
import pytest

from murex import Bezier, CatmullRom, Polyline, _rounding, noise, spline
from murex._rounding import WHOLE_SLACK, whole_ceil, whole_floor


def _nudged(x: float) -> tuple[float, float, float]:
    return math.nextafter(x, -math.inf), x, math.nextafter(x, math.inf)


def test_a_ratio_a_hair_from_a_whole_number_counts_as_that_number():
    for whole in (1.0, 8.0, 600.0, 12345.0):
        for x in _nudged(whole):
            assert whole_floor(x) == whole_ceil(x) == whole
    assert whole_floor(7.5) == 7 and whole_ceil(7.5) == 8
    assert whole_floor(8 - 6e-6) == 7 and whole_ceil(8 + 6e-6) == 9


def test_the_kernel_of_spline_is_compiled_with_the_same_slack():
    # (written out in spline.py: its kernel compiles it in)
    assert spline._WHOLE_SLACK == _rounding.WHOLE_SLACK == WHOLE_SLACK


def test_a_path_is_cut_into_as_many_points_whichever_way_its_length_rounds():
    # 1500 px every 2.5 px: 600 steps. A spacing a last bit under 2.5 (as a
    # medium works it out from a width) used to make that 601.
    path = Polyline([(50.0, 30.0), (1550.0, 30.0)])
    counts = {len(path.sample(spacing)[0]) for spacing in _nudged(2.5)}
    assert counts == {601}
    for end in _nudged(1550.0):
        assert len(Polyline([(50.0, 30.0), (end, 30.0)]).sample(2.5)[0]) == 601


@pytest.mark.parametrize("closed", [False, True])
def test_a_curve_has_as_many_dense_points_whichever_way_a_chord_rounds(closed):
    # chords of 40 px: 21 points each, whatever rounding leaves of the 40
    counts = set()
    for x in _nudged(40.0):
        points = [(0.0, 0.0), (x, 0.0), (x, 40.0), (0.0, 40.0)]
        counts.add(len(CatmullRom(points, closed=closed)._dense()[0]))
        counts.add(len(CatmullRom(points, closed=closed)._dense_general()[0]))
    assert len(counts) == 1


def test_a_bezier_has_as_many_dense_points_whichever_way_its_length_rounds():
    counts = set()
    for x in _nudged(60.0):  # handles on the chord: 60 px, 31 points
        points = [(0, 0), (x / 3, 0), (2 * x / 3, 0), (x, 0)]
        counts.add(len(Bezier(points)._dense()[0]))
    assert counts == {32}


def test_a_noise_draws_as_many_numbers_whichever_way_its_cells_round():
    drawn = set()
    for cell in _nudged(0.1):  # 100 / 0.1: 1000 cells, or 999.9999999999999
        rng = np.random.default_rng(1)
        noise.value_noise_1d(100, cell, rng)
        drawn.add(float(rng.random()))
    assert len(drawn) == 1

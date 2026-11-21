"""What makes murex fast changes no result: the compiled Kubelka-Munk of a
batch of layers, and a path that keeps its dense points and works them out
in compiled code, give to the last bit what numpy gave in murex 0.1.1.

The code of murex 0.1.1 is kept here to compare with, as it was but for two
things: fusain and huile check their pictures byte for byte, so that is the
test. One is how a path counts its points: since huile's fix came into the
shared modules, a ratio within ``WHOLE_SLACK`` of a whole number counts as
that number (see ``murex._rounding``), here as there. The other is ``tanh``:
murex's own (``murex._libm``), not numpy's, which rounds some values
differently from one processor to another."""

import copy
import pickle
import warnings
from typing import Any

import numpy as np
import pytest

from murex import Bezier, CatmullRom, Path, Polyline, spline
from murex import _libm
from murex import spectral as sp
from murex._rounding import WHOLE_SLACK, whole_ceil, whole_floor

N = sp.N_BANDS

# --------------------------------------------------------------------------
# murex 0.1.1, as it was (but for the counts of a path's points, and tanh)
# --------------------------------------------------------------------------


def km_layer_011(kappa, sigma, ground):
    kappa = np.maximum(np.asarray(kappa), 0.0)
    sigma = np.maximum(np.asarray(sigma), 0.0)
    if sigma.ndim == kappa.ndim - 1:
        sigma = sigma[..., None]
    B = np.sqrt(kappa * kappa + 2.0 * kappa * sigma)
    small = B < 1e-4
    tanh = _libm.np_tanh(B)  # (murex's own tanh, the same on every machine)
    tau = np.where(small, 1.0 - B * B / 3.0, tanh / np.where(small, 1.0, B))
    num = sigma * tau - ground * ((sigma + kappa) * tau - 1.0)
    den = (sigma + kappa - ground * sigma) * tau + 1.0
    return num / den


def sample_011(path, spacing):
    pts, knot = dense_011(path)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    length = s[-1]
    if length < 1e-9:
        p = pts[:1]
        return p, np.array([[1.0, 0.0]]), np.zeros(1), knot[:1]
    n = max(2, whole_ceil(length / max(spacing, 1e-3)) + 1)
    si = np.linspace(0.0, length, n)
    out = np.stack([np.interp(si, s, pts[:, 0]), np.interp(si, s, pts[:, 1])], -1)
    k = np.interp(si, s, knot)
    tan = np.gradient(out, axis=0)
    tan /= np.maximum(np.linalg.norm(tan, axis=1, keepdims=True), 1e-12)
    return out, tan, si / length, k


def length_011(path):
    pts, _ = dense_011(path)
    return float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())


def dense_011(path):
    if isinstance(path, CatmullRom):
        return _catmull_dense_011(path.points, path.alpha, path.closed)
    if isinstance(path, Bezier):
        return _bezier_dense_011(path.points, path.n_knots)
    if isinstance(path, Polyline):
        return path.points.copy(), np.arange(len(path.points), dtype=np.float64)
    return path._dense()


def _catmull_dense_011(P, alpha, closed):
    if len(P) == 1:
        return P.copy(), np.zeros(1)
    if closed:
        P = np.vstack([P[-1], P, P[0], P[1]])
    else:  # reflect end points to get natural end tangents
        P = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    # all segments at once: segment i runs from P[i + 1] to P[i + 2]
    p0, p1, p2, p3 = P[:-3], P[1:-2], P[2:-1], P[3:]
    # samples per segment
    half = np.linalg.norm(p2 - p1, axis=1) / 2
    m = np.maximum(8, np.floor(half + WHOLE_SLACK).astype(int) + 1)
    seg = np.repeat(np.arange(len(m)), m)
    # 0..1 within each
    t = (np.arange(m.sum()) - np.repeat(np.cumsum(m) - m, m)) * (1.0 / m[seg])
    pts = _catmull_segment_011(p0[seg], p1[seg], p2[seg], p3[seg], t, alpha)
    return np.vstack([pts, P[-2][None]]), np.concatenate([seg + t, [float(len(P) - 3)]])


def _catmull_segment_011(p0, p1, p2, p3, t, alpha):
    def tj(ti, a, b):
        return ti + np.maximum(np.linalg.norm(b - a, axis=1), 1e-6) ** alpha

    t0 = 0.0
    t1 = tj(t0, p0, p1)
    t2 = tj(t1, p1, p2)
    t3 = tj(t2, p2, p3)
    tt = t1 + (t2 - t1) * t
    t1, t2, t3, tt = t1[:, None], t2[:, None], t3[:, None], tt[:, None]
    a1 = (t1 - tt) / (t1 - t0) * p0 + (tt - t0) / (t1 - t0) * p1
    a2 = (t2 - tt) / (t2 - t1) * p1 + (tt - t1) / (t2 - t1) * p2
    a3 = (t3 - tt) / (t3 - t2) * p2 + (tt - t2) / (t3 - t2) * p3
    b1 = (t2 - tt) / (t2 - t0) * a1 + (tt - t0) / (t2 - t0) * a2
    b2 = (t3 - tt) / (t3 - t1) * a2 + (tt - t1) / (t3 - t1) * a3
    return (t2 - tt) / (t2 - t1) * b1 + (tt - t1) / (t2 - t1) * b2


def _bezier_dense_011(P, n_knots):
    pts, knots = [], []
    for i in range(n_knots - 1):
        p0, p1, p2, p3 = P[3 * i : 3 * i + 4]
        approx = (
            np.linalg.norm(p1 - p0) + np.linalg.norm(p2 - p1) + np.linalg.norm(p3 - p2)
        )
        count = max(8, whole_floor(float(approx) / 2) + 1)
        t = np.linspace(0.0, 1.0, count, endpoint=False)[:, None]
        mt = 1 - t
        pts.append(mt**3 * p0 + 3 * mt * mt * t * p1 + 3 * mt * t * t * p2 + t**3 * p3)
        knots.append(i + t[:, 0])
    pts.append(P[-1][None])
    knots.append(np.array([float(n_knots - 1)]))
    return np.vstack(pts), np.concatenate(knots)


# --------------------------------------------------------------------------
# to the bit
# --------------------------------------------------------------------------


def same(got, want) -> bool:
    """Whether two results are one: the same type, and for arrays the same
    dtype, shape and bytes (so -0.0 is not 0.0), lying in memory in the same
    order (which what is worked out from them next, a sum or a product of
    matrices, may depend on to the last bit).

    A value that is not a number must be one in both, but any NaN will do:
    which of two NaN an operation returns (they differ by a sign, or more)
    is a matter of the order a compiler gave its operands, not of arithmetic,
    and numpy itself does not always answer the same from version to version.
    """
    if type(got) is not type(want):
        return False
    if isinstance(want, tuple):
        return len(got) == len(want) and all(map(same, got, want))
    if isinstance(want, str):
        return got == want
    if isinstance(want, float):
        return _bits(np.float64(got)) == _bits(np.float64(want))
    return (
        got.dtype == want.dtype
        and got.shape == want.shape
        and _bits(got) == _bits(want)
        and got.flags.c_contiguous == want.flags.c_contiguous
        and got.flags.f_contiguous == want.flags.f_contiguous
    )


def _bits(values) -> bytes:
    """Every bit of some numbers, with one NaN for all of them."""
    if values.dtype.kind in "fc":
        values = np.where(np.isnan(values), np.nan, values)
    return values.tobytes()


def quietly(function, *arguments):
    """What ``function`` returns, without numpy's warnings (the code of
    0.1.1 warns where a result is infinite or not a number)."""
    with warnings.catch_warnings(), np.errstate(all="ignore"):
        warnings.simplefilter("ignore")
        return function(*arguments)


# --------------------------------------------------------------------------
# Kubelka-Munk layers
# --------------------------------------------------------------------------


def _layers(rng, shape, bands=N):
    """Layers of every kind Kubelka-Munk tells apart: kappa (*shape, bands)
    and sigma (*shape)."""
    kappa = rng.uniform(0.0, 3.0, (*shape, bands))
    sigma = rng.uniform(0.0, 4.0, shape)
    k, s = kappa.reshape(-1, bands), sigma.reshape(-1)
    k[::13] *= 1e-6  # thin: the series for a small depth
    k[1::13], s[1::13] = 0.0, 0.0  # zero thickness: the ground shows as it was
    s[2::13] = 0.0  # zero scattering, a dye: Beer-Lambert
    k[3::13] *= 40.0  # thick and dark
    s[3::13] *= 40.0
    k[4::13, : bands // 2 + 1] = -1e-9  # what rounding may leave below nothing
    s[5::13] = -1e-9
    k[6::13], s[6::13] = -0.0, -0.0  # nothing, with a minus sign
    k[7::13] = rng.uniform(0.0, 3e-4, k[7::13].shape)  # about where the series
    s[7::13] = rng.uniform(0.0, 3e-4, s[7::13].shape)  # takes over (B = 1e-4)
    k[8::13] *= 1e-310  # subnormal
    k[9::13] *= 1e3  # opaque: tanh is 1
    k[10::13] = 0.0  # no absorption: a white scatterer
    k[11::13, ::2] = 0.0  # ... in every other band
    return kappa, sigma


def _grounds(rng, shape, bands=N):
    """A ground for each layer: any reflectance, with the ends of the range
    and a little beyond."""
    ground = rng.uniform(0.0, 1.0, (*shape, bands))
    g = ground.reshape(-1, bands)
    g[::17] = 1.0
    g[5::17] = 0.0
    g[9::17] = sp.MIN_REFLECTANCE
    g[13::17] *= 1.05  # (rounding may leave a reflectance a hair above 1)
    g[15::17, ::3] = -0.0
    return ground


SHAPES = [(1,), (2,), (7,), (1359,), (1360,), (1361,), (2721,), (4099,)]
SHAPES += [(3, 5), (40, 70), (2, 3, 4), (1, 1), (5, 1, 300)]


@pytest.mark.parametrize("shape", SHAPES, ids=str)
@pytest.mark.parametrize("seed", range(2))
def test_a_layer_over_a_ground_for_each_is_what_numpy_gave_to_the_bit(shape, seed):
    rng = np.random.default_rng(seed)
    kappa, sigma = _layers(rng, shape)
    ground = _grounds(rng, shape)
    assert sp._is_batch(kappa, sigma, ground)
    want = km_layer_011(kappa, sigma, ground)
    assert same(sp.km_layer(kappa, sigma, ground), want)
    # a second layer over the first, as a picture is rendered
    more, more_sigma = _layers(rng, shape)
    assert same(
        sp.km_layer(more, more_sigma, sp.km_layer(kappa, sigma, ground)),
        km_layer_011(more, more_sigma, want),
    )
    # over one ground for all, of any float type
    for dtype in (np.float64, np.float32, np.float16):
        paper = rng.uniform(0.2, 1.0, N).astype(dtype)
        assert sp._is_batch(kappa, sigma, paper)
        assert same(sp.km_layer(kappa, sigma, paper), km_layer_011(kappa, sigma, paper))
    # and a ground for each that is not float64
    for dtype in (np.float32, np.float16, ">f8"):
        other = ground.astype(dtype)
        assert sp._is_batch(kappa, sigma, other)
        assert same(sp.km_layer(kappa, sigma, other), km_layer_011(kappa, sigma, other))


@pytest.mark.parametrize("bands", [1, 2, 3, 5, 7, 8, 16, 31, 100, 3000])
def test_any_number_of_bands(bands):
    rng = np.random.default_rng(bands)
    for shape in [(1,), (33,), (700,), (4, 9)]:
        kappa, sigma = _layers(rng, shape, bands)
        ground = _grounds(rng, shape, bands)
        assert sp._is_batch(kappa, sigma, ground)
        want = km_layer_011(kappa, sigma, ground)
        assert same(sp.km_layer(kappa, sigma, ground), want)
        one = ground.reshape(-1, bands)[0].copy()
        assert same(sp.km_layer(kappa, sigma, one), km_layer_011(kappa, sigma, one))


@pytest.mark.parametrize("bands", [1, 3, 5, 7, 24, 29])
def test_layers_taken_a_few_at_a_time(bands, monkeypatch):
    """The layers are worked out some at a time (tanh on each lot):
    with lots of 16 layers, every count of layers there is around a few
    lots gives what the whole batch gives at once."""
    monkeypatch.setattr(sp, "_KM_VALUES", 16 * bands)
    rng = np.random.default_rng(bands)
    for count in [*range(1, 70), 127, 128, 129, 1000]:
        kappa, sigma = _layers(rng, (count,), bands)
        ground = _grounds(rng, (count,), bands)
        want = km_layer_011(kappa, sigma, ground)
        assert same(sp.km_layer(kappa, sigma, ground), want)
        out = ground.copy()
        assert sp.km_layer(kappa, sigma, out, out=out) is out
        assert same(out, want)
        one = ground[count // 2].copy()
        assert same(sp.km_layer(kappa, sigma, one), km_layer_011(kappa, sigma, one))


def test_the_layers_of_a_sheet_of_fusain():
    """As fusain packs them: K per band, then S, then what Kubelka-Munk does
    not read, a row for each pixel that is marked; laid over what is seen
    there, one layer over the other, and ink over the bare paper."""
    rng = np.random.default_rng(3)
    count, scattering = 64 * 1120 // 9, N
    paper = rng.uniform(0.3, 1.0, N).astype(np.float32)
    seen = np.empty((count, N))
    seen[:] = paper
    in_place, want = seen.copy(), seen.copy()
    for _ in range(3):  # held, under and loose
        packed = np.zeros((count, N + 3))
        packed[:, :N], packed[:, scattering] = _layers(rng, (count,))
        packed /= rng.uniform(1e-6, 1.0, count)[:, None]  # (the covered share)
        kappa, sigma = packed[:, :N], packed[:, scattering]
        assert not kappa.flags.c_contiguous and sp._is_batch(kappa, sigma, seen)
        want = km_layer_011(kappa, sigma, want)
        seen = sp.km_layer(kappa, sigma, seen)
        assert same(seen, want)
        # in place, as fusain's own compiled copy did it
        assert sp.km_layer(kappa, sigma, in_place, out=in_place) is in_place
        assert same(in_place, want)
        assert same(sp.km_layer(kappa, sigma, paper), km_layer_011(kappa, sigma, paper))


def _memory_layouts(array):
    """The same values laid out in memory in other ways."""
    wide = np.full((array.shape[0], array.shape[1] + 5), 7.5)
    wide[:, 2:-3] = array
    spaced = np.full((2 * array.shape[0], array.shape[1]), 7.5)
    spaced[::2] = array
    columns = np.full((array.shape[0], 2 * array.shape[1]), 7.5)
    columns[:, ::2] = array
    read_only = array.copy()
    read_only.flags.writeable = False
    return {
        "a slice of the columns": wide[:, 2:-3],
        "every other row": spaced[::2],
        "every other column": columns[:, ::2],
        "backwards": array[::-1, ::-1][::-1, ::-1],
        "rows backwards": array[::-1].copy()[::-1],
        "by columns": np.asfortranarray(array),
        "read only": read_only,
    }


def test_however_the_layers_lie_in_memory():
    rng = np.random.default_rng(4)
    compiled = 0
    for count in (1, 2, 500, 3000):
        kappa, sigma = _layers(rng, (count,))
        ground = _grounds(rng, (count,))
        sigmas = {
            "as it is": sigma,
            "every other": np.stack([sigma, sigma], -1)[:, 0],
            "backwards": sigma[::-1].copy()[::-1],
        }
        for name, k in _memory_layouts(kappa).items():
            for s in sigmas.values():
                for g in _memory_layouts(ground).values():
                    # (numpy lays its result out as kappa lies: only layers
                    # that lie row after row are for the kernels)
                    assert sp._is_batch(k, s, g) == (name != "by columns" or count == 1)
                    compiled += sp._is_batch(k, s, g)
                    assert same(sp.km_layer(k, s, g), km_layer_011(k, s, g))
    assert compiled > 500
    # more than two dimensions, not in one piece, or with their axes swapped
    kappa, sigma = _layers(rng, (6, 50, 7))
    ground = _grounds(rng, (6, 50, 7))
    k, s, g = kappa[::2, :, ::3], sigma[::2, :, ::3], ground[::2, :, ::3]
    assert sp._is_batch(k, s, g)
    assert same(sp.km_layer(k, s, g), km_layer_011(k, s, g))
    assert same(sp.km_layer(k, s, g[::-1, ::-1][::-1, ::-1]), km_layer_011(k, s, g))
    k, s, g = (a.swapaxes(0, 1) for a in (kappa, sigma, ground))
    assert not sp._is_batch(k, s, g)
    assert same(sp.km_layer(k, s, g), km_layer_011(k, s, g))
    k, s = kappa.swapaxes(0, 1).copy(), sigma.swapaxes(0, 1).copy()
    assert sp._is_batch(k, s, g)  # (the ground alone lies otherwise)
    assert same(sp.km_layer(k, s, g), km_layer_011(k, s, g))
    spread = np.broadcast_to(kappa[0, 0, 0], (40, N))  # (one spectrum, read 40 times)
    s, g = sigma[0, :40, 0], ground[0, :40, 0]
    assert not sp._is_batch(spread, s, g)
    assert same(sp.km_layer(spread, s, g), km_layer_011(spread, s, g))


def test_layers_that_are_not_finite():
    rng = np.random.default_rng(5)
    kappa, sigma = _layers(rng, (4000,))
    ground = _grounds(rng, (4000,))
    for array in (kappa, sigma, ground):
        flat = array.reshape(-1)
        at = rng.permutation(flat.size)
        flat[at[:300]] = np.inf
        flat[at[300:600]] = np.nan
        flat[at[600:900]] = -np.inf
        flat[at[900:1200]] = 1e200  # (its square overflows)
        flat[at[1200:1500]] = -np.nan
    want = quietly(km_layer_011, kappa, sigma, ground)
    assert np.isnan(want).sum() > 1000 and np.isfinite(want).sum() > 1000
    assert same(sp.km_layer(kappa, sigma, ground), want)
    paper = ground[7].copy()
    assert same(
        sp.km_layer(kappa, sigma, paper), quietly(km_layer_011, kappa, sigma, paper)
    )


class _Spectra(np.ndarray):
    """An array that is not numpy's own."""


def _not_batches():
    """Arguments that are no batch of plain float64 layers: numpy works
    these out, as it did every call in murex 0.1.1."""
    rng = np.random.default_rng(6)
    kappa, sigma = _layers(rng, (60,))
    ground = _grounds(rng, (60,))
    one = ground[3].copy()
    return {
        "numbers": (0.7, 0.2, 0.9),
        "a spectrum, numbers": (kappa[0], 0.5, 1.0),
        "a spectrum, a ground": (kappa[0], float(sigma[0]), one),
        "a spectrum, sigma an array": (kappa[0], sigma[0], one),
        "a batch, sigma a number": (kappa, 0.5, ground),
        "a batch, sigma per band": (kappa, np.abs(kappa[::-1]) * 0.5, ground),
        "a batch, sigma with its band axis": (kappa, sigma[:, None], ground),
        "a batch, the ground a number": (kappa, sigma, 1.0),
        "a batch, the ground black": (kappa, sigma, 0.0),
        "a batch, the ground per layer": (kappa, sigma, ground[:, :1].copy()),
        "batches, the ground spread": (
            kappa[None] * np.ones((3, 1, 1)),
            sigma[None] * np.ones((3, 1)),
            ground,
        ),
        "float32 layers": (kappa.astype(np.float32), sigma.astype(np.float32), ground),
        "float32 kappa": (kappa.astype(np.float32), sigma, ground),
        "float32 sigma": (kappa, sigma.astype(np.float32), ground),
        "whole numbers": ((kappa * 3).astype(int), sigma.astype(int), ground),
        "an integer ground": (kappa, sigma, (ground > 0.5).astype(int)),
        "the other byte order": (kappa.astype(">f8"), sigma.astype(">f8"), ground),
        "lists": (kappa[:4].tolist(), sigma[:4].tolist(), ground[:4].tolist()),
        "a subclass": (kappa.view(_Spectra), sigma, ground),
        "a ground of a subclass": (kappa, sigma, ground.view(_Spectra)),
        "no layers": (kappa[:0], sigma[:0], ground[:0]),
        "no layers, one ground": (kappa[:0], sigma[:0], one),
        "no bands": (kappa[:, :0], sigma, ground[:, :0]),
    }


@pytest.mark.parametrize("name", _not_batches())
def test_anything_else_is_worked_out_as_it_was(name):
    kappa, sigma, ground = _not_batches()[name]
    assert not sp._is_batch(kappa, sigma, ground)
    want = km_layer_011(kappa, sigma, ground)
    got = sp.km_layer(kappa, sigma, ground)
    assert type(got) is type(want)
    assert same(np.asarray(got), np.asarray(want))
    # and put in an array, if one is given for it
    out = np.full(np.shape(want), 7.5)
    assert sp.km_layer(kappa, sigma, ground, out=out) is out
    assert same(out, np.asarray(want, dtype=np.float64))


def test_layers_that_do_not_fit_are_refused_as_they_were():
    kappa, sigma = _layers(np.random.default_rng(7), (6,))
    for ground in (np.ones((5, N)), np.ones(N + 1)):
        with pytest.raises(ValueError, match="broadcast"):
            sp.km_layer(kappa, sigma, ground)
        with pytest.raises(ValueError, match="broadcast"):
            km_layer_011(kappa, sigma, ground)
    with pytest.raises(ValueError, match="broadcast"):
        sp.km_layer(kappa, sigma[:5], np.ones(N))


def test_the_result_put_where_it_is_asked_for():
    rng = np.random.default_rng(8)
    kappa, sigma = _layers(rng, (2000,))
    ground = _grounds(rng, (2000,))
    want = km_layer_011(kappa, sigma, ground)
    # over the ground itself, or over the layers
    for name in ("ground", "kappa"):
        arrays = {"kappa": kappa.copy(), "sigma": sigma, "ground": ground.copy()}
        assert sp.km_layer(**arrays, out=arrays[name]) is arrays[name]
        assert same(arrays[name], want)
    # in an array of its own, however it lies in memory
    for out in _memory_layouts(np.full(want.shape, 7.5)).values():
        if out.flags.writeable:
            assert sp.km_layer(kappa, sigma, ground, out=out) is out
            assert same(np.ascontiguousarray(out), want)
    # in memory that the layers or the ground share askew: read before written
    room = np.concatenate([ground, ground])
    g, out = room[:2000], room[1:2001]
    assert sp.km_layer(kappa, sigma, g, out=out) is out
    assert same(np.ascontiguousarray(out), want)
    room = np.concatenate([kappa, kappa])
    k, out = room[5:2005], room[:2000]
    want_shifted = km_layer_011(k.copy(), sigma, ground)
    assert sp.km_layer(k, sigma, ground, out=out) is out
    assert same(np.ascontiguousarray(out), want_shifted)
    wide = np.zeros((2000, N + 1))
    wide[:, 0], out = sigma, wide[:, 1:]
    assert sp.km_layer(kappa, wide[:, 0], ground, out=out) is out
    assert same(np.ascontiguousarray(out), want)
    # a view of the ground is the ground's memory too
    seen = ground.copy()
    assert same(sp.km_layer(kappa, sigma, seen, out=seen[:]), want)
    # in an array of another type: converted, as numpy assigns
    out = np.zeros(want.shape, np.float32)
    assert sp.km_layer(kappa, sigma, ground, out=out) is out
    assert same(out, want.astype(np.float32))
    # a ground of float32 over itself
    seen = ground.astype(np.float32)
    want32 = km_layer_011(kappa, sigma, seen).astype(np.float32)
    assert same(sp.km_layer(kappa, sigma, seen, out=seen), want32)
    # more than two dimensions, in one piece or not
    kappa, sigma = _layers(rng, (6, 50))
    ground = _grounds(rng, (6, 50))
    want = km_layer_011(kappa, sigma, ground)
    seen = ground.copy()
    assert same(sp.km_layer(kappa, sigma, seen, out=seen), want)
    room = np.zeros((12, 50, N))
    assert same(
        np.ascontiguousarray(sp.km_layer(kappa, sigma, ground, out=room[::2])), want
    )
    assert not room[1::2].any()
    # and what does not fit, or may not be written, is refused
    with pytest.raises(ValueError):
        sp.km_layer(kappa, sigma, ground, out=np.zeros((6, 49, N)))
    seen = ground.copy()
    seen.flags.writeable = False
    with pytest.raises(ValueError, match="read-only"):
        sp.km_layer(kappa, sigma, ground, out=seen)


def test_the_batch_of_oilpaint_is_what_it_was():
    """``_km_layer_batch``, which oilpaint calls: a batch over one ground,
    or anything else."""
    rng = np.random.default_rng(9)
    paper = rng.uniform(0.2, 1.0, N)
    for shape in [(), (1,), (5000,), (30, 40), (0,)]:
        kappa, sigma = _layers(rng, shape)
        for ground in (paper, paper.astype(np.float32), _grounds(rng, shape), 1.0):
            want = km_layer_011(kappa, sigma, ground)
            assert same(sp._km_layer_batch(kappa, sigma, ground), want)
    kappa, sigma = _layers(rng, (50,))
    for odd in (kappa.astype(np.float32), kappa.view(_Spectra), kappa.tolist()):
        want = km_layer_011(odd, sigma, paper)
        assert same(np.asarray(sp._km_layer_batch(odd, sigma, paper)), np.asarray(want))


def test_the_physics_holds_for_a_batch():
    """What ``tests/test_spectral.py`` checks of one layer, of a batch."""
    rng = np.random.default_rng(10)
    ground = rng.uniform(0.0, 1.0, (500, N))
    K = rng.uniform(0.1, 3.0, (500, N))
    nothing = np.zeros(500)
    assert same(sp.km_layer(K * 0, nothing, ground), ground)
    assert np.allclose(sp.km_layer(K, nothing, ground), ground * np.exp(-2 * K))
    thick = sp.km_layer(K * 200, np.full(500, 400.0), ground)
    assert np.allclose(thick, sp.km_opaque(K, 2.0), atol=1e-4)
    R, T = sp.km_film(K, nothing + 1.5)
    assert np.allclose(
        sp.km_layer(K, nothing + 1.5, ground), R + T**2 * ground / (1 - R * ground)
    )


# --------------------------------------------------------------------------
# paths
# --------------------------------------------------------------------------

SPACINGS = (0.25, 0.375, 0.75, 1.0, 3.7, 1e-9, 1e6)
ALPHAS: tuple[Any, ...] = (
    0.5,
    0.0,
    1.0,
    0.3,
    np.float64(0.5),
    2,
    0.75,
    np.array(0.5),
    np.array([0.5]),
)


def _points(rng, count):
    """Control points as strokes have them: of any size, anywhere, some
    twice, some in line, some on whole pixels."""
    scale = float(rng.choice([1e-7, 0.01, 1.0, 30.0, 400.0, 5000.0]))
    points = rng.normal(0.0, scale, (count, 2)) + rng.choice([0.0, 500.0, -1e4])
    if count > 2 and rng.random() < 0.2:
        points[1] = points[0]
    if count > 2 and rng.random() < 0.1:
        points[:, 1] = 0.0
    if rng.random() < 0.1:
        points = np.round(points)
    if rng.random() < 0.05:
        points[0] = -0.0
    return points


def _paths(seed, count):
    rng = np.random.default_rng(seed)
    for _ in range(count):
        kind = int(rng.integers(0, 5))
        points = _points(rng, int(rng.integers(1, 9)))
        if kind == 0:
            alpha = ALPHAS[int(rng.integers(0, len(ALPHAS)))]
            yield CatmullRom(points, alpha, bool(rng.integers(0, 2)))
        elif kind == 1:
            yield CatmullRom(points)
        elif kind == 2:
            yield spline.as_path(points[:2].tolist())  # a stroke of fusain
        elif kind == 3:
            yield Bezier(_points(rng, 3 * int(rng.integers(1, 4)) + 1))
        else:
            yield Polyline(points)


def _outcome(function, *arguments):
    """What ``function`` returns, or the error it raises (as text)."""
    try:
        return quietly(function, *arguments)
    except (ValueError, OverflowError) as error:
        return f"{type(error).__name__}: {error}"


@pytest.mark.parametrize("seed", range(5))
def test_a_path_is_sampled_as_numpy_sampled_it_to_the_bit(seed):
    rng = np.random.default_rng(seed)
    sampled, failed = 0, 0
    for path in _paths(seed, 300):
        want_length = _outcome(length_011, path)
        for spacing in rng.choice(SPACINGS, 3):
            if want_length / max(spacing, 1e-3) > 1e5:
                continue  # (hundreds of thousands of points)
            # (sampled, sampled again and asked its length, in any order)
            want = _outcome(sample_011, path, float(spacing))
            assert same(_outcome(path.sample, float(spacing)), want)
            assert same(path.length, want_length)
            assert same(_outcome(path.sample, float(spacing)), want)
            sampled += 1
            failed += isinstance(want, str)
    # (a path whose knots run into each other gives points that are not
    # numbers, and cannot be sampled: neither could it be)
    assert sampled > 500 and failed < sampled / 50


def test_the_strokes_of_fusain():
    """A stroke of fusain: two points, sampled at an eighth of its width,
    then asked its length; with a width that varies, sampled every pixel
    first."""
    rng = np.random.default_rng(11)
    for _ in range(300):
        x, y = rng.uniform(0.0, 1100.0, 2)
        dx, dy = rng.normal(0.0, 30.0, 2)
        points = [(x, y), (x + dx, y + dy)]
        line, plain = spline.as_path(points), spline.as_path(points)
        spacing = max(0.25, float(rng.choice([2.0, 3.0, 6.0, 10.0, 24.0])) / 8.0)
        if rng.random() < 0.5:
            assert same(line.sample(1.0), sample_011(plain, 1.0))
        assert same(line.sample(spacing), sample_011(plain, spacing))
        assert same(line.length, length_011(plain))


def test_a_path_that_is_a_point():
    for points in ([(3.0, 4.0)], [(3.0, 4.0)] * 3, [(3.0, 4.0), (3.0, 4.0 + 1e-12)]):
        for path in (
            CatmullRom(points),
            Polyline(points),
            CatmullRom(points, closed=True),
        ):
            want = sample_011(path, 0.5)
            assert len(want[0]) == 1
            assert same(path.sample(0.5), want)
            assert same(path.length, length_011(path))
            # (what it returns is the caller's: the path gives the same again)
            for array in path.sample(0.5):
                array += 9.0
            assert same(path.sample(0.5), want)
    flat = Bezier([(1.0, 1.0)] * 4)
    assert same(flat.sample(0.5), sample_011(flat, 0.5))


class _Counted(CatmullRom):
    """A Catmull-Rom path that counts how often its dense points are worked
    out. (Its ``_state`` is its own: it says they are worked out from the
    same as its parent's.)"""

    worked_out = 0

    def _state(self):
        return super()._state()

    def _dense(self):
        self.worked_out += 1
        return super()._dense()


def test_dense_points_are_worked_out_once():
    points = [(3.0, 4.0), (40.0, 9.0), (55.0, 40.0), (20.0, 60.0)]
    path = _Counted(points)
    first = path.sample(0.75)
    assert path.length == length_011(path)
    assert same(path.sample(0.75), first) and same(
        path.sample(2.0), sample_011(path, 2.0)
    )
    assert path.worked_out == 1
    # what is returned is the caller's to change
    for array in path.sample(0.75):
        array *= 0.0
    assert same(path.sample(0.75), first) and path.worked_out == 1


def test_a_path_that_is_changed_is_worked_out_again():
    given = np.array([(3.0, 4.0), (40.0, 9.0), (55.0, 40.0), (20.0, 60.0)])
    path = _Counted(given)
    path.sample(0.75)
    # the caller's own array, moved in place: it is the path's too
    given += 5.0
    assert same(path.sample(0.75), sample_011(CatmullRom(given), 0.75))
    assert path.worked_out == 2
    path.points[1, 0] = -path.points[1, 0]
    assert same(path.length, length_011(CatmullRom(given)))
    assert path.worked_out == 3
    path.points = given[::-1].copy()
    assert same(path.sample(0.75), sample_011(CatmullRom(given[::-1]), 0.75))
    path.alpha = 1.0
    assert same(path.sample(0.75), sample_011(CatmullRom(given[::-1], 1.0), 0.75))
    path.closed = True
    assert same(path.sample(0.75), sample_011(CatmullRom(given[::-1], 1.0, True), 0.75))
    assert path.worked_out == 6
    # a zero that changes its sign is a change
    path.points[0, 0] = 0.0
    path.sample(0.75)
    path.points[0, 0] = -0.0
    path.sample(0.75)
    assert path.worked_out == 8
    # the other paths too
    for cls, count in ((Polyline, 4), (Bezier, 4)):
        other = cls(given[:count])
        before = other.sample(1.0)
        other.points[2] += 30.0
        assert not same(other.sample(1.0), before)
        assert same(other.sample(1.0), sample_011(cls(other.points), 1.0))
        assert same(other.length, length_011(cls(other.points)))


def test_points_that_are_not_float64_any_more():
    """A path's points are float64 unless they are replaced: numpy then
    works the dense points out, as it did."""
    given = np.array([(3.0, 4.0), (40.0, 9.0), (55.0, 40.0), (20.0, 60.0)])
    for dtype in (np.float32, int, ">f8"):
        for closed in (False, True):
            path = CatmullRom(given, closed=closed)
            path.points = given.astype(dtype)
            assert same(path.sample(0.75), sample_011(path, 0.75))
            assert same(path.length, length_011(path))
    odd: Any = 0.5 + 0j  # (a power that is no plain number)
    path = CatmullRom(given, alpha=odd)
    assert same(_outcome(path.sample, 0.75), _outcome(sample_011, path, 0.75))
    path = CatmullRom(given[::-1][::2])  # (not in one piece in memory)
    assert same(path.sample(0.75), sample_011(path, 0.75))


class _Dense(Path):
    """fusain's way round a path that worked its dense points out at every
    call (fusain 0.3): it implements ``_dense`` and nothing else."""

    def __init__(self, path: Path):
        self._path, self.n_knots = path, path.n_knots
        self._points: tuple[np.ndarray, np.ndarray] | None = None
        self.asked = 0

    def _dense(self) -> tuple[np.ndarray, np.ndarray]:
        self.asked += 1
        if self._points is None:
            self._points = self._path._dense()
        return self._points


class _Shifted(CatmullRom):
    """A path that works its dense points out from more than its parent
    knows of, and does not say so."""

    by = 0.0

    def _dense(self):
        points, knot = super()._dense()
        return points + self.by, knot


class _ShiftedAndSaysSo(_Shifted):
    def _state(self):
        return CatmullRom._state(self), self.by


class _Rough(Path):
    """Dense points that are not a plain array of float64."""

    def __init__(self, dtype):
        self.dtype = dtype

    def _dense(self):
        points = np.array([(0, 0), (30, 40), (30, 100), (-20, 100)], self.dtype)
        return points, np.arange(4.0)


def test_a_path_of_another_kind_is_asked_every_time():
    points = [(3.0, 4.0), (40.0, 9.0), (55.0, 40.0), (20.0, 60.0)]
    once, plain = _Dense(spline.as_path(points)), spline.as_path(points)
    assert same(once.sample(0.75), sample_011(plain, 0.75))
    assert same(once.length, length_011(plain))
    assert same(once.sample(0.75), sample_011(plain, 0.75))
    assert once.asked == 3  # (as before: the path cannot tell what it depends on)
    assert once._state() is None and once._kept is None and not _Dense._keeps
    # a subclass that says nothing of what its dense points depend on is not
    # given stale ones
    shifted = _Shifted(points)
    before = shifted.sample(0.75)
    shifted.by = 100.0
    assert np.allclose(shifted.sample(0.75)[0], before[0] + 100.0, atol=1e-9)
    assert not _Shifted._keeps and _ShiftedAndSaysSo._keeps and CatmullRom._keeps
    told = _ShiftedAndSaysSo(points)
    before = told.sample(0.75)
    assert told._kept is not None
    told.by = 100.0
    assert np.allclose(told.sample(0.75)[0], before[0] + 100.0, atol=1e-9)
    # dense points of another type are measured by numpy, as they were
    for dtype in (np.float32, int, np.float64):
        rough = _Rough(dtype)
        assert same(rough.sample(0.75), sample_011(rough, 0.75))
        assert same(rough.length, length_011(rough))
    with pytest.raises(NotImplementedError):
        Path().sample(1.0)


def test_what_a_path_keeps_is_not_copied_or_pickled():
    points = [(3.0, 4.0), (40.0, 9.0), (55.0, 40.0), (20.0, 60.0)]
    for path in (CatmullRom(points, closed=True), Bezier(points), Polyline(points)):
        fresh = pickle.dumps(path)
        want = path.sample(0.75)
        assert path._kept is not None
        assert pickle.dumps(path) == fresh
        for other in (pickle.loads(fresh), copy.copy(path), copy.deepcopy(path)):
            assert type(other) is type(path) and other._kept is None
            assert same(other.sample(0.75), want)
            assert other.n_knots == path.n_knots
        # a copy does not share its points with the path it was copied from
        moved = copy.deepcopy(path)
        moved.points += 1.0
        assert same(path.sample(0.75), want)
        assert same(moved.sample(0.75), sample_011(moved, 0.75))
        assert not same(moved.sample(0.75), want)


def test_an_alpha_changed_in_place_is_seen():
    points = [(0, 0), (10, 4), (12, 30), (40, 31)]
    alpha: Any = np.array(0.5)
    path = spline.CatmullRom(points, alpha)
    before = path.sample(1.0)[0].copy()
    alpha[...] = 1.0
    after = path.sample(1.0)[0]
    fresh = spline.CatmullRom(points, 1.0)
    assert np.array_equal(after, fresh.sample(1.0)[0])
    assert not np.array_equal(after, before)


class _Slotted(spline.Polyline):
    __slots__ = ("label",)

    def __init__(self, points, label):
        super().__init__(points)
        self.label = label


def test_the_slots_of_a_subclass_are_copied_and_pickled():
    path = _Slotted([(0, 0), (5, 5), (9, 2)], "edge")
    path.sample(1.0)
    for other in (
        pickle.loads(pickle.dumps(path)),
        copy.copy(path),
        copy.deepcopy(path),
    ):
        assert other.label == "edge"
        assert other._kept is None
        assert np.array_equal(other.points, path.points)

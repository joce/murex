"""Spectral color science used by the paint model.

Everything here works on *reflectance spectra*: arrays whose last axis holds
reflectance (0..1) sampled at :data:`WAVELENGTHS`.

Pipeline
--------
sRGB color  ->  smooth reflectance spectrum      (Burns' LHTSS basis spectra)
paint layer ->  Kubelka-Munk absorption/scatter  (two-flux model, finite thickness)
spectrum    ->  CIE XYZ (D65)  ->  linear sRGB  ->  sRGB

Mixing paints means adding their absorption (K) and scattering (S) spectra,
weighted by volume. That is what makes blue + yellow give green instead of the
grey you get by averaging RGB values.
"""

from __future__ import annotations

import re
from itertools import pairwise

import numpy as np
from numba import njit
from numpy.lib.stride_tricks import as_strided

from ._spectral_tables import BASIS_TABLE, SPECTRUM_TO_RGB_TABLE

# --------------------------------------------------------------------------
# Wavelength sampling
# --------------------------------------------------------------------------
#: Sample wavelengths in nm. 24 uniform bands over the visible range keep the
#: mixing error below ~0.3 dE (mean) compared with a full 10 nm spectrum,
#: while keeping the per-pixel memory of the canvas reasonable.
WAVELENGTHS = np.linspace(400.0, 700.0, 24)
N_BANDS = WAVELENGTHS.size

# CIE 1931 2-degree standard observer, 380..780 nm, 10 nm steps (x, y, z).
_CIE_WL = np.arange(380.0, 781.0, 10.0)
_CIE_1931 = np.array(
    [
        [0.001368, 0.000039, 0.006450],
        [0.004243, 0.000120, 0.020050],
        [0.014310, 0.000396, 0.067850],
        [0.043510, 0.001210, 0.207400],
        [0.134380, 0.004000, 0.645600],
        [0.283900, 0.011600, 1.385600],
        [0.348280, 0.023000, 1.747060],
        [0.336200, 0.038000, 1.772110],
        [0.290800, 0.060000, 1.669200],
        [0.195360, 0.090980, 1.287640],
        [0.095640, 0.139020, 0.812950],
        [0.032010, 0.208020, 0.465180],
        [0.004900, 0.323000, 0.272000],
        [0.009300, 0.503000, 0.158200],
        [0.063270, 0.710000, 0.078250],
        [0.165500, 0.862000, 0.042160],
        [0.290400, 0.954000, 0.020300],
        [0.433450, 0.994950, 0.008750],
        [0.594500, 0.995000, 0.003900],
        [0.762100, 0.952000, 0.002100],
        [0.916300, 0.870000, 0.001650],
        [1.026300, 0.757000, 0.001100],
        [1.062200, 0.631000, 0.000800],
        [1.002600, 0.503000, 0.000340],
        [0.854450, 0.381000, 0.000190],
        [0.642400, 0.265000, 0.000050],
        [0.447900, 0.175000, 0.000020],
        [0.283500, 0.107000, 0.000000],
        [0.164900, 0.061000, 0.000000],
        [0.087400, 0.032000, 0.000000],
        [0.046770, 0.017000, 0.000000],
        [0.022700, 0.008210, 0.000000],
        [0.011359, 0.004102, 0.000000],
        [0.005790, 0.002091, 0.000000],
        [0.002899, 0.001047, 0.000000],
        [0.001440, 0.000520, 0.000000],
        [0.000690, 0.000249, 0.000000],
        [0.000332, 0.000120, 0.000000],
        [0.000166, 0.000060, 0.000000],
        [0.000083, 0.000030, 0.000000],
        [0.000042, 0.000015, 0.000000],
    ]
)

# CIE standard illuminant D65, 380..780 nm, 10 nm steps.
_D65_SPD = np.array(
    [
        49.98,
        54.65,
        82.75,
        91.49,
        93.43,
        86.68,
        104.86,
        117.01,
        117.81,
        114.86,
        115.92,
        108.81,
        109.35,
        107.80,
        104.79,
        107.69,
        104.41,
        104.05,
        100.00,
        96.33,
        95.79,
        88.69,
        90.01,
        89.60,
        87.70,
        83.29,
        83.70,
        80.03,
        80.21,
        82.28,
        78.28,
        69.72,
        71.61,
        74.35,
        61.60,
        69.89,
        75.09,
        63.59,
        46.42,
        66.81,
        63.38,
    ]
)

_XYZ_TO_LINEAR_SRGB = np.array(
    [
        [3.2404542, -1.5371385, -0.4985314],
        [-0.9692660, 1.8760108, 0.0415560],
        [0.0556434, -0.2040259, 1.0572252],
    ]
)


def _build_spectrum_to_rgb(wavelengths: np.ndarray) -> np.ndarray:
    """3xN matrix mapping a sampled reflectance spectrum to linear sRGB.

    The spectrum is treated as piecewise linear between samples and integrated
    against the CIE observer under D65 on a 1 nm grid. Rows are normalised so
    that a perfect white reflector (R = 1) maps exactly to (1, 1, 1).
    """
    fine = np.arange(380.0, 781.0, 1.0)
    cmf = np.stack([np.interp(fine, _CIE_WL, _CIE_1931[:, i]) for i in range(3)], -1)
    weights = cmf * np.interp(fine, _CIE_WL, _D65_SPD)[:, None]
    hats = np.empty((wavelengths.size, fine.size))
    for i in range(wavelengths.size):
        unit = np.zeros(wavelengths.size)
        unit[i] = 1.0
        hats[i] = np.interp(fine, wavelengths, unit)
    xyz = (hats @ weights).T
    rgb = _XYZ_TO_LINEAR_SRGB @ (xyz / xyz[1].sum())
    return rgb / rgb.sum(axis=1, keepdims=True)


#: (3, N_BANDS) matrix: linear sRGB = SPECTRUM_TO_RGB @ reflectance.
#:
#: A stored table, not computed at import: the arithmetic of NumPy (the
#: interpolation, the matrix products) rounds differently from one NumPy, BLAS
#: or processor to another, and oilpaint and fusain check their pictures byte
#: for byte. ``_build_spectrum_to_rgb`` derives it (to within rounding);
#: ``tools/derive_spectral_tables.py`` writes the table, and a test checks
#: that the two agree.
#:
#: The table is for 24 bands. With another number of them (``WAVELENGTHS``
#: changed, to try it) there is no table to read, and it is derived.
SPECTRUM_TO_RGB = (
    np.array(SPECTRUM_TO_RGB_TABLE, dtype=np.float64)
    if len(SPECTRUM_TO_RGB_TABLE[0]) == N_BANDS
    else _build_spectrum_to_rgb(WAVELENGTHS)
)

#: Rec.709 luminance weights for linear sRGB.
LUMINANCE = np.array([0.2126, 0.7152, 0.0722])

# --------------------------------------------------------------------------
# sRGB helpers
# --------------------------------------------------------------------------


def srgb_to_linear(c) -> np.ndarray:
    c = np.asarray(c, dtype=np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c) -> np.ndarray:
    c = np.clip(np.asarray(c, dtype=np.float64), 0.0, 1.0)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1.0 / 2.4) - 0.055)


_HEX = re.compile(r"^#?([0-9a-fA-F]{6})$")

# How far above 1 a colour on the 0..1 scale may stray by rounding.
_OVERSHOOT = 1e-6


def parse_color(color) -> np.ndarray:
    """Return an sRGB triple in 0..1.

    Accepts ``"#rrggbb"`` strings, float triples in 0..1, or int triples in
    0..255:

    * numpy ``uint8`` values (an image's pixel) are always on the 0..255
      scale, so ``np.array([1, 1, 1], np.uint8)`` is near-black;
    * otherwise a triple whose components are all at most 1 is on the 0..1
      scale (so ``(1, 1, 1)`` is white), counting a float a hair above 1
      (rounding in a colour computed on the 0..1 scale) as 1;
    * a triple with a component of 2 or more is on the 0..255 scale, floats
      included (``(123.4, 56.7, 89.1)``);
    * a triple whose largest component is above 1 but below 2, such as
      ``(1.02, 0.5, 0.5)``, is refused: read as 0..255 it would be almost
      black, which is never what it means (it is a colour on the 0..1 scale
      pushed a little too far).

    Components outside the scale are clipped to it.
    """
    if isinstance(color, str):
        m = _HEX.match(color.strip())
        if not m:
            raise ValueError(f"cannot parse color {color!r}; use '#rrggbb'")
        h = m.group(1)
        return (
            np.array([int(h[i : i + 2], 16) for i in (0, 2, 4)], dtype=np.float64)
            / 255.0
        )
    try:
        raw = np.asarray(color)
        c = raw.astype(np.float64).reshape(-1)
    except (TypeError, ValueError):
        raise TypeError(
            f"cannot parse color {color!r}; use '#rrggbb', a float triple in "
            "0..1 or an int triple in 0..255"
        ) from None
    if c.size != 3:
        raise ValueError(f"expected 3 color components, got {c.size}")
    if not np.isfinite(c).all():
        raise ValueError(f"color components must be finite numbers, got {color!r}")
    top = c.max()
    if raw.dtype == np.uint8 or top >= 2.0:
        c = c / 255.0
    elif top > 1.0 + _OVERSHOOT:  # (no whole numbers lie in between)
        raise ValueError(
            f"cannot tell the scale of color {color!r}: give floats in 0..1 "
            "or numbers in 0..255 (with one of 2 or more)"
        )
    return np.clip(c, 0.0, 1.0)


def to_hex(srgb) -> str:
    c = np.clip(np.round(np.asarray(srgb) * 255), 0, 255).astype(int)
    return "#{:02x}{:02x}{:02x}".format(*c)


_RGB_TO_XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ]
)
# The D65 white point in XYZ (not to be confused with _D65_SPD, the
# illuminant's spectrum above).
_D65_WHITE_XYZ = np.array([0.95047, 1.0, 1.08883])


def srgb_to_lab(srgb) -> np.ndarray:
    """sRGB (..., 3) in 0..1 -> CIELAB (D65): L* 0..100, where a difference
    of ~2.3 is just noticeable."""
    xyz = srgb_to_linear(srgb) @ _RGB_TO_XYZ.T / _D65_WHITE_XYZ
    f = np.where(
        xyz > (6 / 29) ** 3,
        np.cbrt(np.maximum(xyz, 0.0)),
        xyz / (3 * (6 / 29) ** 2) + 4 / 29,
    )
    return np.stack(
        [
            116 * f[..., 1] - 16,
            500 * (f[..., 0] - f[..., 1]),
            200 * (f[..., 1] - f[..., 2]),
        ],
        axis=-1,
    )


# --------------------------------------------------------------------------
# sRGB -> reflectance (Scott Burns' least hyperbolic tangent slope squared)
# --------------------------------------------------------------------------


def _lhtss(
    target_linear_rgb: np.ndarray, T: np.ndarray, iters: int = 200
) -> np.ndarray:
    """Smoothest reflectance in (0, 1) whose color is ``target_linear_rgb``.

    S. A. Burns, "Generating reflectance curves from sRGB triplets" (2015/2019).
    Newton iteration on the Lagrangian of: minimise sum (z[i+1]-z[i])^2 with
    reflectance = (tanh(z) + 1) / 2 and T @ reflectance = target.
    """
    n = T.shape[1]
    D = 4 * np.eye(n) - 2 * np.eye(n, k=1) - 2 * np.eye(n, k=-1)
    D[0, 0] = D[-1, -1] = 2
    z = np.zeros(n)
    lam = np.zeros(3)
    for _ in range(iters):
        th = np.tanh(z)
        sech2 = 1.0 - th * th
        d1 = sech2 / 2.0
        d2 = -sech2 * th
        F = np.concatenate(
            [D @ z + d1 * (T.T @ lam), T @ ((th + 1.0) / 2.0) - target_linear_rgb]
        )
        if np.abs(F).max() < 1e-12:
            break
        J = np.zeros((n + 3, n + 3))
        J[:n, :n] = D + np.diag(d2 * (T.T @ lam))
        J[:n, n:] = d1[:, None] * T.T
        J[n:, :n] = T * d1[None, :]
        delta = np.linalg.solve(J, -F)
        z += delta[:n]
        lam += delta[n:]
    return (np.tanh(z) + 1.0) / 2.0


def _build_basis(T: np.ndarray) -> np.ndarray:
    """The seven basis spectra for the matrix ``T`` (``SPECTRUM_TO_RGB``).

    Not called at import: the result is stored as ``_BASIS`` (see
    ``SPECTRUM_TO_RGB``), and ``np.linalg.solve``, which this rests on, rounds
    differently from one BLAS to another.
    """
    # white, cyan, magenta, yellow, red, green, blue
    corners = [
        (1, 1, 1),
        (0, 1, 1),
        (1, 0, 1),
        (1, 1, 0),
        (1, 0, 0),
        (0, 1, 0),
        (0, 0, 1),
    ]
    eps = 1e-4
    return np.stack(
        [_lhtss(np.clip(np.array(c, float), eps, 1 - eps), T) for c in corners]
    )


#: (7, N_BANDS) reflectance spectra of white, cyan, magenta, yellow, red, green,
#: blue: a stored table, derived by ``_build_basis(SPECTRUM_TO_RGB)``.
_BASIS = (
    np.array(BASIS_TABLE, dtype=np.float64)
    if len(BASIS_TABLE[0]) == N_BANDS
    else _build_basis(SPECTRUM_TO_RGB)
)

# (the tables above are shared by everything that works with colour: read-only)
for _table in (
    WAVELENGTHS,
    _CIE_WL,
    _CIE_1931,
    _D65_SPD,
    _XYZ_TO_LINEAR_SRGB,
    SPECTRUM_TO_RGB,
    LUMINANCE,
    _RGB_TO_XYZ,
    _D65_WHITE_XYZ,
    _BASIS,
):
    _table.flags.writeable = False
del _table

#: Darkest reflectance any color is mapped to. Real "black" paint reflects a
#: few percent; this keeps Kubelka-Munk absorption finite.
MIN_REFLECTANCE = 1e-3


def linear_rgb_to_reflectance(lrgb) -> np.ndarray:
    """Vectorised linear sRGB (..., 3) -> reflectance spectrum (..., N_BANDS).

    The color is split into white + one secondary + one primary component and
    the matching precomputed smooth spectra are summed. Because the color
    transform is linear, the result reproduces the input color exactly.
    """
    lrgb = np.clip(np.asarray(lrgb, dtype=np.float64), 0.0, 1.0)
    r, g, b = lrgb[..., 0], lrgb[..., 1], lrgb[..., 2]
    w = np.minimum(np.minimum(r, g), b)
    r, g, b = r - w, g - w, b - w
    c = np.minimum(g, b)
    m = np.minimum(r, b)
    y = np.minimum(r, g)
    red = np.minimum(np.maximum(0, r - b), np.maximum(0, r - g))
    green = np.minimum(np.maximum(0, g - b), np.maximum(0, g - r))
    blue = np.minimum(np.maximum(0, b - g), np.maximum(0, b - r))
    weights = np.stack([w, c, m, y, red, green, blue], axis=-1)
    return np.clip(weights @ _BASIS, MIN_REFLECTANCE, 1.0)


def reflectance_to_linear_rgb(R) -> np.ndarray:
    """Reflectance spectrum (..., N_BANDS) -> linear sRGB (..., 3)."""
    return np.asarray(R) @ SPECTRUM_TO_RGB.T


def srgb_to_reflectance(color) -> np.ndarray:
    return linear_rgb_to_reflectance(srgb_to_linear(parse_color(color)))


def reflectance_to_srgb(R) -> np.ndarray:
    return linear_to_srgb(reflectance_to_linear_rgb(R))


# --------------------------------------------------------------------------
# Kubelka-Munk
# --------------------------------------------------------------------------


def _km_terms(kappa, sigma):
    """The terms of the Kubelka-Munk solution for a layer of optical
    thicknesses ``kappa`` (per band) and ``sigma`` (see :func:`km_layer`):
    those two, clamped at 0 (tiny negatives are left by float rounding in the
    paint bookkeeping) and ``sigma`` with a band axis where it had none;
    ``B = sqrt(kappa^2 + 2 kappa sigma)``; and ``tau = tanh(B) / B`` (its
    series where B is tiny)."""
    kappa = np.maximum(np.asarray(kappa), 0.0)
    sigma = np.maximum(np.asarray(sigma), 0.0)
    if sigma.ndim == kappa.ndim - 1:
        sigma = sigma[..., None]
    B = np.sqrt(kappa * kappa + 2.0 * kappa * sigma)
    small = B < 1e-4
    tau = np.where(small, 1.0 - B * B / 3.0, np.tanh(B) / np.where(small, 1.0, B))
    return kappa, sigma, B, tau


def km_layer(kappa, sigma, ground, out: np.ndarray | None = None):
    """Reflectance of a paint layer lying on a ground of reflectance ``ground``.

    Two-flux Kubelka-Munk solution for a layer of finite thickness. Inputs are
    *optical thicknesses*: ``kappa = K * thickness`` (absorption, per band) and
    ``sigma = S * thickness`` (scattering). Written in a form that stays finite
    for empty layers (returns the ground) and for pure dyes (sigma = 0 gives
    Beer-Lambert: ground * exp(-2 kappa)).

    A batch of layers is worked out by compiled code, several times as fast
    and to the same result to the last bit: ``kappa`` (..., bands) and
    ``sigma`` (...) float64 arrays of two dimensions or more, over one
    ``ground`` (bands,) or over a ground for each layer (..., bands), as when
    each pixel of a picture has its own layer over what is already there.
    Anything else (numbers, a single spectrum, other dtypes or shapes, array
    subclasses, layers that lie in memory column after column) is worked out
    by numpy, as every call was before.

    ``out``, if given, is an array of the shape of the result, which is put
    there instead of in a new array, and returned. It may be ``ground``
    itself: ``km_layer(kappa, sigma, seen, out=seen)`` lays a layer over what
    is seen at each pixel, in place.
    """
    if _is_batch(kappa, sigma, ground):
        return _km_layers(kappa, sigma, ground, out)
    result = _km_layer_general(kappa, sigma, ground)
    if out is None:
        return result
    out[...] = result
    return out


def _km_layer_general(kappa, sigma, ground):
    """:func:`km_layer` for whatever numpy can broadcast: the formula the
    compiled kernels below repeat, operation for operation."""
    kappa, sigma, _, tau = _km_terms(kappa, sigma)
    num = sigma * tau - ground * ((sigma + kappa) * tau - 1.0)
    den = (sigma + kappa - ground * sigma) * tau + 1.0
    return num / den


def _is_float64(array) -> bool:
    """Whether ``array`` is what the kernels take: a numpy array itself (not
    a subclass) of float64 in this machine's byte order."""
    return type(array) is np.ndarray and array.dtype == np.float64


def _is_ground(ground) -> bool:
    """Whether ``ground`` is a numpy array itself of floats that float64
    holds exactly."""
    return (
        type(ground) is np.ndarray
        and ground.dtype.kind == "f"
        and ground.dtype.itemsize <= 8
    )


def _is_batch(kappa, sigma, ground) -> bool:
    """Whether :func:`km_layer` hands these to the compiled kernels: a batch
    of layers (see there), not an empty one, whose result numpy would lay
    out in memory as the kernels do, row after row (it follows ``kappa``:
    not one that lies column after column, or with its axes swapped)."""
    return (
        _is_float64(kappa)
        and _is_float64(sigma)
        and _is_ground(ground)
        and kappa.ndim >= 2
        and kappa.size > 0
        and sigma.shape == kappa.shape[:-1]
        and ground.shape in {kappa.shape, kappa.shape[-1:]}
        and all(abs(a) >= abs(b) > 0 for a, b in pairwise(kappa.strides))
    )


def _km_layer_batch(kappa, sigma, ground):
    """:func:`km_layer` for a large batch of layers over one ground: ``kappa``
    (..., N_BANDS) and ``sigma`` (...) float64 arrays, ``ground`` (N_BANDS,).

    The same operations in the same order, so the same result to the last
    bit, but in two compiled passes over the batch (and numpy's ``tanh``
    between them, so that too is the very same function) instead of some
    twenty numpy passes. Anything else (other dtypes or shapes, array
    subclasses) goes to :func:`km_layer`, which does as much itself for a
    batch of two dimensions or more; this also takes a single layer.
    """
    plain = (
        _is_float64(kappa)
        and _is_float64(sigma)
        and _is_ground(ground)
        and kappa.size > 0
        and kappa.shape[:-1] == sigma.shape
        and kappa.shape[-1:] == ground.shape == (N_BANDS,)
    )
    if not plain:
        return km_layer(kappa, sigma, ground)
    return _km_layers(kappa, sigma, ground, None)


def _km_layers(kappa, sigma, ground, out: np.ndarray | None) -> np.ndarray:
    """:func:`km_layer` for ``kappa`` (..., bands) and ``sigma`` (...)
    float64 arrays, and a ``ground`` (bands,) or (..., bands) of floats, by
    the compiled kernels."""
    shape = kappa.shape
    bands = shape[-1]
    k, k_step = _rows(kappa.reshape(-1, bands))
    s = np.ascontiguousarray(sigma.reshape(-1))
    if ground.ndim == 1:  # one ground: every layer reads the same row
        g, g_step = np.array(ground, dtype=np.float64), 0
    else:
        g, g_step = _rows(ground.reshape(-1, bands).astype(np.float64, copy=False))
    if out is None:
        R = np.empty((s.shape[0], bands))
        _km_blocks(k, k_step, s, g, g_step, R, False)
        return R.reshape(shape)
    target = _km_target(out, shape, (kappa, sigma, ground))
    if target is None:  # (into an array of the kernels' own first)
        out[...] = _km_layers(kappa, sigma, ground, None)
    else:
        _km_blocks(k, k_step, s, g, g_step, target, True)
    return out


#: How many values the kernels work out at a time: few enough for what they
#: keep between their passes to stay in the processor's cache.
_KM_VALUES = 32768


def _km_blocks(k, k_step, s, g, g_step, R, aside: bool) -> None:
    """Fill ``R`` (layers, bands) with the reflectance of the layers ``k``
    and ``s`` over ``g`` (as :func:`_rows` gives them): two compiled passes
    over the layers, and numpy's ``tanh`` between them, so that too is the
    very same function as in :func:`_km_layer_general`.

    The layers are taken some at a time, each in whole (what numpy's
    ``tanh`` gives for a value does not depend on those around it), so that
    nothing as large as the batch is needed but the result. ``aside`` says
    that ``R`` is not a new array of the kernels' own: it may be the ground,
    or the layers themselves. Each lot is then worked out aside and put in
    ``R`` once it is whole.
    """
    count, bands = R.shape
    # (a multiple of 16 layers at a time: of whole vectors, whatever numpy's
    # tanh takes at once, as when it is given the whole batch)
    size = min(max(_KM_VALUES // bands // 16, 1) * 16, count)
    B, tanh_B = np.empty((size, bands)), np.empty((size, bands))
    lot = np.empty((size, bands)) if aside else None
    for a in range(0, count, size):
        n = min(size, count - a)
        _km_b(k, k_step, s, a, n, B)
        if n == size:
            np.tanh(B, out=tanh_B)
        else:
            np.tanh(B[:n], out=tanh_B[:n])
        if lot is None:
            _km_reflectance(k, k_step, s, g, g_step, a, n, B, tanh_B, R, a)
        else:
            _km_reflectance(k, k_step, s, g, g_step, a, n, B, tanh_B, lot, 0)
            R[a : a + n] = lot[:n]


def _rows(array):
    """The values of ``array`` (layers, bands), float64, as they lie in
    memory, one after the other, and how many lie from the start of a row to
    the start of the next: ``(values, step)``, row ``i`` being
    ``values[i * step : i * step + bands]``. Without a copy where every row
    is in one piece, as in a slice of the columns of a wider array."""
    count, bands = array.shape
    if array.flags.c_contiguous:
        return array.reshape(-1), bands
    step, rest = divmod(array.strides[0], array.itemsize)
    if array.strides[1] == array.itemsize and step > bands and not rest:
        # (from the first value of the first row to the last of the last:
        # all within the memory the rows are a part of)
        values = as_strided(
            array, ((count - 1) * step + bands,), (array.itemsize,), writeable=False
        )
        return values, step
    return np.ascontiguousarray(array).reshape(-1), bands


def _km_target(out, shape, inputs) -> np.ndarray | None:
    """``out`` as (layers, bands) for :func:`_km_layers` to fill as it goes,
    or None if it cannot: there is none; it is not an array of float64 of
    this shape whose layers can be reached one after the other; or it shares
    memory with one of the ``inputs`` without being that very array, so that
    filling it could change a value before it is read."""
    if not (_is_float64(out) and out.shape == shape and out.flags.writeable):
        return None
    if any(a is not out and np.may_share_memory(a, out) for a in inputs):
        return None
    if out.ndim > 2 and not out.flags.c_contiguous:
        return None
    return out.reshape(-1, shape[-1])


# Plain IEEE arithmetic only (no fastmath): numba then neither reorders nor
# fuses the operations, so each matches numpy's to the bit. "x <= 0.0: 0.0"
# is np.maximum(x, 0.0): -0.0 becomes +0.0 and NaN stays NaN.
#
# The kernels take the layers as _rows gives them (kappa: values and step)
# and work on ``count`` of them from layer ``start``; B and tanh_B are
# (layers, bands) C-contiguous arrays of their own, filled from their top.
@njit(cache=True, error_model="numpy")
def _km_b(kappa, step, sigma, start, count, B):
    for i in range(count):
        s = sigma[start + i]
        if s <= 0.0:
            s = 0.0
        row = (start + i) * step
        for j in range(B.shape[1]):
            k = kappa[row + j]
            if k <= 0.0:
                k = 0.0
            B[i, j] = np.sqrt(k * k + 2.0 * k * s)


# (the ground as _rows gives it too, a step of 0 being one ground for all;
# R, C-contiguous as well, is filled from its row ``at``)
@njit(cache=True, error_model="numpy")
def _km_reflectance(
    kappa, step, sigma, ground, ground_step, start, count, B, tanh_B, R, at
):
    for i in range(count):
        s = sigma[start + i]
        if s <= 0.0:
            s = 0.0
        row = (start + i) * step
        under = (start + i) * ground_step
        for j in range(B.shape[1]):
            k = kappa[row + j]
            if k <= 0.0:
                k = 0.0
            b = B[i, j]
            tau = 1.0 - b * b / 3.0 if b < 1e-4 else tanh_B[i, j] / b
            g = ground[under + j]
            num = s * tau - g * ((s + k) * tau - 1.0)
            den = (s + k - g * s) * tau + 1.0
            R[at + i, j] = num / den


def km_film(kappa, sigma):
    """Reflectance and transmittance of a free-standing paint film: ``(R, T)``.

    The same from either side (a film is uniform through its thickness).
    ``R`` is what it reflects with nothing behind it, ``T`` the share of
    light that gets through it one way. Over a ground ``g`` it reflects
    ``R + T**2 * g / (1 - R * g)``, which is :func:`km_layer`. Inputs are
    optical thicknesses, as for :func:`km_layer`.
    """
    kappa, sigma, B, tau = _km_terms(kappa, sigma)
    den = (sigma + kappa) * tau + 1.0
    # 1 / cosh(B), without overflow for thick, dark films
    e = np.exp(-B)
    sech = 2.0 * e / (1.0 + e * e)
    return sigma * tau / den, sech / den


def km_opaque(kappa, sigma):
    """Reflectance of an infinitely thick layer (the paint's masstone)."""
    kappa = np.asarray(kappa)
    sigma = np.asarray(sigma)
    if sigma.ndim == kappa.ndim - 1:
        sigma = sigma[..., None]
    ks = kappa / np.maximum(sigma, 1e-12)
    return 1.0 + ks - np.sqrt(ks * ks + 2.0 * ks)


def solve_absorption(target_R, sigma) -> np.ndarray:
    """Absorption ``kappa`` (per band) such that a unit-thickness layer with
    scattering ``sigma`` looks like ``target_R`` when painted over white.

    Over a perfect white ground the KM layer formula reduces to
    R = (1 - kappa*tau) / (1 + kappa*tau), which is monotonic in kappa, so a
    vectorised bisection in log-space is robust.
    """
    target_R = np.clip(np.asarray(target_R, dtype=np.float64), MIN_REFLECTANCE, 1.0)
    sigma = float(sigma)
    lo = np.full(target_R.shape, -14.0)
    hi = np.full(target_R.shape, 12.0)
    for _ in range(70):
        mid = 0.5 * (lo + hi)
        too_dark = target_R > _layer_over_white(np.exp(mid), sigma)
        hi = np.where(too_dark, mid, hi)
        lo = np.where(too_dark, lo, mid)
    kappa = np.exp(0.5 * (lo + hi))
    return np.where(target_R >= 0.99999, 0.0, kappa)


def _layer_over_white(kappa, sigma: float):
    """``km_layer(kappa, sigma, 1.0)`` for kappa >= 0 and a scalar sigma >= 0,
    without the general case's checks: the bisection above calls it 70 times
    per paint. The arithmetic is km_layer's, operation for operation
    (multiplying by a ground of exactly 1 changes nothing), so the result is
    the same to the last bit."""
    B = np.sqrt(kappa * kappa + 2.0 * kappa * sigma)
    small = B < 1e-4
    tau = np.tanh(B) / np.where(small, 1.0, B)
    if small.any():
        tau = np.where(small, 1.0 - B * B / 3.0, tau)
    num = sigma * tau - ((sigma + kappa) * tau - 1.0)
    den = (sigma + kappa - sigma) * tau + 1.0
    return num / den

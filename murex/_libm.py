"""Elementary functions that give the same bits on every machine.

NumPy's ``power``, ``exp`` and ``tanh`` take SIMD paths that round some
values differently from one processor to another, and the C library behind
numba's ``math`` differs between systems (and, with fused multiply-add,
between processors). The colour science must not: two media check their
pictures to the bit. So these are computed here with nothing but IEEE
addition, subtraction, multiplication and division, which every machine
rounds alike, and integer work on the bits of a double; compiled without
``fastmath``, numba neither fuses nor reorders them.

The algorithms are those of fdlibm (Sun Microsystems' freely distributable
libm, by way of its descendants in the BSD and musl C libraries), restricted
to what the colour science needs. Their results are within one unit in the
last place of the exact value (two for ``tanh``); ``tests/test_libm.py``
checks it against decimal arithmetic over the ranges they are used on, and
pins some values to the bit.

    ====================================================
    Copyright (C) 1993, 2004 by Sun Microsystems, Inc. All rights reserved.

    Developed at SunSoft, a Sun Microsystems, Inc. business.
    Permission to use, copy, modify, and distribute this
    software is freely granted, provided that this notice
    is preserved.
    ====================================================
"""

from __future__ import annotations

import struct
from collections.abc import Callable
from typing import cast

import numpy as np
from llvmlite import ir
from numba import njit, types
from numba.extending import intrinsic

_inlined = njit(cache=True, error_model="numpy", inline="always")


@intrinsic
def _bits_of(typingctx, x):
    """The 64 bits of a double, as a signed integer."""
    signature = types.int64(types.float64)

    def codegen(context, builder, sig, args):
        return builder.bitcast(args[0], ir.IntType(64))

    return signature, codegen


@intrinsic
def _double_of(typingctx, bits):
    """The double whose 64 bits these are."""
    signature = types.float64(types.int64)

    def codegen(context, builder, sig, args):
        return builder.bitcast(args[0], ir.DoubleType())

    return signature, codegen


# (the two as the kernels call them: one argument each)
_bits = cast("Callable[[float], int]", _bits_of)
_double = cast("Callable[[int], float]", _double_of)


def _hex(high: int, low: int) -> float:
    """A constant given by its two 32-bit words, as fdlibm gives them."""
    return struct.unpack("<d", struct.pack("<Q", (high << 32) | low))[0]


@_inlined
def _high(x):
    """The high 32 bits of a double, signed (fdlibm's GET_HIGH_WORD)."""
    return _bits(x) >> 32


@_inlined
def _low_zeroed(x):
    """The double with its low 32 bits cleared (fdlibm's SET_LOW_WORD(x, 0))."""
    return _double(_bits(x) & -4294967296)  # ~0xffffffff


@_inlined
def _with_high(high, low):
    """The double of these two 32-bit words (fdlibm's INSERT_WORDS)."""
    return _double(((high & 0xFFFFFFFF) << 32) | (low & 0xFFFFFFFF))


@_inlined
def _scale(y, k):
    """``y`` times two to the ``k``, exactly where the result is normal (fdlibm's
    scalbn, for the exponents met here: at most two multiplications)."""
    if k > 1023:
        y *= _with_high(0x7FE00000, 0)  # 2**1023
        k -= 1023
        if k > 1023:
            k = 1023
    elif k < -1022:
        y *= _with_high(0x03700000, 0)  # 2**-968, exactly: y stays normal
        k += 968
        if k < -1022:
            k = -1022
    return y * _with_high((0x3FF + k) << 20, 0)


# ---------------------------------------------------------------- exp
_O_THRESHOLD = _hex(0x40862E42, 0xFEFA39EF)  # 7.09782712893383973096e+02
_U_THRESHOLD = _hex(0xC0874910, 0xD52D3051)  # -7.45133219101941108420e+02
_LN2_HI = _hex(0x3FE62E42, 0xFEE00000)  # 6.93147180369123816490e-01
_LN2_LO = _hex(0x3DEA39EF, 0x35793C76)  # 1.90821492927058770002e-10
_INV_LN2 = _hex(0x3FF71547, 0x652B82FE)  # 1.44269504088896338700e+00
_P1 = _hex(0x3FC55555, 0x5555553E)
_P2 = _hex(0xBF66C16C, 0x16BEBD93)
_P3 = _hex(0x3F11566A, 0xAF25DE2C)
_P4 = _hex(0xBEBBBD41, 0xC5D26BF1)
_P5 = _hex(0x3E663769, 0x72BEA4D0)


@_inlined
def exp(x):
    """e to the ``x`` (fdlibm's e_exp.c)."""
    if x != x:
        return x
    if x > _O_THRESHOLD:
        return np.inf
    if x < _U_THRESHOLD:
        return 0.0
    hx = _high(x) & 0x7FFFFFFF
    k = 0
    hi = 0.0
    lo = 0.0
    if hx > 0x3FD62E42:  # |x| > 0.5 ln2
        if hx < 0x3FF0A2B2:  # |x| < 1.5 ln2
            if x > 0.0:
                hi = x - _LN2_HI
                lo = _LN2_LO
                k = 1
            else:
                hi = x + _LN2_HI
                lo = -_LN2_LO
                k = -1
        else:
            k = int(_INV_LN2 * x + (0.5 if x > 0.0 else -0.5))
            t = float(k)
            hi = x - t * _LN2_HI
            lo = t * _LN2_LO
        x = hi - lo
    elif hx < 0x3E300000:  # |x| < 2**-28
        return 1.0 + x
    t = x * x
    c = x - t * (_P1 + t * (_P2 + t * (_P3 + t * (_P4 + t * _P5))))
    if k == 0:
        return 1.0 - ((x * c) / (c - 2.0) - x)
    y = 1.0 - ((lo - (x * c) / (2.0 - c)) - hi)
    return _scale(y, k)


# ---------------------------------------------------------------- expm1
_Q1 = _hex(0xBFA11111, 0x111110F4)
_Q2 = _hex(0x3F5A01A0, 0x19FE5585)
_Q3 = _hex(0xBF14CE19, 0x9EAADBB7)
_Q4 = _hex(0x3ED0CFCA, 0x86E65239)
_Q5 = _hex(0xBE8AFDB7, 0x6E09C32D)


@_inlined
def _expm1_reduce(x, negative, hx):
    """``x`` = k ln2 + r + c for |x| > 0.5 ln2: ``(r, c, k)``."""
    if hx < 0x3FF0A2B2:  # |x| < 1.5 ln2
        if not negative:
            hi = x - _LN2_HI
            lo = _LN2_LO
            k = 1
        else:
            hi = x + _LN2_HI
            lo = -_LN2_LO
            k = -1
    else:
        k = int(_INV_LN2 * x + (-0.5 if negative else 0.5))
        t = float(k)
        hi = x - t * _LN2_HI
        lo = t * _LN2_LO
    r = hi - lo
    return r, (hi - r) - lo, k


@_inlined
def _expm1_scaled(x, e, k):
    """e**(k ln2 + x) - 1 from its parts, for k other than 0, 1 and -1."""
    if k <= -2 or k > 56:
        return _scale(1.0 - (e - x), k) - 1.0
    if k < 20:
        t = _with_high(0x3FF00000 - (0x200000 >> k), 0)  # 1 - 2**-k
        return _scale(t - (e - x), k)
    t = _with_high((0x3FF - k) << 20, 0)  # 2**-k
    return _scale((x - (e + t)) + 1.0, k)


@_inlined
def expm1(x):
    """e to the ``x``, less one, accurate near zero (fdlibm's s_expm1.c)."""
    if x != x:
        return x
    hx = _high(x)
    negative = hx < 0
    hx &= 0x7FFFFFFF
    if hx >= 0x4043687A:  # |x| >= 56 ln2
        if x > _O_THRESHOLD:
            return np.inf
        if negative:
            return -1.0
    k = 0
    c = 0.0
    if hx > 0x3FD62E42:  # |x| > 0.5 ln2
        x, c, k = _expm1_reduce(x, negative, hx)
    elif hx < 0x3C900000:  # |x| < 2**-54
        return x
    hfx = 0.5 * x
    hxs = x * hfx
    r1 = 1.0 + hxs * (_Q1 + hxs * (_Q2 + hxs * (_Q3 + hxs * (_Q4 + hxs * _Q5))))
    t = 3.0 - r1 * hfx
    e = hxs * ((r1 - t) / (6.0 - x * t))
    if k == 0:
        return x - (x * e - hxs)
    e = x * (e - c) - c
    e -= hxs
    if k == -1:
        return 0.5 * (x - e) - 0.5
    if k == 1:
        if x < -0.25:
            return -2.0 * (e - (x + 0.5))
        return 1.0 + 2.0 * (x - e)
    return _expm1_scaled(x, e, k)


# ---------------------------------------------------------------- tanh
@_inlined
def tanh(x):
    """The hyperbolic tangent of ``x`` (fdlibm's s_tanh.c)."""
    if x != x:
        return x
    ix = _high(x) & 0x7FFFFFFF
    a = -x if x < 0.0 else x
    if ix >= 0x40360000:  # |x| >= 22 (and infinities)
        z = 1.0
    elif ix < 0x3C800000:  # |x| < 2**-55
        return x * (1.0 + x)
    elif ix >= 0x3FF00000:  # |x| >= 1
        t = expm1(2.0 * a)
        z = 1.0 - 2.0 / (t + 2.0)
    else:
        t = expm1(-2.0 * a)
        z = -t / (t + 2.0)
    return -z if x < 0.0 else z


# ---------------------------------------------------------------- pow
_BP = (1.0, 1.5)
_DP_H = (0.0, _hex(0x3FE2B803, 0x40000000))  # 5.84962487220764160156e-01
_DP_L = (0.0, _hex(0x3E4CFDEB, 0x43CFD006))  # 1.35003920212974897128e-08
_TWO53 = _hex(0x43400000, 0x00000000)
_L1 = _hex(0x3FE33333, 0x33333303)
_L2 = _hex(0x3FDB6DB6, 0xDB6FABFF)
_L3 = _hex(0x3FD55555, 0x518F264D)
_L4 = _hex(0x3FD17460, 0xA91D4101)
_L5 = _hex(0x3FCD864A, 0x93C9DB65)
_L6 = _hex(0x3FCA7E28, 0x4A454EEF)
_LG2 = _hex(0x3FE62E42, 0xFEFA39EF)
_LG2_H = _hex(0x3FE62E43, 0x00000000)
_LG2_L = _hex(0xBE205C61, 0x0CA86C39)
_OVT = 8.0085662595372944372e-17
_CP = _hex(0x3FEEC709, 0xDC3A03FD)  # 2/(3 ln2)
_CP_H = _hex(0x3FEEC709, 0xE0000000)
_CP_L = _hex(0xBE3E2FE0, 0x145B01F5)


@_inlined
def _log2_parts(ax):
    """log2 of ``ax`` > 0 as a sum of two doubles, the first with its low
    word cleared (the logarithm in fdlibm's e_pow.c)."""
    ix = _high(ax)
    n = 0
    if ix < 0x00100000:  # subnormal
        ax *= _TWO53
        n -= 53
        ix = _high(ax)
    n += (ix >> 20) - 0x3FF
    j = ix & 0x000FFFFF
    ix = j | 0x3FF00000
    k = 0
    if j <= 0x3988E:  # |x| < sqrt(3/2)
        k = 0
    elif j < 0xBB67A:  # |x| < sqrt(3)
        k = 1
    else:
        k = 0
        n += 1
        ix -= 0x00100000
    ax = _with_high(ix, _bits(ax))
    bp = _BP[k]
    u = ax - bp
    v = 1.0 / (ax + bp)
    ss = u * v
    s_h = _low_zeroed(ss)
    t_h = _with_high(((ix >> 1) | 0x20000000) + 0x00080000 + (k << 18), 0)
    t_l = ax - (t_h - bp)
    s_l = v * ((u - s_h * t_h) - s_h * t_l)
    s2 = ss * ss
    r = s2 * s2 * (_L1 + s2 * (_L2 + s2 * (_L3 + s2 * (_L4 + s2 * (_L5 + s2 * _L6)))))
    r += s_l * (s_h + ss)
    s2 = s_h * s_h
    t_h = _low_zeroed(3.0 + s2 + r)
    t_l = r - ((t_h - 3.0) - s2)
    u = s_h * t_h
    v = s_l * t_h + t_l * ss
    p_h = _low_zeroed(u + v)
    p_l = v - (p_h - u)
    z_h = _CP_H * p_h
    z_l = _CP_L * p_h + p_l * _CP + _DP_L[k]
    t = float(n)
    t1 = _low_zeroed(((z_h + z_l) + _DP_H[k]) + t)
    t2 = z_l - (((t1 - t) - _DP_H[k]) - z_h)
    return t1, t2


@_inlined
def power(x, y):
    """``x`` to the power ``y``, for ``x`` > 0 and finite ``y`` (fdlibm's
    e_pow.c, without its cases of a negative or zero ``x``: the colour
    science raises only positive numbers to fixed powers). Otherwise NaN,
    except 1 for ``y`` == 0."""
    if y == 0.0:
        return 1.0
    if not (x > 0.0) or x == np.inf or y != y or abs(y) == np.inf:
        return np.nan
    if x == 1.0:
        return 1.0
    t1, t2 = _log2_parts(x)
    y1 = _low_zeroed(y)
    p_l = (y - y1) * t1 + y * t2
    p_h = y1 * t1
    z = p_l + p_h
    j = _high(z)
    i = _bits(z) & 0xFFFFFFFF
    if j >= 0x40900000 and (((j - 0x40900000) | i) != 0 or p_l + _OVT > z - p_h):
        return np.inf  # z >= 1024
    if (j & 0x7FFFFFFF) >= 0x4090CC00 and (
        (((j & 0xFFFFFFFF) - 0xC090CC00) | i) != 0 or p_l <= z - p_h
    ):
        return 0.0  # z <= -1075
    # 2 to the power p_h + p_l
    i = j & 0x7FFFFFFF
    k = (i >> 20) - 0x3FF
    n = 0
    if i > 0x3FE00000:  # |z| > 0.5: n = [z + 0.5]
        n = j + (0x00100000 >> (k + 1))
        k = ((n & 0x7FFFFFFF) >> 20) - 0x3FF
        t = _with_high(n & ~(0x000FFFFF >> k), 0)
        n = ((n & 0x000FFFFF) | 0x00100000) >> (20 - k)
        if j < 0:
            n = -n
        p_h -= t
    t = _low_zeroed(p_l + p_h)
    u = t * _LG2_H
    v = (p_l - (t - p_h)) * _LG2 + t * _LG2_L
    z = u + v
    w = v - (z - u)
    t = z * z
    t1 = z - t * (_P1 + t * (_P2 + t * (_P3 + t * (_P4 + t * _P5))))
    r = (z * t1) / (t1 - 2.0) - (w + z * w)
    z = 1.0 - (r - z)
    j = _high(z) + (n << 20)
    if (j >> 20) <= 0:
        return _scale(z, n)  # subnormal
    return _with_high(j, _bits(z))


# ---------------------------------------------------------------- cbrt
_B1 = 715094163
_B2 = 696219795
_C = _hex(0x3FE15F15, 0xF15F15F1)  # 19/35
_D = _hex(0xBFE691DE, 0x2532C834)  # -864/1225
_E = _hex(0x3FF6A0EA, 0x0EA0EA0F)  # 99/70
_F = _hex(0x3FF9B6DB, 0x6DB6DB6E)  # 45/28
_G = _hex(0x3FD6DB6D, 0xB6DB6DB7)  # 5/14


@_inlined
def cbrt(x):
    """The cube root of ``x`` (fdlibm's s_cbrt.c)."""
    if x != x or x == 0.0 or abs(x) == np.inf:
        return x + x if x != x or abs(x) == np.inf else x
    hx = _high(x)
    sign = hx & 0x80000000
    hx &= 0x7FFFFFFF
    x = _double(_bits(x) & 0x7FFFFFFFFFFFFFFF)  # |x|
    if hx < 0x00100000:  # subnormal
        t = _with_high(0x43500000, 0) * x  # 2**54 * x
        t = _with_high(_high(t) // 3 + _B2, 0)
    else:
        t = _with_high(hx // 3 + _B1, 0)
    r = t * t / x
    s = _C + r * t
    t *= _G + _F / (s + _E + _D / s)
    t = _with_high(_high(t) + 1, 0)
    s = t * t
    r = x / s
    w = t + t
    r = (r - t) / (w + r)
    t = t + t * r
    return _with_high(_high(t) | sign, _bits(t))


# ---------------------------------------------------------------- arrays
@njit(cache=True, error_model="numpy")
def tanh_array(x, out):
    """``tanh`` of each element of the flat array ``x``, into ``out``."""
    for i in range(x.shape[0]):
        out[i] = tanh(x[i])


@njit(cache=True, error_model="numpy")
def exp_array(x, out):
    """``exp`` of each element of the flat array ``x``, into ``out``."""
    for i in range(x.shape[0]):
        out[i] = exp(x[i])


@njit(cache=True, error_model="numpy")
def power_array(x, y, out):
    """``power(x, y)`` for each element of the flat array ``x``, into ``out``."""
    for i in range(x.shape[0]):
        out[i] = power(x[i], y)


@njit(cache=True, error_model="numpy")
def cbrt_array(x, out):
    """``cbrt`` of each element of the flat array ``x``, into ``out``."""
    for i in range(x.shape[0]):
        out[i] = cbrt(x[i])


def _elementwise(kernel, x, *extra):
    """``kernel`` over every element of ``x``, keeping its shape (a number
    gives a number) and, as NumPy's functions do, a floating type narrower
    than float64 (worked out in float64, then rounded to it once: the same
    everywhere too)."""
    given = np.asarray(x)
    a = given.astype(np.float64, copy=False)
    out = np.empty(a.shape)
    kernel(np.ascontiguousarray(a.reshape(-1)), *extra, out.reshape(-1))
    if given.dtype.kind == "f" and given.dtype.itemsize < 8:
        out = out.astype(given.dtype)
    return out if out.ndim else out[()]


def np_tanh(x):
    """``tanh`` of an array (or a number), as :func:`tanh` gives it."""
    return _elementwise(tanh_array, x)


def np_exp(x):
    """``exp`` of an array (or a number), as :func:`exp` gives it."""
    return _elementwise(exp_array, x)


def np_power(x, y: float):
    """``x`` to the power ``y`` for an array ``x``, as :func:`power` gives it."""
    return _elementwise(power_array, x, float(y))


def np_cbrt(x):
    """The cube root of each element of an array, as :func:`cbrt` gives it."""
    return _elementwise(cbrt_array, x)

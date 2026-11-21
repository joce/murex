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

import math
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
    """``x`` to the power ``y``, for ``x`` >= 0 and finite ``y`` (fdlibm's
    e_pow.c, without its cases of a negative ``x``: murex raises only
    amounts and lengths). Otherwise NaN, except 1 for ``y`` == 0."""
    if y == 0.0:
        return 1.0
    if x < 0.0 or x != x or y != y or abs(y) == np.inf:
        return np.nan
    if x == 0.0 or x == np.inf:
        return 0.0 if (y > 0.0) == (x == 0.0) else np.inf
    if x == 1.0 or y == 1.0:
        return x
    if y == 2.0:
        return x * x
    if y == 0.5:
        return math.sqrt(x)
    if y == -1.0:
        return 1.0 / x
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


# ---------------------------------------------------------------- log
_TWO54 = _hex(0x43500000, 0x00000000)  # 2**54
_LG1 = _hex(0x3FE55555, 0x55555593)  # 6.666666666666735130e-01
_LG2_ = _hex(0x3FD99999, 0x9997FA04)  # 3.999999999940941908e-01
_LG3 = _hex(0x3FD24924, 0x94229359)  # 2.857142874366239149e-01
_LG4 = _hex(0x3FCC71C5, 0x1D8E78AF)  # 2.222219843214978396e-01
_LG5 = _hex(0x3FC74664, 0x96CB03DE)  # 1.818357216161805012e-01
_LG6 = _hex(0x3FC39A09, 0xD078C69F)  # 1.531383769920937332e-01
_LG7 = _hex(0x3FC2F112, 0xDF3E5244)  # 1.479819860511658591e-01


@_inlined
def _log_tail(f, s, k, c):
    """log(1 + f) + k ln2 + c, for |f| < sqrt(2) - 1 and s = f / (2 + f)
    (the end of fdlibm's e_log.c and s_log1p.c)."""
    dk = float(k)
    z = s * s
    w = z * z
    t1 = w * (_LG2_ + w * (_LG4 + w * _LG6))
    t2 = z * (_LG1 + w * (_LG3 + w * (_LG5 + w * _LG7)))
    r = t2 + t1
    hfsq = 0.5 * f * f
    if k == 0:
        return f - (hfsq - s * (hfsq + r))
    return dk * _LN2_HI - ((hfsq - (s * (hfsq + r) + (dk * _LN2_LO + c))) - f)


@_inlined
def log(x):
    """The natural logarithm of ``x`` (fdlibm's e_log.c, its two polynomials
    for f near 0 and elsewhere taken as one)."""
    if x != x or x == np.inf:
        return x + x
    if x == 0.0:
        return -np.inf
    if x < 0.0:
        return np.nan
    hx = _high(x)
    k = 0
    if hx < 0x00100000:  # subnormal
        k -= 54
        x *= _TWO54
        hx = _high(x)
    k += (hx >> 20) - 1023
    hx &= 0x000FFFFF
    i = (hx + 0x95F64) & 0x100000
    x = _with_high(hx | (i ^ 0x3FF00000), _bits(x))  # x or x/2, in [sqrt(2)/2, sqrt(2))
    k += i >> 20
    f = x - 1.0
    return _log_tail(f, f / (2.0 + f), k, 0.0)


@_inlined
def log1p(x):
    """The natural logarithm of 1 + ``x``, accurate near zero (fdlibm's
    s_log1p.c)."""
    if x != x or x == np.inf:
        return x + x
    if x <= -1.0:
        return -np.inf if x == -1.0 else np.nan
    hx = _high(x)
    ax = hx & 0x7FFFFFFF
    if ax < 0x3E200000:  # |x| < 2**-29
        return x if ax < 0x3C900000 else x - x * x * 0.5
    if hx < 0x3FDA827A and (hx > 0 or hx <= -1076707644):  # 0xbfd2bec4
        return _log_tail(x, x / (2.0 + x), 0, 0.0)  # sqrt(2)/2 <= 1 + x < sqrt(2)
    c = 0.0
    if hx < 0x43400000:  # 1 + x is not x
        u = 1.0 + x
        hu = _high(u)
        k = (hu >> 20) - 1023
        c = (1.0 - (u - x) if k > 0 else x - (u - 1.0)) / u  # what 1 + x lost
    else:
        u = x
        hu = _high(u)
        k = (hu >> 20) - 1023
    hu &= 0x000FFFFF
    if hu < 0x6A09E:  # u < sqrt(2), about
        u = _with_high(hu | 0x3FF00000, _bits(u))
    else:
        k += 1
        u = _with_high(hu | 0x3FE00000, _bits(u))
    f = u - 1.0
    return _log_tail(f, f / (2.0 + f), k, c)


# ---------------------------------------------------------------- sin, cos, tan
_S1 = _hex(0xBFC55555, 0x55555549)
_S2 = _hex(0x3F811111, 0x1110F8A6)
_S3 = _hex(0xBF2A01A0, 0x19C161D5)
_S4 = _hex(0x3EC71DE3, 0x57B1FE7D)
_S5 = _hex(0xBE5AE5E6, 0x8A2B9CEB)
_S6 = _hex(0x3DE5D93A, 0x5ACFD57C)
_C1 = _hex(0x3FA55555, 0x5555554C)
_C2 = _hex(0xBF56C16C, 0x16C15177)
_C3 = _hex(0x3EFA01A0, 0x19CB1590)
_C4 = _hex(0xBE927E4F, 0x809C52AD)
_C5 = _hex(0x3E21EE9E, 0xBDB4B1C4)
_C6 = _hex(0xBDA8FAE9, 0xBE8838D4)
_INV_PIO2 = _hex(0x3FE45F30, 0x6DC9C883)  # 2/pi
_PIO2_1 = _hex(0x3FF921FB, 0x54400000)  # the first 33 bits of pi/2
_PIO2_1T = _hex(0x3DD0B461, 0x1A626331)  # pi/2 - _PIO2_1
_PIO2_2 = _hex(0x3DD0B461, 0x1A600000)  # the next 33 bits
_PIO2_2T = _hex(0x3BA3198A, 0x2E037073)
_PIO2_3 = _hex(0x3BA3198A, 0x2E000000)  # and the next
_PIO2_3T = _hex(0x397B839A, 0x252049C1)
_ROUNDER = _hex(0x43380000, 0x00000000)  # 1.5 * 2**52: adding it rounds to whole


@_inlined
def _sin_near(x, y):
    """sin(x + y) for |x + y| <= pi/4, y a tail of x (fdlibm's k_sin.c)."""
    z = x * x
    w = z * z
    r = _S2 + z * (_S3 + z * _S4) + z * w * (_S5 + z * _S6)
    v = z * x
    return x - ((z * (0.5 * y - v * r) - y) - v * _S1)


@_inlined
def _cos_near(x, y):
    """cos(x + y) for |x + y| <= pi/4, y a tail of x (fdlibm's k_cos.c)."""
    z = x * x
    w = z * z
    r = z * (_C1 + z * (_C2 + z * _C3)) + w * w * (_C4 + z * (_C5 + z * _C6))
    hz = 0.5 * z
    w = 1.0 - hz
    return w + (((1.0 - w) - hz) + (z * r - x * y))


@_inlined
def _quadrant(x):
    """``x`` = n pi/2 + y0 + y1 with |y0 + y1| <= pi/4: ``(n mod 4, y0, y1)``
    (fdlibm's e_rem_pio2.c by Cody and Waite's method, with pi/2 in three
    parts: correct for |x| < 2**20 pi/2. Beyond, where fdlibm takes the
    digits of 2/pi it needs from a table, the same on every machine still,
    but no longer exact: nothing here turns by that much.)"""
    fn = (x * _INV_PIO2 + _ROUNDER) - _ROUNDER
    n = int(fn)
    r = x - fn * _PIO2_1
    w = fn * _PIO2_1T  # good to 85 bits
    j = (_high(x) >> 20) & 0x7FF
    y0 = r - w
    if j - ((_high(y0) >> 20) & 0x7FF) > 16:  # a second round, to 118 bits
        t = r
        w = fn * _PIO2_2
        r = t - w
        w = fn * _PIO2_2T - ((t - r) - w)
        y0 = r - w
        if j - ((_high(y0) >> 20) & 0x7FF) > 49:  # a third, to 151
            t = r
            w = fn * _PIO2_3
            r = t - w
            w = fn * _PIO2_3T - ((t - r) - w)
            y0 = r - w
    return n & 3, y0, (r - y0) - w


@_inlined
def sin(x):
    """The sine of ``x``, in radians (fdlibm's s_sin.c)."""
    ix = _high(x) & 0x7FFFFFFF
    if ix <= 0x3FE921FB:  # |x| <= pi/4, about
        return x if ix < 0x3E500000 else _sin_near(x, 0.0)
    if ix >= 0x7FF00000:
        return np.nan
    n, y0, y1 = _quadrant(x)
    if n == 0:
        return _sin_near(y0, y1)
    if n == 1:
        return _cos_near(y0, y1)
    if n == 2:
        return -_sin_near(y0, y1)
    return -_cos_near(y0, y1)


@_inlined
def cos(x):
    """The cosine of ``x``, in radians (fdlibm's s_cos.c)."""
    ix = _high(x) & 0x7FFFFFFF
    if ix <= 0x3FE921FB:  # |x| <= pi/4, about
        return 1.0 if ix < 0x3E46A09E else _cos_near(x, 0.0)
    if ix >= 0x7FF00000:
        return np.nan
    n, y0, y1 = _quadrant(x)
    if n == 0:
        return _cos_near(y0, y1)
    if n == 1:
        return -_sin_near(y0, y1)
    if n == 2:
        return -_cos_near(y0, y1)
    return _sin_near(y0, y1)


@_inlined
def tan(x):
    """The tangent of ``x``, in radians: its sine over its cosine (within two
    units in the last place, not fdlibm's k_tan.c)."""
    return sin(x) / cos(x)


# ---------------------------------------------------------------- atan, atan2
_ATAN_HI = (
    _hex(0x3FDDAC67, 0x0561BB4F),  # atan(0.5)
    _hex(0x3FE921FB, 0x54442D18),  # atan(1)
    _hex(0x3FEF730B, 0xD281F69B),  # atan(1.5)
    _hex(0x3FF921FB, 0x54442D18),  # atan(inf)
)
_ATAN_LO = (
    _hex(0x3C7A2B7F, 0x222F65E2),
    _hex(0x3C81A626, 0x33145C07),
    _hex(0x3C700788, 0x7AF0CBBD),
    _hex(0x3C91A626, 0x33145C07),
)
_AT0 = _hex(0x3FD55555, 0x5555550D)
_AT1 = _hex(0xBFC99999, 0x9998EBC4)
_AT2 = _hex(0x3FC24924, 0x920083FF)
_AT3 = _hex(0xBFBC71C6, 0xFE231671)
_AT4 = _hex(0x3FB745CD, 0xC54C206E)
_AT5 = _hex(0xBFB3B0F2, 0xAF749A6D)
_AT6 = _hex(0x3FB10D66, 0xA0D03D51)
_AT7 = _hex(0xBFADDE2D, 0x52DEFD9A)
_AT8 = _hex(0x3FA97B4B, 0x24760DEB)
_AT9 = _hex(0xBFA2B444, 0x2C6A6C2F)
_AT10 = _hex(0x3F90AD3A, 0xE322DA11)
_PI = _hex(0x400921FB, 0x54442D18)
_PI_LO = _hex(0x3CA1A626, 0x33145C07)
_PIO2 = _hex(0x3FF921FB, 0x54442D18)


@_inlined
def _atan_reduce(a, ix):
    """|x| = a, high word ix, for 7/16 <= a < 2**66: ``(id, x)`` with
    atan(a) = atan(id's point) + atan(x)."""
    if ix < 0x3FF30000:  # a < 19/16
        if ix < 0x3FE60000:  # a < 11/16
            return 0, (2.0 * a - 1.0) / (2.0 + a)
        return 1, (a - 1.0) / (a + 1.0)
    if ix < 0x40038000:  # a < 39/16
        return 2, (a - 1.5) / (1.0 + 1.5 * a)
    return 3, -1.0 / a


@_inlined
def atan(x):
    """The arc tangent of ``x``, in radians (fdlibm's s_atan.c)."""
    if x != x:
        return x
    hx = _high(x)
    ix = hx & 0x7FFFFFFF
    if ix >= 0x44100000:  # |x| >= 2**66
        return _ATAN_HI[3] + _ATAN_LO[3] if hx > 0 else -_ATAN_HI[3] - _ATAN_LO[3]
    k = -1
    if ix < 0x3FDC0000:  # |x| < 7/16
        if ix < 0x3E400000:  # |x| < 2**-27
            return x
    else:
        k, x = _atan_reduce(-x if hx < 0 else x, ix)
    z = x * x
    w = z * z
    s1 = z * (_AT0 + w * (_AT2 + w * (_AT4 + w * (_AT6 + w * (_AT8 + w * _AT10)))))
    s2 = w * (_AT1 + w * (_AT3 + w * (_AT5 + w * (_AT7 + w * _AT9))))
    if k < 0:
        return x - x * (s1 + s2)
    z = _ATAN_HI[k] - ((x * (s1 + s2) - _ATAN_LO[k]) - x)
    return -z if hx < 0 else z


@_inlined
def _atan2_edge(y, x, m):
    """atan2 where ``y`` or ``x`` is zero or infinite; m = 2 sign(x) + sign(y)."""
    if y == 0.0:
        return y if m < 2 else (_PI if m == 2 else -_PI)
    if x == 0.0:
        return -_PIO2 if y < 0.0 else _PIO2
    if abs(x) == np.inf:
        if abs(y) == np.inf:
            z = 0.25 * _PI if m < 2 else 0.75 * _PI
        else:
            z = 0.0 if m < 2 else _PI
        return -z if m & 1 else z
    return -_PIO2 if y < 0.0 else _PIO2  # y infinite


@_inlined
def atan2(y, x):
    """The angle of the point (``x``, ``y``) from the x axis, in radians, from
    -pi to pi (fdlibm's e_atan2.c)."""
    if x != x or y != y:
        return x + y
    if x == 1.0:
        return atan(y)
    hx = _high(x)
    hy = _high(y)
    m = ((hy >> 31) & 1) | ((hx >> 30) & 2)  # 2 sign(x) + sign(y)
    if y == 0.0 or x == 0.0 or abs(x) == np.inf or abs(y) == np.inf:
        return _atan2_edge(y, x, m)
    k = ((hy & 0x7FFFFFFF) - (hx & 0x7FFFFFFF)) >> 20
    if k > 60:  # |y/x| > 2**60
        z = _PIO2 + 0.5 * _PI_LO
        m &= 1
    elif hx < 0 and k < -60:  # 0 > |y|/x > -2**-60
        z = 0.0
    else:
        z = atan(abs(y / x))
    if m == 0:
        return z
    if m == 1:
        return -z
    if m == 2:
        return _PI - (z - _PI_LO)
    return (z - _PI_LO) - _PI


# ---------------------------------------------------------------- hypot
@_inlined
def hypot(x, y):
    """The length of (``x``, ``y``): the square root of x*x + y*y, which every
    machine rounds alike (within a unit in the last place; not scaled against
    overflow, which lengths on a canvas or a sheet never come near)."""
    return math.sqrt(x * x + y * y)


# ---------------------------------------------------------------- arrays
# Each function over every element of a flat array, into another.
@njit(cache=True, error_model="numpy")
def tanh_array(x, out):
    for i in range(x.shape[0]):
        out[i] = tanh(x[i])


@njit(cache=True, error_model="numpy")
def exp_array(x, out):
    for i in range(x.shape[0]):
        out[i] = exp(x[i])


@njit(cache=True, error_model="numpy")
def log_array(x, out):
    for i in range(x.shape[0]):
        out[i] = log(x[i])


@njit(cache=True, error_model="numpy")
def log1p_array(x, out):
    for i in range(x.shape[0]):
        out[i] = log1p(x[i])


@njit(cache=True, error_model="numpy")
def sin_array(x, out):
    for i in range(x.shape[0]):
        out[i] = sin(x[i])


@njit(cache=True, error_model="numpy")
def cos_array(x, out):
    for i in range(x.shape[0]):
        out[i] = cos(x[i])


@njit(cache=True, error_model="numpy")
def cbrt_array(x, out):
    for i in range(x.shape[0]):
        out[i] = cbrt(x[i])


@njit(cache=True, error_model="numpy")
def power_array(x, y, out):
    """``power(x[i], y)``."""
    for i in range(x.shape[0]):
        out[i] = power(x[i], y)


@njit(cache=True, error_model="numpy")
def powers_array(x, y, out):
    """``power(x[i], y[i])``."""
    for i in range(x.shape[0]):
        out[i] = power(x[i], y[i])


@njit(cache=True, error_model="numpy")
def atan2_array(y, x, out):
    for i in range(x.shape[0]):
        out[i] = atan2(y[i], x[i])


@njit(cache=True, error_model="numpy")
def hypot_array(x, y, out):
    for i in range(x.shape[0]):
        out[i] = hypot(x[i], y[i])


@njit(cache=True, error_model="numpy")
def interp_array(x, xp, fp, out):
    """``np.interp(x, xp, fp)``, worked out as NumPy does (so the same where
    NumPy's compiler does not fuse its multiply and add, as on x86-64)."""
    n = xp.shape[0]
    for i in range(x.shape[0]):
        v = x[i]
        if v != v or v < xp[0] or v >= xp[n - 1]:
            out[i] = v if v != v else (fp[0] if v < xp[0] else fp[n - 1])
            continue
        lo = 0
        hi = n - 1  # xp[lo] <= v < xp[hi]
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if xp[mid] <= v:
                lo = mid
            else:
                hi = mid
        if xp[lo] == v:
            out[i] = fp[lo]
            continue
        slope = (fp[lo + 1] - fp[lo]) / (xp[lo + 1] - xp[lo])
        r = slope * (v - xp[lo]) + fp[lo]
        if r != r:
            r = slope * (v - xp[lo + 1]) + fp[lo + 1]
            if r != r and fp[lo] == fp[lo + 1]:
                r = fp[lo]
        out[i] = r


def _flat(x) -> np.ndarray:
    """``x`` as a flat, contiguous array of float64 (itself, if it is one)."""
    if (
        type(x) is np.ndarray
        and x.dtype == np.float64
        and x.ndim == 1
        and x.flags.c_contiguous
    ):
        return x
    return np.ascontiguousarray(x, dtype=np.float64).reshape(-1)


def _elementwise(kernel, *operands, scalars=()):
    """``kernel`` over every element of the operands, broadcast together,
    keeping their shape (numbers give a number) and, as NumPy's functions
    do, a floating type narrower than float64 (worked out in float64, then
    rounded to it once: the same everywhere too)."""
    given = [x if type(x) is np.ndarray else np.asarray(x) for x in operands]
    shaped = np.broadcast_arrays(*given) if len(given) > 1 else given
    out = np.empty(shaped[0].shape)
    kernel(*[_flat(x) for x in shaped], *scalars, out.reshape(-1))
    kind = given[0].dtype if len(given) == 1 else np.result_type(*given)
    if kind.kind == "f" and kind.itemsize < 8:
        out = out.astype(kind)
    return out if out.ndim else out[()]


def np_tanh(x):
    """``tanh`` of an array (or a number), as :func:`tanh` gives it."""
    return _elementwise(tanh_array, x)


def np_exp(x):
    """``exp`` of an array (or a number), as :func:`exp` gives it."""
    return _elementwise(exp_array, x)


def np_log(x):
    """``log`` of an array (or a number), as :func:`log` gives it."""
    return _elementwise(log_array, x)


def np_log1p(x):
    """``log1p`` of an array (or a number), as :func:`log1p` gives it."""
    return _elementwise(log1p_array, x)


def np_sin(x):
    """``sin`` of an array (or a number), as :func:`sin` gives it."""
    return _elementwise(sin_array, x)


def np_cos(x):
    """``cos`` of an array (or a number), as :func:`cos` gives it."""
    return _elementwise(cos_array, x)


def np_power(x, y):
    """``x`` to the power ``y``, element by element, as :func:`power` gives
    it (``y`` a number or an array)."""
    if np.ndim(y) == 0:
        return _elementwise(power_array, x, scalars=(float(y),))
    return _elementwise(powers_array, x, y)


def np_cbrt(x):
    """The cube root of each element of an array, as :func:`cbrt` gives it."""
    return _elementwise(cbrt_array, x)


def np_atan2(y, x):
    """``atan2`` element by element, as :func:`atan2` gives it."""
    return _elementwise(atan2_array, y, x)


def np_hypot(x, y):
    """``hypot`` element by element, as :func:`hypot` gives it."""
    return _elementwise(hypot_array, x, y)


def np_interp(x, xp, fp):
    """``np.interp(x, xp, fp)``, the same on every machine (the end values
    beyond the ends, as NumPy's defaults)."""
    xp, fp = _flat(xp), _flat(fp)
    if xp.shape != fp.shape or xp.size == 0:
        raise ValueError("xp and fp must be of the same length, not empty")
    given = x if type(x) is np.ndarray else np.asarray(x, dtype=np.float64)
    out = np.empty(given.shape)
    interp_array(_flat(given), xp, fp, out.reshape(-1))
    return out if out.ndim else out[()]

"""The colour science gives the same numbers to the last bit, on any machine.

oilpaint and fusain check their pictures byte for byte, so murex's numbers
must not move with the NumPy, the BLAS or the processor that works them out.
The two tables the colour model rests on, ``SPECTRUM_TO_RGB`` and ``_BASIS``,
are therefore stored as literals (``murex/_spectral_tables.py``), not solved
for at import: what ``np.linalg.solve`` returns differs in its last bits from
one NumPy and BLAS to another. The code that derives them is kept, and what it
gives agrees with the tables to rounding (``test_tables_agree_with_their_derivation``).

The pins below are exact: ``float.hex`` of single numbers, and the SHA-256 of
the bytes of whole arrays. They were taken with NumPy 2.5 on x86-64 and hold
under every NumPy, BLAS and processor this was tried with (CI adds ARM). If one
fails, a result of ``spectral`` has changed: that is a breaking change for
oilpaint and fusain, not a number to update.

Only inputs whose result does not depend on the processor are pinned. Some do:
NumPy's ``power`` and ``tanh`` on arrays take a SIMD path on processors with
AVX-512 that rounds some values differently from the one the other processors
use, and a BLAS with fused multiply-add sums a product differently from one
without, so that for many colours (#336699, #a0522d, #f5deb3 and others) the
last bit of the reflectance is that of the machine it was worked out on. The
same goes for ``solve_absorption`` and so for the optics of a ``Pigment``, which
are not pinned.
"""

import hashlib

import numpy as np
import pytest

from murex import spectral as sp


def digest(array) -> str:
    return hashlib.sha256(
        np.ascontiguousarray(array, dtype="<f8").tobytes()
    ).hexdigest()


def hexes(array) -> list[str]:
    return [float(x).hex() for x in np.ravel(array)]


def test_tables_are_exactly_what_they_were():
    assert digest(sp.SPECTRUM_TO_RGB) == (
        "0e44b19ab8e0f928059a7f6c231ab3461f27d6d3076a2fd871fcb7453859563b"
    )
    assert digest(sp._BASIS) == (
        "527b463ee235e94b9030dcecf95633dfd4b4ffb5305eed08932951e099573d91"
    )
    assert sp.SPECTRUM_TO_RGB.shape == (3, sp.N_BANDS)
    assert sp._BASIS.shape == (7, sp.N_BANDS)
    assert not sp.SPECTRUM_TO_RGB.flags.writeable
    assert not sp._BASIS.flags.writeable


def test_tables_agree_with_their_derivation():
    # Worked out again, they differ from the stored tables in the last bits at
    # most, and by a different amount on another NumPy or BLAS: that is why
    # they are stored.
    matrix = sp._build_spectrum_to_rgb(sp.WAVELENGTHS)
    np.testing.assert_allclose(matrix, sp.SPECTRUM_TO_RGB, rtol=0, atol=1e-13)
    np.testing.assert_allclose(sp._build_basis(matrix), sp._BASIS, rtol=0, atol=1e-13)


# colour: (SHA-256 of its reflectance spectrum, bands 0, 11 and 23)
REFLECTANCES = {
    "#ff0000": (
        "e2137527fe7bbfa1d0198c8a84a6cbaad726bb85dcf53f046053fb1db9f48658",
        ["0x1.325810b10d530p-5", "0x1.1515f3f3d0e40p-8", "0x1.faaeb25f8b937p-1"],
    ),
    "#00ff00": (
        "48540ae2f352d55f17cf391c6639501d0591520eb180371a5795d864148b784f",
        ["0x1.c34a3c6344fc0p-8", "0x1.f7a14283c71dfp-1", "0x1.5b04b32c9c980p-6"],
    ),
    "#0000ff": (
        "4b273d7c45099e48a85d0fbc048c11af96c524a45ee4101205cc5794f38b5661",
        ["0x1.f72995d887acap-1", "0x1.1130a89812e70p-6", "0x1.19a0a44226c20p-6"],
    ),
    "#ffffff": (
        "eaa390108ebc47a471b35cf1c0ec71e97d591f646ecdc47ab19e98ba5ee9ab5e",
        ["0x1.fff2e48e8a6a2p-1", "0x1.fff2e48e8a6a2p-1", "0x1.fff2e48e8a6a2p-1"],
    ),
    "#808080": (
        "d98aa1eabf71c34f632a9218c1357ac77f5bbb45fb5c8f5851e2c07d651d7557",
        ["0x1.ba09c0a8de4a4p-3", "0x1.ba09c0a8de4a4p-3", "0x1.ba09c0a8de4a4p-3"],
    ),
    "#ff8000": (
        "73b5ded57ab6dc6618c7916e307fb4d87a051903c62d57e2f0132c597de4b34e",
        ["0x1.0ebd433c85846p-5", "0x1.b98030d1784f0p-3", "0x1.f9ee35d846a81p-1"],
    ),
    "#ffd700": (
        "12c237ef60edb58642931753e4265977a3fbfb3ebd6430d245e64936c0b810f9",
        ["0x1.84842f04da110p-6", "0x1.56d16cca2a5c9p-1", "0x1.f850bcc0f58b6p-1"],
    ),
    "#4b0082": (
        "848348dedb2000b7715a808224cd464765969c56c27b92f73b5c4606046cf81f",
        ["0x1.c2c6509b1681dp-3", "0x1.e4dbf89046c64p-9", "0x1.24da9538218b7p-4"],
    ),
    "#dc143c": (
        "e233956c00c66ce73364c5aa8ddb7094c75e11b83f218a085e6f672dda9d4e9b",
        ["0x1.1eb4a0bf1cc77p-4", "0x1.568e0f9895c93p-7", "0x1.6a747ff353a1dp-1"],
    ),
    "#7fff00": (
        "cfcfbb2a5486b285f5a2440b0e067780eb1a4aa41ecd9a7971e898cd60defffa",
        ["0x1.29cb7013682dbp-7", "0x1.f7982e35a0fecp-1", "0x1.cd59404f46e83p-3"],
    ),
}


@pytest.mark.parametrize("color", REFLECTANCES)
def test_srgb_to_reflectance_to_the_bit(color):
    expected_digest, expected_bands = REFLECTANCES[color]
    R = sp.srgb_to_reflectance(color)
    assert hexes(R[[0, 11, 23]]) == expected_bands
    assert digest(R) == expected_digest


# colour: (linear sRGB, sRGB) of its reflectance spectrum
SPECTRUM_COLORS = {
    "#ff8000": (
        ["0x1.fff2e48e8a71dp-1", "0x1.ba32dd33aca7ap-3", "0x1.a36e2eb1c4428p-14"],
        ["0x1.fffa3cf5c72b1p-1", "0x1.010902d618bf6p-1", "0x1.52b0a6fc58b84p-10"],
    ),
    "#4b0082": (
        ["0x1.203a8f2c6a408p-4", "0x1.7683ad78b1330p-16", "0x1.c9200924685a5p-3"],
        ["0x1.2d31a5e1f0bf2p-2", "0x1.2e6b9c1404d93p-12", "0x1.0501ef57ecf23p-1"],
    ),
    "#7fff00": (
        ["0x1.b2c436d191088p-3", "0x1.fff2e48e8a71fp-1", "0x1.a36e2eb1c4900p-14"],
        ["0x1.fe0e5f4ba0603p-2", "0x1.fffa3cf5c72b1p-1", "0x1.52b0a6fc58f6dp-10"],
    ),
}


@pytest.mark.parametrize("color", SPECTRUM_COLORS)
def test_spectrum_to_rgb_to_the_bit(color):
    linear, srgb = SPECTRUM_COLORS[color]
    R = sp.srgb_to_reflectance(color)
    assert hexes(sp.reflectance_to_linear_rgb(R)) == linear
    assert hexes(sp.reflectance_to_srgb(R)) == srgb


def test_kubelka_munk_mix_to_the_bit():
    # a part of one dye and two of another (absorptions made of plain
    # arithmetic), half a thickness over white
    x = np.linspace(0.0, 1.0, sp.N_BANDS)
    K1 = 0.2 + 2.5 * (1 - x) ** 2
    K2 = 0.1 + 1.8 * (x - 0.6) ** 2 * 4
    K = (1 * K1 + 2 * K2) / 3
    S = (1 * 1.2 + 2 * 0.9) / 3
    assert (
        digest(K) == "b81d597ae9ddb0154ab14d7812d3ac2e5e8eac34aaf9b60e910bc0f9318e94c6"
    )
    R = sp.km_layer(K * 0.5, S * 0.5, sp.srgb_to_reflectance("#ffffff"))
    assert hexes(R[[0, 11, 23]]) == [
        "0x1.5383e81b50348p-3",
        "0x1.564dc37ff016ap-1",
        "0x1.d3d9239944c44p-2",
    ]
    assert (
        digest(R) == "4d7aca91335ae43dc5123d3522785da55ac6b7d62baa880a57c3c7cb730d7fff"
    )
    assert hexes(sp.reflectance_to_linear_rgb(R)) == [
        "0x1.a59c789ab8b3ep-1",
        "0x1.5496533335548p-1",
        "0x1.051550b9fa976p-2",
    ]
    srgb = sp.reflectance_to_srgb(R)
    assert hexes(srgb) == [
        "0x1.d60150ef71167p-1",
        "0x1.ab9eab4e9045ep-1",
        "0x1.157d0391229b5p-1",
    ]
    assert sp.to_hex(srgb) == "#ead58a"


def test_kubelka_munk_functions_to_the_bit():
    K = np.linspace(0.1, 3.0, sp.N_BANDS)
    ground = np.full(sp.N_BANDS, 0.6)
    assert digest(sp.km_layer(K, 0.7, ground)) == (
        "f11275fd983214bed0ccda8401207dcb6dc9adb25c8cb8e404a1aed5ad0e0dd5"
    )
    assert digest(sp.km_opaque(K, 0.7)) == (
        "6a4a4e1bb865eb03a843d95cca0d746841b4c52a290b52d72760ba9b52a54653"
    )

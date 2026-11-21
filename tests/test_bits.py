"""The colour science gives the same numbers to the last bit, on any machine.

The media check their pictures byte for byte, so murex's numbers must not
move with the NumPy, the BLAS or the processor that works them out. The two
tables the colour model rests on, ``SPECTRUM_TO_RGB`` and ``_BASIS``, are
stored as literals (``murex/_spectral_tables.py``), not solved for at import;
powers, roots, ``exp`` and ``tanh`` are murex's own (``murex._libm``), made of
IEEE arithmetic only, not NumPy's SIMD routines or the C library; and sums
are taken in a fixed order by compiled loops, not by BLAS.

So every result can be pinned, and is: the SHA-256 of the bytes of what each
computation below gives. They were recorded on x86-64 and hold on ARM too
(CI runs this file on both). If one fails, a result of ``spectral`` has
changed: that is a breaking change for every medium, to be said in the
changelog with the pictures recorded again, not a number to update.
``python tests/test_bits.py`` prints the pins of the code as it is.
"""

import hashlib

import numpy as np
import pytest

from murex import Pigment, mix_colors
from murex import spectral as sp


def digest(array) -> str:
    data = np.ascontiguousarray(array, dtype="<f8").tobytes()
    return hashlib.sha256(data).hexdigest()


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


# Colours of every kind: primaries, secondaries, greys, darks, and the ones
# whose last bit used to be the processor's (#336699, #a0522d, #f5deb3).
COLORS = [
    "#ff0000",
    "#00ff00",
    "#0000ff",
    "#ffffff",
    "#000000",
    "#808080",
    "#ff8000",
    "#ffd700",
    "#4b0082",
    "#dc143c",
    "#7fff00",
    "#336699",
    "#a0522d",
    "#f5deb3",
    "#2e8b57",
    "#c71585",
    "#0a0a0a",
    "#fefefe",
]
GRID = np.linspace(0.0, 1.0, 1001)


def _reflectances():
    return np.array([sp.srgb_to_reflectance(c) for c in COLORS])


def _mix():
    # a part of one dye and two of another, half a thickness over white
    x = np.linspace(0.0, 1.0, sp.N_BANDS)
    K = (0.2 + 2.5 * (1 - x) ** 2 + 2 * (0.1 + 1.8 * (x - 0.6) ** 2 * 4)) / 3
    return sp.km_layer(K * 0.5, (1.2 + 2 * 0.9) / 6, sp.srgb_to_reflectance("#ffffff"))


def _layers():
    # a batch over a ground for each layer: the compiled path
    rng = np.random.default_rng(3)
    kappa = rng.uniform(0.0, 3.0, (500, sp.N_BANDS))
    kappa[::7] *= 1e-6  # nearly empty layers: tanh's series
    sigma = rng.uniform(0.0, 2.0, 500)
    return sp.km_layer(kappa, sigma, _reflectances()[np.arange(500) % len(COLORS)])


def _pigments():
    optics = []
    for color in COLORS:
        for opacity in (1.0, 0.3):
            p = Pigment(color, opacity=opacity)
            optics.append(np.append(p.K, p.S))
    return np.array(optics)


COMPUTED = {
    "srgb_to_linear": lambda: sp.srgb_to_linear(GRID),
    "linear_to_srgb": lambda: sp.linear_to_srgb(GRID),
    "srgb_to_lab": lambda: sp.srgb_to_lab(
        np.array([sp.parse_color(c) for c in COLORS])
    ),
    "srgb_to_reflectance": _reflectances,
    "reflectance_to_linear_rgb": lambda: sp.reflectance_to_linear_rgb(_reflectances()),
    "reflectance_to_srgb": lambda: sp.reflectance_to_srgb(_reflectances()),
    "km_layer, one": _mix,
    "km_layer, a batch": _layers,
    "km_film": lambda: np.array(sp.km_film(np.linspace(0.0, 4.0, 24), 0.7)),
    "km_opaque": lambda: sp.km_opaque(np.linspace(0.1, 3.0, 24), 0.7),
    "solve_absorption": lambda: np.array(
        [sp.solve_absorption(R, 1.5) for R in _reflectances()]
    ),
    "Pigment optics": _pigments,
}
PINS = {
    "srgb_to_linear": (
        "e3e3a0f05243212573cdf87f99db64abf77a6bc2cae63eeaf1bb612a5f684bb1"
    ),
    "linear_to_srgb": (
        "6aa4e14cc21c589208b8a0c23d20e180a152906e3191933d89f7f68f188aeb6e"
    ),
    "srgb_to_lab": ("03e1ab705c640b2e10c41a60c6c71691be6ae94ef8dc0649550508394475ba8f"),
    "srgb_to_reflectance": (
        "e64bc6f2cb0923d31479bf98592293c6e59af661358a26a14ec9ee7b290e2cfb"
    ),
    "reflectance_to_linear_rgb": (
        "958f0f6b6d427c195f8eb86820837a0d1715b63d4778f1ce5ce0db0a45495dc9"
    ),
    "reflectance_to_srgb": (
        "1d432ad745351de303537c4e0040643ffc4f9585c95ce2bebe1e92e59c4ba1f8"
    ),
    "km_layer, one": (
        "d6c88b887a7c3f0bc0f0bf69c92e11b875aa0bb97a4f88885559d8566426b065"
    ),
    "km_layer, a batch": (
        "0dacce5a1e384d51a4e6e7f938f391d454675f69297658e30747740ab5c37042"
    ),
    "km_film": ("6c63b030ddc69f84bf0d0120b10b04adcc7af4e5aa484ef055751b829ffeb179"),
    "km_opaque": ("6a4a4e1bb865eb03a843d95cca0d746841b4c52a290b52d72760ba9b52a54653"),
    "solve_absorption": (
        "7138a2fd86ba3d71cb0474a8bd11703fbea9818d11851eb80a0259b187c836cb"
    ),
    "Pigment optics": (
        "8eebba89f5ac2d1502469fe07e19a0229dc9bca699e58e323c67df625fdb09bb"
    ),
}


@pytest.mark.parametrize("name", COMPUTED)
def test_to_the_bit(name):
    assert digest(COMPUTED[name]()) == PINS[name]


def test_what_a_mix_looks_like():
    # (the pins above, in a form a person can read)
    assert sp.to_hex(sp.reflectance_to_srgb(_mix())) == "#ead58a"
    assert mix_colors(["#1b3fa0", "#f5d000"]) == "#418340"


if __name__ == "__main__":
    for name, compute in COMPUTED.items():
        print(f'    "{name}": (\n        "{digest(compute())}"\n    ),')

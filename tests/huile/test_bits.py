"""huile paints the same picture to the last bit on any machine.

What a stroke computes is IEEE arithmetic, which every processor rounds
alike, and murex's own elementary functions and random draws
(``murex._libm``, ``murex._random``), not the C library's or NumPy's, which
round some values differently from one machine to the next. So what a few
small paintings leave on the canvas, and how they look, can be pinned: the
SHA-256 of every array :mod:`tools/huile/bench.py` keeps of a scene (its
state and its picture). They were recorded on x86-64 and CI checks them on
ARM and on Windows too.

If one fails on every machine, the picture has changed: if it was meant to,
pin it again (``python tests/huile/test_bits.py`` prints the pins).
"""

import hashlib
import importlib.util
import os
import sys

import numpy as np
import pytest

from murex.huile import Canvas, brushes, surfaces
from murex.huile import palette as P


def _bench():
    path = os.path.join(os.path.dirname(__file__), "..", "..", "tools", "huile")
    spec = importlib.util.spec_from_file_location(
        "huile_bits_bench", os.path.join(path, "bench.py")
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    saved = list(sys.path)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = saved
    return module


bench = _bench()


def _brushes() -> tuple[Canvas, tuple]:
    """Hair of every kind, dabs, a stipple, drying, and paint over it."""
    c = Canvas(96, 64, seed=1)
    c.stroke([(6, 10), (50, 14), (90, 8)], P.CADMIUM_RED, width=14)
    c.stroke(
        [(8, 50), (48, 30), (88, 52)],
        P.PHTHALO_BLUE,
        brush=brushes.FILBERT_SABLE,
        pressure=lambda u: 0.3 + 0.5 * u,
        angle=lambda u: 60 * u,
    )
    c.stroke([(20, 6), (24, 58)], P.TITANIUM_WHITE, brush=brushes.FAN_HOG, amount=3)
    c.stroke([(70, 30)], P.CADMIUM_YELLOW, brush=brushes.ROUND, width=12)
    c.stipple([(30, 40), (60, 40)], P.BURNT_SIENNA, brush=brushes.STIPPLER)
    c.dry()
    c.stroke([(4, 32), (92, 34)], P.ULTRAMARINE_BLUE, brush=brushes.FLAT_HOG, amount=2)
    return c, ()


def _knives() -> tuple[Canvas, tuple]:
    """Blades of every shape over thick paint, on a coarse linen."""
    c = Canvas(96, 64, seed=2, surface=surfaces.LINEN_COARSE)
    c.stroke([(6, 20), (90, 24)], P.CADMIUM_YELLOW, amount=12, width=20)
    c.stroke([(6, 44), (90, 40)], P.ALIZARIN_CRIMSON, amount=12, width=20)
    c.stroke([(10, 8), (80, 56)], P.TITANIUM_WHITE, brush=brushes.PALETTE_KNIFE)
    c.stroke([(80, 8), (14, 58)], None, brush=brushes.KNIFE_PEAR)
    c.stroke([(4, 32), (92, 30)], None, brush=brushes.KNIFE_COMB)
    return c, ()


def _spatter() -> tuple[Canvas, tuple]:
    """Flicked drops (normal, gamma and log-normal draws) on a panel."""
    c = Canvas(96, 64, seed=3, surface=surfaces.GESSO_PANEL)
    c.spatter([(10, 32), (40, 30)], P.PHTHALO_GREEN, amount=2.0, reach=40, seed=5)
    c.spatter([(80, 10)], P.CADMIUM_RED, amount=1.0, direction=200, size=4, seed=6)
    return c, ()


SCENES = {"brushes": _brushes, "knives": _knives, "spatter": _spatter}


def scene_digests(name: str) -> dict[str, str]:
    canvas, tools = SCENES[name]()
    arrays = {**bench.canvas_state(canvas, tools), **bench.canvas_picture(canvas)}
    out = {}
    for key in sorted(arrays):
        a = np.ascontiguousarray(arrays[key])
        mark = hashlib.sha256(f"{a.dtype.str}{a.shape}".encode())
        mark.update(a.tobytes())
        out[key] = mark.hexdigest()[:16]
    return out


def digest(name: str) -> str:
    marks = scene_digests(name)
    return hashlib.sha256(repr(sorted(marks.items())).encode()).hexdigest()


PINS = {
    "brushes": "776a58a91e252de0e7094f5f23002a3847905765939c548b890969d59907b1a3",
    "knives": "57b2e3f825a3abea24aa4b66f264a7636286386d93280d76de9712c0092292cb",
    "spatter": "e839d48ed552a760bf3596e8f3877e35f61f320d37504a761099fb5f2f6b28ad",
}


@pytest.mark.parametrize("name", SCENES)
def test_to_the_bit(name):
    assert digest(name) == PINS[name], (
        "the picture has changed (if it was meant to, pin it again: "
        "python tests/huile/test_bits.py)"
    )


if __name__ == "__main__":
    for scene in SCENES:
        print(f'    "{scene}": "{digest(scene)}",')

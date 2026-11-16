"""Write ``murex/_spectral_tables.py``: the two tables of ``murex.spectral``
that are stored, not computed at import.

``SPECTRUM_TO_RGB`` and the basis spectra ``_BASIS`` rest on the arithmetic of
NumPy (``np.interp``, matrix products, ``np.linalg.solve``), which rounds
differently from one NumPy, BLAS or processor to another. Stored, they are the
same everywhere, and so is every colour built on them.

Run it only to change the model (the wavelengths, the observer, the basis):
the numbers it writes become the new ones, a breaking change for the libraries
that check their pictures byte for byte. ``tests/test_spectral.py`` checks that
the stored tables agree with what this derives (to 1e-13, not to the last bit).

    uv run python tools/derive_spectral_tables.py          # write the module
    uv run python tools/derive_spectral_tables.py --check  # agree to 1e-13?
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np

from murex import spectral

TARGET = Path(__file__).resolve().parent.parent / "murex" / "_spectral_tables.py"

#: How far a freshly derived table may stray from the stored one.
TOLERANCE = 1e-13


def derive() -> tuple[np.ndarray, np.ndarray]:
    """``(SPECTRUM_TO_RGB, _BASIS)``, worked out here and now."""
    matrix = spectral._build_spectrum_to_rgb(spectral.WAVELENGTHS)
    return matrix, spectral._build_basis(matrix)


def literal(name: str, table: np.ndarray) -> str:
    """A table as Python source: ``repr`` of a float64 round-trips exactly."""
    rows = ",\n".join(
        "    [" + ", ".join(repr(float(x)) for x in row) + "]" for row in table
    )
    return f"{name} = [\n{rows},\n]\n"


def render(matrix: np.ndarray, basis: np.ndarray) -> str:
    return (
        '"""The tables of murex.spectral that are stored, not computed (written by\n'
        "``tools/derive_spectral_tables.py``; do not edit by hand).\n\n"
        "Each number is the float64 it was derived as, written with ``repr``, so\n"
        "that it reads back to the last bit.\n"
        '"""\n\n'
        "# (3, N_BANDS): linear sRGB = matrix @ reflectance\n"
        + literal("SPECTRUM_TO_RGB_TABLE", matrix)
        + "\n# (7, N_BANDS): white, cyan, magenta, yellow, red, green, blue\n"
        + literal("BASIS_TABLE", basis)
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Write the stored spectral tables.")
    parser.add_argument(
        "--check",
        action="store_true",
        help=f"compare a fresh derivation with the stored tables (to {TOLERANCE})",
    )
    args = parser.parse_args()
    matrix, basis = derive()
    if args.check:
        for name, fresh, stored in (
            ("SPECTRUM_TO_RGB", matrix, spectral.SPECTRUM_TO_RGB),
            ("_BASIS", basis, spectral._BASIS),
        ):
            worst = float(np.abs(fresh - stored).max())
            print(f"{name}: largest difference {worst:.3g}")
            if worst > TOLERANCE:
                return 1
        return 0
    TARGET.write_text(render(matrix, basis))
    subprocess.run([sys.executable, "-m", "black", "--quiet", str(TARGET)], check=True)
    print(f"wrote {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

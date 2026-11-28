"""The spectra of the core pigments, taken out of Deborah's spectral library.

H. Deborah, "Hyperspectral pigments", Zenodo 2022 (CC BY 4.0), is an ENVI
spectral library of the median spectra of Kremer colour charts, each pigment
at four thicknesses, 405 to 996 nm. Its two files are kept in Git LFS under
``docs/aquarelle/references/spectra/``; this writes, beside them, the
spectra of the pigments aquarelle is judged on, as ordinary text that a test
can read where the LFS files are not fetched (in CI)::

    python tools/aquarelle/extract_deborah.py

It writes three files: ``deborah2022_core_raw.csv`` (the library's own
bands), ``deborah2022_core_10nm.csv`` (means over 10 nm, 410 to 700 nm) and
``deborah2022_core_murex24.csv`` (means over murex's 24 bands, as wide as
their spacing: the first, at 400 nm, holds only 405 to 406.5 nm, the
library starting at 405). See ``docs/aquarelle/references.md``,
``deborah2022``.
"""

# cspell:ignore hostaperm pnumber speclib

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np

from murex import spectral as sp

HERE = Path(__file__).resolve().parents[2] / "docs/aquarelle/references/spectra"

#: The pigments taken out: a label, and the pigment's Kremer number.
CORE = (
    ("ultramarine_dark_K45010", "45010"),
    ("ultramarine_light_K45080", "45080"),
    ("cobalt_blue_medium_K45710", "45710"),
    ("cobalt_cerulean_K45730", "45730"),
    ("phthalo_blue_K23050", "23050"),
    ("phthalo_green_dark_K23000", "23000"),
    ("viridian_K44250", "44250"),
    ("alizarin_light_K23600", "23600"),
    ("burnt_sienna_france_K40470", "40470"),
    ("cadmium_red_light_K21120", "21120"),
    ("cadmium_yellow_medium_K21040", "21040"),
    ("hostaperm_pink_E_K23153", "23153"),
    ("hostaperm_red_K23720", "23720"),
    ("ivory_black_K12000", "12000"),
)


def _field(header: str, name: str) -> str:
    found = re.search(r"\n" + name + r" = \{(.*?)\}\s*\n", header, re.DOTALL)
    if found is None:
        raise ValueError(f"the library's header has no {name!r}")
    return found.group(1)


def _library(folder: Path):
    """The names, Kremer numbers, wavelengths and spectra of the library."""
    header = (folder / "deborah2022_speclib_medians.hdr").read_text()
    names = [s.strip() for s in _field(header, "spectra names").split(",")]
    numbers = [s.strip() for s in _field(header, "pnumber").split(",")]
    wavelengths = np.array([float(x) for x in _field(header, "wavelength").split(",")])
    data = np.fromfile(folder / "deborah2022_speclib_medians.sli", dtype="<f4")
    return names, numbers, wavelengths, data.reshape(len(names), len(wavelengths))


def _core(names, numbers, spectra):
    """The core pigments' spectra, one column each, and their labels: of each
    pigment, the four thicknesses of its first patch."""
    columns, labels = [], []
    for label, number in CORE:
        rows = [i for i, n in enumerate(numbers) if n == number]
        if not rows:
            raise ValueError(f"no pigment {number} in the library")
        patch = names[rows[0]].rsplit("_sh", 1)[0]
        for i in rows:
            if names[i].startswith(patch + "_sh"):
                columns.append(spectra[i])
                labels.append(f"{label}_{names[i].rsplit('_', 1)[1]}")
    return np.column_stack(columns), labels


def _banded(wavelengths, core, centres):
    """Means of ``core`` over bands around ``centres``, as wide as their
    spacing."""
    half = (centres[1] - centres[0]) / 2
    return np.array(
        [
            core[(wavelengths >= c - half) & (wavelengths < c + half)].mean(axis=0)
            for c in centres
        ]
    )


def main(folder: Path = HERE) -> None:
    names, numbers, wavelengths, spectra = _library(folder)
    core, labels = _core(names, numbers, spectra)
    header = "wavelength_nm," + ",".join(labels)
    outputs = {
        "raw": (wavelengths, core, ""),
        "10nm": (np.arange(410.0, 701.0, 10.0), None, "  (box mean)"),
        "murex24": (
            sp.WAVELENGTHS,
            None,
            "  (box mean; murex24 first band 400 nm has only 405-406.5 nm data)",
        ),
    }
    for tag, (centres, values, note) in outputs.items():
        if values is None:
            values = _banded(wavelengths, core, centres)
        np.savetxt(
            folder / f"deborah2022_core_{tag}.csv",
            np.column_stack([centres, values]),
            delimiter=",",
            header=header + note,
            fmt="%.5f",
            comments="",
        )


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE)

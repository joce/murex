"""The spectra of the core pigments, taken out of the spectral data that
``docs/aquarelle/references/spectra/`` keeps in Git LFS, as ordinary text
that a test can read where the LFS files are not fetched (in CI)::

    python tools/aquarelle/extract_spectra.py            # both
    python tools/aquarelle/extract_spectra.py deborah    # one of them

- ``deborah``: H. Deborah, "Hyperspectral pigments", Zenodo 2022 (CC BY
  4.0), an ENVI spectral library of the median spectra of Kremer colour
  charts, each pigment at four thicknesses, 405 to 996 nm. Writes
  ``deborah2022_core_{raw,10nm,murex24}.csv``.
- ``cosentino``: A. Cosentino, "FORS spectral database of historical
  pigments in different binders", e-conservation Journal 2, 2014 (CC
  BY-NC 3.0: non-commercial), 54 pigments in gum arabic on watercolour
  paper, 360 to 1000 nm, read with a 45°/45° probe and with an integrating
  sphere. Writes ``cosentino2014_gumarabic_{probe,sphere}_core_{raw,10nm,
  murex24}.csv``; the raw files are in per cent, as the source is, the
  others reflectance factors.

``*_10nm.csv`` are means over bands 10 nm wide at 400 (410 for Deborah's,
which starts at 405) to 700 nm; ``*_murex24.csv`` means over murex's 24
bands, as wide as their spacing (Deborah's first, at 400 nm, holds only 405
to 406.5 nm). See ``docs/aquarelle/references.md``, ``deborah2022`` and
``cosentino2014``.
"""

# cspell:ignore hostaperm pnumber speclib refletion ultramarin cobaltblu
# cspell:ignore phtaloblue phthalogre burntsien cadmiumre cadmiumye titaniumw
# cspell:ignore ivoryblac prussianbl Gumarabic cobaltblue phthaloblue phthalogreen
# cspell:ignore burntsienna cadmiumred cadmiumyellow titaniumwhite ivoryblack
# cspell:ignore vineblack prussianblue redochre

from __future__ import annotations

import csv
import io
import re
import sys
import zipfile
from pathlib import Path

import numpy as np

from murex import spectral as sp

HERE = Path(__file__).resolve().parents[2] / "docs/aquarelle/references/spectra"

#: Deborah's pigments taken out: a label, and the pigment's Kremer number.
DEBORAH = (
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

#: Cosentino's pigments taken out: a label, and the pigment's column in the
#: probe's file and in the sphere's (whose names are cut short).
COSENTINO = (
    ("ultramarine_PB29", "ultramarine", "ultramarin"),
    ("cobalt_blue_PB28", "cobaltblue", "cobaltblu"),
    ("phthalo_blue_PB15", "phthaloblue", "phtaloblue"),
    ("phthalo_green_PG7", "phthalogreen", "phthalogre"),
    ("viridian_PG18", "viridian", "viridian"),
    ("alizarin_PR83", "alizarin", "alizarin"),
    ("burnt_sienna_PBr7", "burntsienna", "burntsien"),
    ("cadmium_red_PR108", "cadmiumred", "cadmiumre"),
    ("cadmium_yellow_PY35", "cadmiumyellow", "cadmiumye"),
    ("titanium_white_PW6", "titaniumwhite", "titaniumw"),
    ("lamp_black_PBk6", "lampblack", "lampblack"),
    ("ivory_black_PBk9", "ivoryblack", "ivoryblac"),
    ("vine_black_PBk8", "vineblack", "vineblack"),
    ("prussian_blue_PB27", "prussianblue", "prussianbl"),
    ("red_ochre_PR101", "redochre", "redochre"),
)
#: What the sphere's file has besides: the bare card and the gum alone.
COSENTINO_SPHERE_MORE = (
    ("substrate_cardboard", "cardboard"),
    ("gum_arabic_alone", "Gumarabic"),
)
COSENTINO_FILES = {
    "probe": "CSV/gum arabic refletion probe.csv",
    "sphere": "CSV/gum Arabic.csv",
}


def _banded(wavelengths, values, centres):
    """Means of ``values`` over bands around ``centres``, as wide as their
    spacing."""
    half = (centres[1] - centres[0]) / 2
    return np.array(
        [
            values[(wavelengths >= c - half) & (wavelengths < c + half)].mean(axis=0)
            for c in centres
        ]
    )


def _write(path: Path, wavelengths, values, labels, note: str, fmt: str) -> None:
    np.savetxt(
        path,
        np.column_stack([wavelengths, values]),
        delimiter=",",
        header="wavelength_nm," + ",".join(labels) + note,
        fmt=fmt,
        comments="",
    )


def _field(header: str, name: str) -> str:
    found = re.search(r"\n" + name + r" = \{(.*?)\}\s*\n", header, re.DOTALL)
    if found is None:
        raise ValueError(f"the library's header has no {name!r}")
    return found.group(1)


def deborah(folder: Path = HERE) -> None:
    """Deborah's core pigments: of each, the four thicknesses of its first
    patch."""
    header = (folder / "deborah2022_speclib_medians.hdr").read_text()
    names = [s.strip() for s in _field(header, "spectra names").split(",")]
    numbers = [s.strip() for s in _field(header, "pnumber").split(",")]
    wavelengths = np.array([float(x) for x in _field(header, "wavelength").split(",")])
    data = np.fromfile(folder / "deborah2022_speclib_medians.sli", dtype="<f4")
    spectra = data.reshape(len(names), len(wavelengths))
    columns, labels = [], []
    for label, number in DEBORAH:
        rows = [i for i, n in enumerate(numbers) if n == number]
        if not rows:
            raise ValueError(f"no pigment {number} in the library")
        patch = names[rows[0]].rsplit("_sh", 1)[0]
        for i in rows:
            if names[i].startswith(patch + "_sh"):
                columns.append(spectra[i])
                labels.append(f"{label}_{names[i].rsplit('_', 1)[1]}")
    core = np.column_stack(columns)
    first = folder / "deborah2022_core"
    _write(Path(f"{first}_raw.csv"), wavelengths, core, labels, "", "%.5f")
    for tag, centres, note in (
        ("10nm", np.arange(410.0, 701.0, 10.0), "  (box mean)"),
        (
            "murex24",
            sp.WAVELENGTHS,
            "  (box mean; murex24 first band 400 nm has only 405-406.5 nm data)",
        ),
    ):
        banded = _banded(wavelengths, core, centres)
        _write(Path(f"{first}_{tag}.csv"), centres, banded, labels, note, "%.5f")


def _cosentino_table(archive: zipfile.ZipFile, name: str):
    """The wavelengths of one of Cosentino's files, and its columns by name."""
    with archive.open(name) as raw:
        rows = [r for r in csv.reader(io.TextIOWrapper(raw, "latin-1")) if any(r)]
    header, body = rows[0], rows[1:]
    values = np.array([[float(x) for x in r[: len(header)]] for r in body])
    return values[:, 0], {n: values[:, i] for i, n in enumerate(header) if i}


def cosentino(folder: Path = HERE) -> None:
    """Cosentino's core pigments in gum arabic, by the probe and the sphere."""
    archive = zipfile.ZipFile(folder / "cosentino2014_FORS-database-CSV.zip")
    for kind, name in COSENTINO_FILES.items():
        wavelengths, columns = _cosentino_table(archive, name)
        picked = [
            (label, sphere if kind == "sphere" else probe)
            for label, probe, sphere in COSENTINO
        ]
        if kind == "sphere":
            picked += list(COSENTINO_SPHERE_MORE)
        labels = [label for label, _ in picked]
        core = np.column_stack([columns[column] for _, column in picked])
        first = folder / f"cosentino2014_gumarabic_{kind}_core"
        note = "  (reflectance in %, raw CCD samples)"
        _write(Path(f"{first}_raw.csv"), wavelengths, core, labels, note, "%.4f")
        note = "  (reflectance factor 0..1, box mean over band)"
        for tag, centres in (
            ("10nm", np.arange(400.0, 701.0, 10.0)),
            ("murex24", sp.WAVELENGTHS),
        ):
            banded = _banded(wavelengths, core / 100.0, centres)
            _write(Path(f"{first}_{tag}.csv"), centres, banded, labels, note, "%.5f")


SOURCES = {"deborah": deborah, "cosentino": cosentino}


def main(argv: list[str]) -> None:
    names = argv or list(SOURCES)
    for name in names:
        if name not in SOURCES:
            raise SystemExit(f"unknown source {name!r}: use one of {list(SOURCES)}")
        SOURCES[name]()


if __name__ == "__main__":
    main(sys.argv[1:])

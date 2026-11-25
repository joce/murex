"""Measure how a knife's white breaks over a dark: the holes, the islands, their grain.

    python tools/huile/break_stats.py PICTURE --box 100,80,300,240
    python tools/huile/break_stats.py PICTURE --poly 10,10 200,40 180,220
    python tools/huile/break_stats.py PICTURE --box ... --px-per-mm 2.4
    python tools/huile/break_stats.py PICTURE --box ... --pull 36 --thread 4
    python tools/huile/break_stats.py PICTURE --box ... --at 2 --overlay crop.png
    python tools/huile/break_stats.py LAID.npy --box ...     # an array, not a picture

For murex-dnj (a skimming knife breaks in patches): the same measures on a
photograph of a painting and on what huile lays, so that a target and today's
figure sit side by side. ``PICTURE`` is an image (or a ``.npy`` array, such as
the thickness a pull laid); the face to measure is a box or a polygon, in the
picture's pixels. Needs Pillow for pictures (``uv sync --group dev``).

What is measured, the crop turned so that the pull runs along its rows:

* the white is told from the dark on how white a pixel is (the least of its
  red, green and blue: white paint raises all three, a blue shadow one), cut
  between the means of the two classes (``two_means``); every number is given
  at three cuts, 35%, 50% and 65% of the way from the dark mean to the white
  one, and what moves much between them is not a measure of the paint. Where
  the two classes explain little of the variance, or their means are close,
  the crop is all white or all dark and the cut tells shades of one paint
  apart, not white from dark: ``--levels`` then gives the two means, as
  measured where the picture has plain dark and plain white;
* ``pull``: the direction the paint was pulled in, from the structure tensor
  (degrees under the horizontal, towards the right), unless ``--pull`` gives
  it, and how far the picture's edges agree on it (0 to 1);
* ``cover``: the share of the face that is white;
* holes (dark, joined by their sides) and islands (white, likewise), those
  the edge of the face does not cut short: how many, the diameter of the
  disc of the same area at the quartiles, the 90th centile and the largest,
  and ``in``: the diameter such that half their area lies in holes (islands)
  at least that large, which does not move when single pixels come and go as
  the count's quartiles do; then ``cut``, the share of all the dark (the
  white) that lies in pieces the edge cuts, and ``top``, the share in the
  largest piece. White that is one sheet with holes in it has nearly all its
  white in one island and its dark in many holes; a speckle the reverse;
* ``stretch``: how much longer than wide a hole of 12 px or more is, along
  the pull against across it (from its second moments, the median by area),
  ``longer`` its longer axis against its shorter whichever way it lies, and
  ``aligned`` the mean of cos 2a over those holes, a the angle of the longer
  axis to the pull (1: all along it, 0: any way, -1: all across);
* ``ragged``: the outline of a hole against the circle of its area (1: a
  disc), the median over holes of 30 px or more, and ``dim``, twice the slope
  of log outline against log area over them (1: smooth outlines whatever the
  size, towards 2: the larger the more ragged);
* ``chord``: the length of the run of white (of dark) a white (dark) pixel
  taken at random lies on, along the pull and across it. Solid islands have
  long chords both ways, threads of speckle short ones both ways, streaks
  long ones along and short ones across;
* ``solid``: the share of the white (of the dark) that a disc of 1, 2 and
  4 mm can reach without leaving it (a morphological opening);
* ``corr``: how far along and across the pull the white stays correlated
  with itself (to 1/e), and ``lattice``: the highest peak of that correlation
  away from its centre, which a weave's regular speckle raises and patches
  laid by hand do not.

Lengths are in millimetres where ``--px-per-mm`` gives the scale (otherwise
in pixels), and in threads too where ``--thread`` gives the weave's period in
pixels. ``--at`` measures the crop resampled to that many pixels a
millimetre, to compare two pictures at one resolution.
"""

from __future__ import annotations

import argparse

import numpy as np

SHAPE_MIN = 12  # px: holes smaller than this have no shape to speak of
RAGGED_MIN = 30  # px: nor an outline, under this
CUTS = (0.35, 0.5, 0.65)
DISCS_MM = (1.0, 2.0, 4.0)


def load(path: str, channel: str = "white") -> np.ndarray:
    """The picture at ``path`` as one value a pixel, 0 to 1: how white it is
    (``white``: the least of red, green and blue) or its ``luma``. An array
    (``.npy``) is scaled so that its 99.5th centile is 1."""
    if path.endswith(".npy"):
        values = np.load(path).astype(float)
        return np.clip(values / max(np.percentile(values, 99.5), 1e-12), 0.0, 1.0)
    from PIL import Image

    rgb = np.asarray(Image.open(path).convert("RGB"), float) / 255.0
    if channel == "luma":
        return rgb @ np.array([0.2126, 0.7152, 0.0722])
    return rgb.min(axis=2)


def inside(poly: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Whether each point (x, y) lies in the polygon (even-odd)."""
    hit = np.zeros(x.shape, bool)
    for (x0, y0), (x1, y1) in zip(poly, np.roll(poly, -1, axis=0), strict=True):
        if y0 == y1:
            continue
        between = (y0 <= y) != (y1 <= y)
        hit ^= between & (x < x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    return hit


def sample(grey: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """``grey`` at the points (x, y), between its pixels' centres."""
    h, w = grey.shape
    x, y = np.clip(x, 0, w - 1.001), np.clip(y, 0, h - 1.001)
    i, j = np.floor(y).astype(int), np.floor(x).astype(int)
    fy, fx = y - i, x - j
    top = grey[i, j] * (1 - fx) + grey[i, j + 1] * fx
    low = grey[i + 1, j] * (1 - fx) + grey[i + 1, j + 1] * fx
    return top * (1 - fy) + low * fy


def box_blur(grey: np.ndarray, n: int) -> np.ndarray:
    """``grey`` averaged over ``n`` by ``n`` pixels."""
    if n <= 1:
        return grey
    kernel = np.ones(n) / n
    for axis in (0, 1):
        grey = np.apply_along_axis(np.convolve, axis, grey, kernel, "same")
    return grey


def pull_direction(grey: np.ndarray, poly: np.ndarray) -> tuple[float, float]:
    """The way the paint was pulled over the polygon (degrees under the
    horizontal, towards the right, -90 to 90) and how far the edges agree on
    it (0 to 1): the direction the picture changes least along."""
    x0, y0 = np.floor(poly.min(axis=0)).astype(int)
    x1, y1 = np.ceil(poly.max(axis=0)).astype(int) + 1
    part = box_blur(grey[max(y0, 0) : y1, max(x0, 0) : x1], 3)
    gy, gx = np.gradient(part)
    ys, xs = np.mgrid[0 : part.shape[0], 0 : part.shape[1]]
    keep = inside(poly, xs + max(x0, 0) + 0.5, ys + max(y0, 0) + 0.5)
    jxx, jyy, jxy = (
        float((a * b)[keep].sum()) for a, b in ((gx, gx), (gy, gy), (gx, gy))
    )
    steepest = 0.5 * np.degrees(np.arctan2(2 * jxy, jxx - jyy))
    agree = np.hypot(jxx - jyy, 2 * jxy) / max(jxx + jyy, 1e-12)
    return float((steepest + 180.0) % 180.0 - 90.0), float(agree)


def straighten(
    grey: np.ndarray, poly: np.ndarray, pull: float, zoom: float = 1.0
) -> tuple[np.ndarray, np.ndarray]:
    """The polygon of ``grey`` turned so that the pull runs along the rows,
    ``zoom`` pixels for each of the picture's, and which pixels of that are
    inside the polygon."""
    if zoom < 1.0:
        grey = box_blur(grey, int(round(1.0 / zoom)))
    a = np.radians(pull)
    along, across = np.array([np.cos(a), np.sin(a)]), np.array([-np.sin(a), np.cos(a)])
    u, v = poly @ along, poly @ across
    us = np.arange(u.min(), u.max(), 1.0 / zoom)
    vs = np.arange(v.min(), v.max(), 1.0 / zoom)
    uu, vv = np.meshgrid(us, vs)
    x = uu * along[0] + vv * across[0]
    y = uu * along[1] + vv * across[1]
    h, w = grey.shape
    valid = inside(poly, x, y) & (x >= 0.5) & (y >= 0.5) & (x < w - 0.5) & (y < h - 0.5)
    return sample(grey, x - 0.5, y - 0.5), valid


def two_means(values: np.ndarray) -> tuple[float, float, float]:
    """The means of the two classes ``values`` fall into when cut midway
    between those means, and the share of their variance that the two
    classes explain (near 1: two clear classes)."""
    cut = float(values.mean())
    for _ in range(100):
        low, high = values[values <= cut], values[values > cut]
        if not len(low) or not len(high):
            break
        new = 0.5 * (float(low.mean()) + float(high.mean()))
        if abs(new - cut) < 1e-6:
            break
        cut = new
    low, high = values[values <= cut], values[values > cut]
    if not len(low) or not len(high):
        return cut, cut, 0.0
    share = len(high) / len(values)
    between = share * (1 - share) * (float(high.mean()) - float(low.mean())) ** 2
    return (
        float(low.mean()),
        float(high.mean()),
        between / max(float(values.var()), 1e-12),
    )


def _find(parent: list[int], i: int) -> int:
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def label(mask: np.ndarray) -> tuple[np.ndarray, int]:
    """The pieces of ``mask`` joined by their sides, numbered from 1 (0:
    outside the mask), and how many there are."""
    h, w = mask.shape
    padded = np.zeros((h, w + 2), bool)
    padded[:, 1:-1] = mask
    edges = np.diff(padded.astype(np.int8), axis=1)
    rows, starts = np.nonzero(edges == 1)
    ends = np.nonzero(edges == -1)[1]
    parent = list(range(len(rows)))
    first = np.searchsorted(rows, np.arange(h + 1))
    for r in range(1, h):
        i, j = int(first[r - 1]), int(first[r])
        i_end, j_end = j, int(first[r + 1])
        while i < i_end and j < j_end:
            if starts[i] < ends[j] and starts[j] < ends[i]:
                parent[_find(parent, i)] = _find(parent, j)
            if ends[i] < ends[j]:
                i += 1
            else:
                j += 1
    roots = np.array([_find(parent, i) for i in range(len(rows))], int)
    names = np.unique(roots, return_inverse=True)[1] + 1 if len(roots) else roots
    out = np.zeros((h, w), np.int32)
    for r, s, e, n in zip(rows, starts, ends, names, strict=True):
        out[r, s:e] = n
    return out, int(names.max()) if len(names) else 0


def pieces(mask: np.ndarray, valid: np.ndarray) -> dict[str, np.ndarray]:
    """For each piece of ``mask``: its area (px), the variances of its pixels
    along and across the rows and their covariance, the length of its outline
    (px, less the stair-steps: times pi/4) and whether it touches the edge of
    ``valid`` (it is then cut short)."""
    names, n = label(mask)
    flat = names.ravel()
    ys, xs = np.mgrid[0 : mask.shape[0], 0 : mask.shape[1]]

    def total(weights) -> np.ndarray:
        return np.bincount(flat, np.asarray(weights, float).ravel(), n + 1)[1:]

    area = total(np.ones(mask.shape))
    mx, my = total(xs) / area, total(ys) / area
    outline, cut = np.zeros(n), np.zeros(n)
    wide, ok = np.pad(mask, 1), np.pad(valid, 1)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        there = (
            slice(1 + dy, mask.shape[0] + 1 + dy),
            slice(1 + dx, mask.shape[1] + 1 + dx),
        )
        outline += total(mask & ~wide[there])
        cut += total(mask & ~ok[there])
    return {
        "area": area,
        "along": total(xs * xs) / area - mx * mx + 1 / 12,
        "across": total(ys * ys) / area - my * my + 1 / 12,
        "both": total(xs * ys) / area - mx * my,
        "outline": outline * np.pi / 4,
        "cut": cut > 0,
        "names": names,
    }


def by_weight(values: np.ndarray, weights: np.ndarray, q: float = 0.5) -> float:
    """The ``q`` quantile of ``values``, each counted ``weights`` times."""
    if not len(values):
        return float("nan")
    order = np.argsort(values)
    cum = np.cumsum(weights[order])
    return float(values[order][np.searchsorted(cum, q * cum[-1])])


def sizes(p: dict[str, np.ndarray], px: float) -> dict[str, float]:
    """How large the whole pieces are: their number, the diameter of the
    disc of the same area (in units of ``px`` pixels) at the quartiles, the
    90th centile and the largest, and such that half their area lies in
    pieces at least that large; then, of all the pieces, the share of the
    area in those the edge cuts short and in the largest."""
    area = p["area"][~p["cut"]]
    names = ("n", "q1", "median", "q3", "p90", "max", "in")
    out: dict[str, float] = dict.fromkeys(names, 0.0)
    if len(area):
        d = 2.0 * np.sqrt(area / np.pi) / px
        values = [len(d), *np.percentile(d, (25, 50, 75, 90)), d.max()]
        values.append(by_weight(d, area))
        out = {k: float(v) for k, v in zip(names, values, strict=True)}
    everything = max(float(p["area"].sum()), 1.0)
    out["cut"] = float(p["area"][p["cut"]].sum()) / everything
    out["top"] = float(p["area"].max()) / everything if len(p["area"]) else 0.0
    return out


def shapes(p: dict[str, np.ndarray]) -> dict[str, float]:
    """How the whole pieces of 12 px and more are shaped (see the module's
    text: stretch, longer, aligned, ragged, dim) and how many they are."""
    whole = ~p["cut"] & (p["area"] >= SHAPE_MIN)
    area, xx, yy, xy = (p[k][whole] for k in ("area", "along", "across", "both"))
    spread = np.hypot(xx - yy, 2 * xy)
    longer, shorter = 0.5 * (xx + yy + spread), 0.5 * (xx + yy - spread)
    angle = 0.5 * np.arctan2(2 * xy, xx - yy)
    big = ~p["cut"] & (p["area"] >= RAGGED_MIN)
    a, o = p["area"][big], p["outline"][big]
    dim = 2 * np.polyfit(np.log(a), np.log(o), 1)[0] if len(a) >= 8 else float("nan")
    return {
        "shaped": float(whole.sum()),
        "stretch": by_weight(np.sqrt(xx / yy), area),
        "longer": by_weight(np.sqrt(longer / np.maximum(shorter, 1 / 12)), area),
        "aligned": (
            float(np.average(np.cos(2 * angle), weights=area)) if len(area) else 0.0
        ),
        "ragged": (
            float(np.median(o / (2 * np.sqrt(np.pi * a)))) if len(a) else float("nan")
        ),
        "dim": float(dim),
    }


def chord(mask: np.ndarray, valid: np.ndarray, px: float) -> float:
    """The length of the run of ``mask`` along the rows that a pixel of it
    taken at random lies on (in units of ``px`` pixels)."""
    on = np.zeros((mask.shape[0], mask.shape[1] + 2), np.int8)
    on[:, 1:-1] = mask & valid
    edges = np.diff(on, axis=1)
    runs = (np.nonzero(edges == -1)[1] - np.nonzero(edges == 1)[1]).astype(float)
    return float((runs * runs).sum() / max(runs.sum(), 1.0)) / px


def reached(mask: np.ndarray, valid: np.ndarray, d: int) -> float:
    """The share of ``mask`` that a disc ``d`` pixels across can reach
    without leaving it (what lies outside ``valid`` does not stop it)."""
    r = d // 2
    offsets = [
        (dy, dx)
        for dy in range(-r, r + 1)
        for dx in range(-r, r + 1)
        if dy * dy + dx * dx <= (d / 2) ** 2
    ]
    h, w = mask.shape
    fits = np.ones((h, w), bool)
    wide = np.pad(mask | ~valid, r, constant_values=True)
    for dy, dx in offsets:
        fits &= wide[r + dy : r + dy + h, r + dx : r + dx + w]
    swept = np.zeros((h, w), bool)
    wide = np.pad(fits, r)
    for dy, dx in offsets:
        swept |= wide[r + dy : r + dy + h, r + dx : r + dx + w]
    return float((swept & mask & valid).sum() / max((mask & valid).sum(), 1))


def correlation(mask: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """How far ``mask`` is correlated with itself moved by each lag (rows,
    columns; lag 0 at the centre), over the pixels ``valid`` both ways."""
    h, w = mask.shape
    shape = (2 * h, 2 * w)
    values = np.where(valid, mask - mask[valid].mean(), 0.0)

    def with_itself(a: np.ndarray) -> np.ndarray:
        f = np.fft.rfft2(a, shape)
        return np.fft.fftshift(np.fft.irfft2(f * np.conj(f), shape))

    pairs = with_itself(valid.astype(float))
    enough = pairs > 0.25 * valid.sum()
    out = np.where(enough, with_itself(values) / np.maximum(pairs, 1.0), 0.0)
    return out / out[h, w]


def falls_to(profile: np.ndarray, level: float = np.exp(-1.0)) -> float:
    """The lag at which ``profile`` (from lag 0) first falls to ``level``."""
    under = np.nonzero(profile < level)[0]
    if not len(under):
        return float(len(profile))
    k = int(under[0])
    return k - 1 + (profile[k - 1] - level) / (profile[k - 1] - profile[k])


def lattice(corr: np.ndarray, reach: int) -> tuple[float, float]:
    """The highest peak of the correlation ``corr`` away from its centre,
    within ``reach`` pixels (a lag where it is higher than at all 24 lags
    around it), and how far from the centre it is (px)."""
    cy, cx = corr.shape[0] // 2, corr.shape[1] // 2
    reach = min(reach, cy - 3, cx - 3)
    part = corr[cy - reach - 2 : cy + reach + 3, cx - reach - 2 : cx + reach + 3]
    inner = part[2:-2, 2:-2]
    peak = np.ones(inner.shape, bool)
    n = inner.shape[0]
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            if dy or dx:
                peak &= inner > part[2 + dy : 2 + dy + n, 2 + dx : 2 + dx + n]
    ys, xs = np.mgrid[-reach : reach + 1, -reach : reach + 1]
    far = np.hypot(ys, xs)
    peak &= (far >= 2.5) & (far <= reach)
    if not peak.any():
        return 0.0, 0.0
    best = int(np.argmax(np.where(peak, inner, -np.inf)))
    return float(inner.ravel()[best]), float(far.ravel()[best])


def measure(
    grey: np.ndarray, valid: np.ndarray, cut: float, px_per_mm: float
) -> dict[str, float]:
    """Every measure of the straightened crop ``grey`` (the pull along its
    rows) with the white taken as what is above ``cut``, lengths in mm."""
    white, dark = (grey > cut) & valid, (grey <= cut) & valid
    out = {"cover": float(white.sum() / valid.sum())}
    holes, islands = pieces(dark, valid), pieces(white, valid)
    out.update({f"hole_{k}": v for k, v in sizes(holes, px_per_mm).items()})
    out.update({f"isle_{k}": v for k, v in sizes(islands, px_per_mm).items()})
    out.update(shapes(holes))
    for name, mask in (("white", white), ("dark", dark)):
        out[f"{name}_along"] = chord(mask, valid, px_per_mm)
        out[f"{name}_across"] = chord(mask.T, valid.T, px_per_mm)
        for mm in DISCS_MM:
            d = max(3, int(round(mm * px_per_mm)) | 1)
            out[f"{name}_solid{mm:g}"] = reached(mask, valid, d)
    corr = correlation(white.astype(float), valid)
    cy, cx = corr.shape[0] // 2, corr.shape[1] // 2
    out["corr_along"] = falls_to(corr[cy, cx:]) / px_per_mm
    out["corr_across"] = falls_to(corr[cy:, cx]) / px_per_mm
    peak, far = lattice(corr, int(round(12 * px_per_mm)))
    out["lattice"], out["lattice_at"] = peak, far / px_per_mm
    return out


def analyse(
    grey: np.ndarray,
    poly: np.ndarray,
    px_per_mm: float = 1.0,
    pull: float | None = None,
    at: float | None = None,
    levels: tuple[float, float] | None = None,
) -> dict:
    """The measures of the polygon ``poly`` of the picture ``grey`` at each
    cut of ``CUTS``, with the pull, the two classes' means, the scale they
    were taken at and the straightened crop. ``levels`` gives the dark and
    the white where they are known, rather than taken from the crop."""
    found, agree = pull_direction(grey, poly)
    zoom = 1.0 if at is None else at / px_per_mm
    crop, valid = straighten(grey, poly, found if pull is None else pull, zoom)
    low, high, explained = two_means(crop[valid])
    if levels is not None:
        low, high = levels
    scale = px_per_mm * zoom
    return {
        "pull": found if pull is None else pull,
        "pull_found": found,
        "agree": agree,
        "low": low,
        "high": high,
        "explained": explained,
        "px_per_mm": scale,
        "crop": crop,
        "valid": valid,
        "cuts": {f: measure(crop, valid, low + f * (high - low), scale) for f in CUTS},
    }


ROWS = (
    ("cover", "share of the face that is white", ("cover",)),
    ("holes", "n; q1 / median / q3 / p90 / max; in; cut, top", None),
    ("islands", "n; q1 / median / q3 / p90 / max; in; cut, top", None),
    ("shape", "stretch, longer, aligned (holes >= 12 px, n)", None),
    ("ragged", "outline against a disc's, and dim", ("ragged", "dim")),
    ("chord white", "along, across", ("white_along", "white_across")),
    ("chord dark", "along, across", ("dark_along", "dark_across")),
    ("solid white", "reached by a disc of 1, 2, 4 mm", None),
    ("solid dark", "reached by a disc of 1, 2, 4 mm", None),
    ("corr", "along, across; lattice peak, at", None),
)


def _cell(name: str, m: dict[str, float]) -> str:
    if name in ("holes", "islands"):
        k = "hole" if name == "holes" else "isle"
        text = f"{m[k + '_n']:.0f}; " + " / ".join(
            f"{m[f'{k}_{q}']:.2f}" for q in ("q1", "median", "q3", "p90", "max")
        )
        return text + f"; {m[k + '_in']:.2f}; {m[k + '_cut']:.2f}, {m[k + '_top']:.2f}"
    if name == "shape":
        return (
            f"{m['stretch']:.2f}, {m['longer']:.2f}, {m['aligned']:+.2f} "
            f"({m['shaped']:.0f})"
        )
    if name.startswith("solid"):
        k = name.split()[1]
        return ", ".join(f"{m[f'{k}_solid{mm:g}']:.2f}" for mm in DISCS_MM)
    return (
        f"{m['corr_along']:.2f}, {m['corr_across']:.2f}; "
        f"{m['lattice']:.2f}, {m['lattice_at']:.1f}"
    )


def report(result: dict, unit: str, thread_mm: float | None = None) -> None:
    """Print the measures of ``analyse``, a column for each cut."""
    print(
        f"pull {result['pull']:.0f} deg under the horizontal (the edges say "
        f"{result['pull_found']:.0f}, agreeing {result['agree']:.2f}); dark "
        f"{result['low']:.2f}, white {result['high']:.2f}, the two classes "
        f"explain {result['explained']:.2f} of the variance; "
        f"{int(result['valid'].sum())} px at {result['px_per_mm']:.2f} px/{unit}"
    )
    if thread_mm:
        print(f"a thread is {thread_mm:.2f} {unit}")
    print(f"lengths in {unit}; the cut at " + ", ".join(f"{f:.0%}" for f in CUTS))
    for name, what, keys in ROWS:
        cells = [
            ", ".join(f"{m[k]:.2f}" for k in keys) if keys else _cell(name, m)
            for m in result["cuts"].values()
        ]
        print(f"{name:>12}  " + "  |  ".join(cells) + f"   ({what})")


def overlay(result: dict, path: str, cut: float = 0.5, enlarge: int = 3) -> None:
    """Write to ``path`` the straightened crop, its white and dark, and the
    crop with its holes outlined (in red), side by side."""
    from PIL import Image

    crop, valid = result["crop"], result["valid"]
    white = (crop > result["low"] + cut * (result["high"] - result["low"])) & valid
    dark = ~white & valid
    edge = np.zeros(dark.shape, bool)
    wide = np.pad(dark, 1)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        edge |= ~wide[1 + dy : dark.shape[0] + 1 + dy, 1 + dx : dark.shape[1] + 1 + dx]
    edge &= dark
    plain = np.repeat(np.where(valid, crop, 0.5)[:, :, None], 3, axis=2)
    cut_out = np.repeat(np.where(valid, white, 0.5)[:, :, None], 3, axis=2)
    outlined = plain.copy()
    outlined[edge] = (1.0, 0.1, 0.1)
    gap = np.full((crop.shape[0], 4, 3), 0.5)
    panels = np.concatenate([plain, gap, cut_out, gap, outlined], axis=1)
    image = Image.fromarray((panels * 255).round().astype(np.uint8))
    size = (image.width * enlarge, image.height * enlarge)
    image.resize(size, Image.Resampling.NEAREST).save(path)


def main() -> None:
    parser = argparse.ArgumentParser(description=(__doc__ or "").split("\n")[0])
    parser.add_argument("picture", help="an image, or a .npy array")
    parser.add_argument("--box", metavar="X0,Y0,X1,Y1", help="the face, as a box")
    parser.add_argument(
        "--poly", nargs="+", metavar="X,Y", help="the face, as a polygon's corners"
    )
    parser.add_argument(
        "--px-per-mm", type=float, help="the picture's scale (lengths are then in mm)"
    )
    parser.add_argument(
        "--pull", type=float, help="the pull, degrees under the horizontal (else found)"
    )
    parser.add_argument("--thread", type=float, help="the weave's period (px)")
    parser.add_argument("--at", type=float, help="resample to this many px/mm first")
    parser.add_argument("--channel", choices=("white", "luma"), default="white")
    parser.add_argument(
        "--levels",
        metavar="DARK,WHITE",
        help="how white the dark and the white are (0 to 1), where known",
    )
    parser.add_argument("--overlay", metavar="PNG", help="write the crop and its holes")
    args = parser.parse_args()
    grey = load(args.picture, args.channel)
    if args.poly:
        poly = np.array([[float(v) for v in p.split(",")] for p in args.poly])
    elif args.box:
        x0, y0, x1, y1 = (float(v) for v in args.box.split(","))
        poly = np.array([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])
    else:
        h, w = grey.shape
        poly = np.array([(0, 0), (w, 0), (w, h), (0, h)], float)
    scale = args.px_per_mm or 1.0
    at = args.at if args.px_per_mm else None
    levels = None
    if args.levels:
        dark, white = (float(v) for v in args.levels.split(","))
        levels = (dark, white)
    result = analyse(grey, poly, scale, args.pull, at, levels)
    thread = args.thread / scale if args.thread else None
    report(result, "mm" if args.px_per_mm else "px", thread)
    if args.overlay:
        overlay(result, args.overlay)


if __name__ == "__main__":
    main()

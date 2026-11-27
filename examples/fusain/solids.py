"""Solids seen from in front of a sheet, for the examples that build their
subject before they draw it (``toilette_model.py``, ``fox_model.py``).

A :class:`Solids` works on every pixel of a sheet at once. Each solid gives,
at each pixel, how far its surface facing the viewer stands out (z towards
the viewer; ``NONE`` where it is not): ellipsoids, tapered rods, limbs along
a path whose thickness swells and narrows, bodies of rounded sections
stacked down the sheet (lofts). Several melt into one surface by a smooth
maximum of their depths; on a surface lie ridges, grooves and bumps.
:meth:`Solids.stack` lays the parts over each other, the nearest in front,
and :meth:`Solids.cast` traces the shadows they cast on each other.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from murex.filters import box_blur

#: The depth of a pixel no solid covers.
NONE = -1e9


@dataclass(frozen=True)
class Limb:
    """A limb along ``points``, ``radii`` thick and its axis ``zs`` out,
    both given at even places from its first point to its last."""

    points: tuple
    radii: tuple
    zs: tuple


def smooth_line(values, n=256):
    """``n`` values through ``values`` (at even places from 0 to 1),
    smoothed so that they bend without kinks."""
    fine = np.linspace(0.0, 1.0, n)
    line = np.interp(fine, np.linspace(0.0, 1.0, len(values)), values)
    for _ in range(2):
        line = np.convolve(np.pad(line, 12, mode="edge"), np.ones(25) / 25, "valid")
    return line


def melt(depths, k):
    """The smooth maximum of several depths: one surface over them all,
    rounded by about ``k`` where they meet."""
    out = depths[0]
    for d in depths[1:]:
        both = (out > NONE / 2) & (d > NONE / 2)
        h = np.clip(0.5 + 0.5 * (d - out) / k, 0.0, 1.0)
        mixed = out + (d - out) * h + k * h * (1.0 - h)
        out = np.where(both, mixed, np.maximum(out, d))
    return out


def normals(z):
    """Which way a surface faces at each pixel, (3, rows, columns)."""
    gy, gx = np.gradient(box_blur(z, 1))
    n = np.stack([-gx, -gy, np.ones_like(z)])
    return n / np.linalg.norm(n, axis=0)


def limb_side(limb: Limb, side: int, n=48):
    """One side of a limb, from its first point to its last: ``side`` 1 on
    the left of the way it runs, -1 on its right."""
    points = np.asarray(limb.points, float)
    total = np.r_[0.0, np.cumsum(np.hypot(*np.diff(points, axis=0).T))]
    t = np.linspace(0.0, total[-1], n)
    x, y = np.interp(t, total, points[:, 0]), np.interp(t, total, points[:, 1])
    dx, dy = np.gradient(x), np.gradient(y)
    norm = np.hypot(dx, dy)
    r = np.interp(t / total[-1], np.linspace(0, 1, 256), smooth_line(limb.radii))
    return np.stack([x + side * r * dy / norm, y - side * r * dx / norm], axis=1)


def ellipse_arc(centre, radii, turn, start, end, n=60):
    """An arc of an ellipse, from ``start`` to ``end`` degrees round it."""
    a = np.radians(np.linspace(start, end, n))
    c, s = np.cos(np.radians(turn)), np.sin(np.radians(turn))
    u, v = radii[0] * np.cos(a), radii[1] * np.sin(a)
    return np.stack([centre[0] + u * c - v * s, centre[1] + u * s + v * c], axis=1)


class Solids:
    """Solids over a sheet ``width`` by ``height`` pixels, laid out in units
    of their own: drawn ``scale`` times as large about ``origin``."""

    def __init__(self, width: int, height: int, scale=1.0, origin=(0.0, 0.0)):
        self.width, self.height = width, height
        self.scale, self.origin = scale, np.asarray(origin, float)
        rows, cols = np.mgrid[0:height, 0:width].astype(np.float64)
        #: Where each pixel of the sheet is, in the solids' own units.
        self.px = self.origin[0] + (cols - self.origin[0]) / scale
        self.py = self.origin[1] + (rows - self.origin[1]) / scale

    def on_sheet(self, points):
        """Where ``points`` (in the solids' units) are on the sheet."""
        return self.origin + (np.asarray(points, float) - self.origin) * self.scale

    def at(self, field, points):
        """``field`` read at each of ``points`` of the sheet (the nearest
        pixel)."""
        points = np.asarray(points)
        col = np.clip(np.rint(points[:, 0]).astype(int), 0, self.width - 1)
        row = np.clip(np.rint(points[:, 1]).astype(int), 0, self.height - 1)
        return field[row, col]

    def ellipsoid(self, centre, radii, z=0.0, turn=0.0):
        """How far an ellipsoid's front stands out at each pixel. ``centre``
        is (x, y) on the sheet, ``radii`` (across, down, deep), ``z`` how
        far its middle stands out, ``turn`` its turn in the sheet's plane in
        degrees."""
        c, s = np.cos(np.radians(turn)), np.sin(np.radians(turn))
        dx, dy = self.px - centre[0], self.py - centre[1]
        u, v = (dx * c + dy * s) / radii[0], (-dx * s + dy * c) / radii[1]
        q = 1.0 - u * u - v * v
        return np.where(q > 0.0, z + radii[2] * np.sqrt(np.clip(q, 0.0, 1.0)), NONE)

    def capsule(self, a, b, ra, rb, za=0.0, zb=0.0):
        """A tapered rod from ``a`` to ``b`` (points on the sheet), ``ra``
        and ``rb`` thick at its ends, its axis ``za`` and ``zb`` out."""
        px, py = self.px, self.py
        a, b = np.asarray(a, float), np.asarray(b, float)
        ab = b - a
        t = np.clip(((px - a[0]) * ab[0] + (py - a[1]) * ab[1]) / (ab @ ab), 0.0, 1.0)
        d2 = (px - a[0] - t * ab[0]) ** 2 + (py - a[1] - t * ab[1]) ** 2
        r = ra + (rb - ra) * t
        q = r * r - d2
        z = za + (zb - za) * t + np.sqrt(np.clip(q, 0.0, None))
        return np.where(q > 0.0, z, NONE)

    def nearest(self, points):
        """For each pixel, the square of its distance to the polyline
        through ``points`` and how far along it (0 to 1) the nearest point
        lies."""
        px, py = self.px, self.py
        points = np.asarray(points, float)
        total = np.r_[0.0, np.cumsum(np.hypot(*np.diff(points, axis=0).T))]
        best = np.full(px.shape, np.inf)
        along = np.zeros(px.shape)
        for i in range(len(points) - 1):
            a, b = points[i], points[i + 1]
            ab = b - a
            t = np.clip(((px - a[0]) * ab[0] + (py - a[1]) * ab[1]) / (ab @ ab), 0, 1)
            d2 = (px - a[0] - t * ab[0]) ** 2 + (py - a[1] - t * ab[1]) ** 2
            closer = d2 < best
            best = np.where(closer, d2, best)
            along = np.where(closer, (total[i] + t * np.hypot(*ab)) / total[-1], along)
        return best, along

    def limb(self, limb: Limb):
        """How far a limb stands out at each pixel."""
        best, along = self.nearest(limb.points)
        fine = np.linspace(0.0, 1.0, 256)
        r = np.interp(along, fine, smooth_line(limb.radii))
        q = r * r - best
        z = np.interp(along, fine, smooth_line(limb.zs))
        return np.where(q > 0.0, z + np.sqrt(np.clip(q, 0, None)), NONE)

    def bump(self, x0, y0, sx, sy, turn=0.0):
        """A soft round bump of height 1 about (x0, y0), ``sx`` by ``sy``."""
        c, s = np.cos(np.radians(turn)), np.sin(np.radians(turn))
        dx, dy = self.px - x0, self.py - y0
        u, v = (dx * c + dy * s) / sx, (-dx * s + dy * c) / sy
        return np.exp(-(u * u + v * v))

    def ridge(self, points, width, heights):
        """A ridge (or with heights below 0, a groove) along a polyline, of
        gaussian section ``width`` wide, its height changing along it."""
        best, along = self.nearest(points)
        height = np.interp(along, np.linspace(0, 1, len(heights)), heights)
        return height * np.exp(-best / width**2)

    def profile(self, ys, values, soft=18):
        """A value at every row of the sheet, through ``values`` at the rows
        ``ys`` and smoothed over about ``soft`` rows."""
        rows = np.arange(self.height, dtype=np.float64)
        line = np.interp(rows, ys, values)
        for _ in range(3):
            line = box_blur(line[:, None], soft // 2)[:, 0]
        return line

    def loft(self, ys, half, deep, out, sway, flat=0.45):
        """A body of rounded sections stacked down the sheet: at each height
        y (``ys``) it is ``half`` wide either side of ``sway``, ``deep`` deep
        and stands ``out``. ``flat`` below 0.5 flattens the section."""
        px, py = self.px, self.py
        row = np.clip(py, 0, self.height - 1).astype(int)
        w = np.maximum(self.profile(ys, half)[row], 1.0)
        u = (px - self.profile(ys, sway)[row]) / w
        q = np.clip(1.0 - u * u, 0.0, 1.0)
        z = self.profile(ys, out)[row] + self.profile(ys, deep)[row] * q**flat
        there = (np.abs(u) < 1.0) & (py >= ys[0]) & (py <= ys[-1])
        return np.where(there, z, NONE)

    def loft_side(self, ys, half, sway, side: int, y0=None, y1=None, step=4.0):
        """One side of a lofted body, from row ``y0`` to ``y1``."""
        y = np.arange(y0 or ys[0], (y1 or ys[-1]) + 1, step, dtype=float)
        rows = y.astype(int).clip(0, self.height - 1)
        x = self.profile(ys, sway)[rows] + side * self.profile(ys, half)[rows]
        return np.stack([x, y], axis=1)

    def stack(self, layers, empty=0):
        """The parts laid over each other, the nearest in front: from
        ``layers`` of (depth, part), what part each pixel shows (``empty``
        where none), how far it stands out and which way it faces."""
        depth = np.full(self.px.shape, NONE)
        part = np.full(self.px.shape, empty)
        normal = np.zeros((3,) + self.px.shape)
        for z, which in layers:
            front = (z > NONE / 2) & (z > depth)
            depth = np.where(front, z, depth)
            part = np.where(front, which, part)
            n = normals(np.where(z > NONE / 2, z, 0.0))
            normal[:, front] = n[:, front]
        normal[2, part == empty] = 1.0
        return part, depth, normal

    def cast(self, z, light, reach=240):
        """How much of a lamp in the direction ``light`` reaches each pixel
        (1 lit, 0 in a cast shadow): a ray towards it, over the depths."""
        flat = np.hypot(light[0], light[1])
        dx, dy, rise = light[0] / flat, light[1] / flat, light[2] / flat
        lit = np.ones_like(z)
        for step in range(3, reach, 3):
            col = np.clip(np.rint(self.px + dx * step).astype(int), 0, self.width - 1)
            row = np.clip(np.rint(self.py + dy * step).astype(int), 0, self.height - 1)
            over = z[row, col] - (z + rise * step + 4.0)
            lit = np.minimum(lit, np.clip(1.0 - over / 10.0, 0.0, 1.0))
        return lit

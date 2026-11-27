"""The seated woman of ``toilette.py``, built as solids and lit.

Imported by ``toilette.py``, which lays the crayons over it: this module
gives, for every pixel of the sheet, which part of the figure is seen there
(skin, hair, the drape, the wall behind), how far it stands out towards the
viewer, which way it faces and what tone it takes; and the lines it is
built on (the outlines of the back, the arms, the head and the drape, the
furrow of the spine, the folds), for the contours.

The figure is seen from behind, sitting on a stool, both arms raised to
gather her hair on the top of her head. She is about four heads high from
the gathered hair to the stool (``HEAD`` px each), in the proportions of the
academic canon: the back two heads across under the raised arms, the waist
a head and a half, the upper arm a head and a third, the forearm a head and
a fifth.

Each part is a body of rounded sections (the torso, the drape), limbs along
a path whose thickness swells and narrows (the arms), and ellipsoids (the
head), seen from behind (z towards the viewer) and melted together by a
smooth maximum of their depths, so that the back and the arms are one
surface; the parts meet each other with a hard edge, as a forearm passes in
front of the head. On the back lies what the skeleton and the muscles raise
and hollow: the furrow of the spine between the long muscles beside it, the
shoulder blades turned up and out by the raised arms, the trapezius bunched
between them and the neck, the bump at the base of the neck, the two
dimples above the drape. The lamp is high on the left; the shadows each
part casts on the others are traced over the depths, and the hollows of
the surface take less of the light from all round.
"""

# cspell:words tensordot toilette trapezius

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from murex.filters import box_blur

WIDTH, HEIGHT = 900, 1200
HEAD = 150.0
#: Where the light comes from: high on the left, a little in front.
LIGHT = np.array([-0.62, -0.62, 0.48])
LIGHT = LIGHT / np.linalg.norm(LIGHT)

#: What each pixel shows.
WALL, SKIN, HAIR, DRAPE = 0, 1, 2, 3

#: The sheet's pixels: their columns and their rows.
py, px = np.mgrid[0:HEIGHT, 0:WIDTH].astype(np.float64)
_NONE = -1e9

# --- the pose ----------------------------------------------------------------

X0 = 450.0
#: Shoulders, elbows and wrists (her right is our left), and where the
#: hands hold the hair.
R_SHOULDER, L_SHOULDER = (X0 - 140, 410), (X0 + 142, 414)
R_ELBOW, L_ELBOW = (X0 - 238, 236), (X0 + 236, 222)
R_WRIST, L_WRIST = (X0 - 92, 186), (X0 + 92, 158)
HAIR_KNOT = (X0 - 2, 150)
DRAPE_Y = 838.0


@dataclass(frozen=True)
class Limb:
    """A limb along ``points``, ``radii`` thick and its axis ``zs`` out,
    both given at even places from its first point to its last."""

    points: tuple
    radii: tuple
    zs: tuple


_UPPER = ((46, 44, 40, 33, 27, 25), (16, 24, 28, 28, 28, 32))
_FORE = ((24, 27, 25, 21, 18, 17), (34, 50, 64, 78, 90, 96))
UPPER_ARMS = (
    Limb((R_SHOULDER, R_ELBOW), *_UPPER),
    Limb((L_SHOULDER, L_ELBOW), *_UPPER),
)
FOREARMS = (Limb((R_ELBOW, R_WRIST), *_FORE), Limb((L_ELBOW, L_WRIST), *_FORE))


def knuckles(side: int) -> tuple:
    """Where the knuckles of a hand are: her right hand (``side`` -1) holds
    the twist low, her left above it."""
    return (HAIR_KNOT[0] + side * 26, HAIR_KNOT[1] + (16 if side < 0 else -12))


#: The back of each hand, from the wrist to the knuckles: broad and flat.
HANDS = tuple(
    Limb((wrist, knuckles(side)), (18, 22, 25, 25), (96, 104, 110, 112))
    for wrist, side in ((R_WRIST, -1), (L_WRIST, 1))
)


def fingers(side: int):
    """Each finger of a hand, from its knuckle curling over the twist of
    hair, its tip going round behind it."""
    wrist = np.array(R_WRIST if side < 0 else L_WRIST, float)
    root = np.array(knuckles(side), float)
    way = (root - wrist) / np.hypot(*(root - wrist))
    across = np.array([-way[1], way[0]])
    out = []
    for k in range(4):
        a = root + across * 12.5 * (k - 1.5) + way * (6 - 2.5 * abs(k - 1.5))
        b = a + way * (34 - 5 * abs(k - 1.3)) + across * 3 * (k - 1.5) + [0, 5]
        out.append((tuple(a), tuple(b)))
    return out


#: The torso, row by row: half its width, its depth, how far it stands out
#: and where its middle is. The trapezius slopes from the neck to the raised
#: shoulders; under the arms the back is broad, the lats sweeping down from
#: the armpits to the waist; below it the hips, under the drape.
TORSO_YS = (330, 350, 372, 395, 425, 455, 490, 540, 610, 680, 730, 775, 830, 890, 960)
TORSO_HALF = (36, 66, 104, 136, 162, 172, 168, 158, 144, 124, 112, 118, 150, 176, 182)
TORSO_DEEP = (34, 50, 64, 76, 86, 90, 92, 92, 90, 84, 78, 80, 88, 90, 90)
TORSO_OUT = (48, 34, 22, 12, 6, 6, 6, 8, 4, -2, -8, -8, -2, 2, 0)
TORSO_SWAY = tuple(X0 + d for d in (4, 3, 2, 1, 0, 0, 0, 0, -2, -2, 0, 2, 2, 0, 0))

#: The drape, the same way, from its rolled top edge to the foot of the sheet.
DRAPE_YS = (DRAPE_Y - 30, 880, 960, 1040, 1110, HEIGHT)
DRAPE_HALF = (170, 188, 208, 230, 248, 262)
DRAPE_DEEP = (86, 92, 92, 90, 86, 84)
DRAPE_OUT = (8, 10, 6, 0, -4, -6)
DRAPE_SWAY = (X0, X0 - 2, X0 - 4, X0 - 4, X0 - 2, X0)
#: The knot of the cloth at her right hip, and the folds pulled from it
#: across the back and round (angle in degrees, length, height).
KNOT = (X0 - 150, 872.0)
PULLED = ((4, 330, 7), (16, 360, 10), (30, 330, 8), (46, 300, 9), (64, 250, 7))
#: The folds hanging under their own weight below the stool's edge.
HANGING = (
    (-215, 8),
    (-150, 5),
    (-95, 7),
    (-30, 6),
    (55, 9),
    (120, 6),
    (175, 8),
    (228, 9),
)

#: The furrow of the spine, from the base of the neck to the drape.
SPINE = ((X0 + 3, 372), (X0 + 1, 470), (X0 - 2, 600), (X0 - 1, 720), (X0 + 2, 840))
#: The head (centre, radii, how far its middle stands out, turn) and the
#: hair over it, cut off at the nape.
HEAD_AT = ((X0 + 6, 246), (72, 88, 74), 30.0, 6.0)
HAIRLINE = 314.0
#: The twist of hair the hands hold, from the crown up and its end turning
#: over to the left.
TWIST = ((X0 + 2, 212), HAIR_KNOT, (X0 - 4, 102), (X0 - 20, 80), (X0 - 46, 86))
TWIST_R = (28, 21, 19, 13, 6)


# --- solids ------------------------------------------------------------------


def ellipsoid(centre, radii, z=0.0, turn=0.0):
    """How far an ellipsoid's back stands out at each pixel (``_NONE`` off
    it). ``centre`` is (x, y) on the sheet, ``radii`` (across, down, deep),
    ``z`` how far its middle stands out, ``turn`` its turn in the sheet's
    plane in degrees."""
    c, s = np.cos(np.radians(turn)), np.sin(np.radians(turn))
    dx, dy = px - centre[0], py - centre[1]
    u, v = (dx * c + dy * s) / radii[0], (-dx * s + dy * c) / radii[1]
    q = 1.0 - u * u - v * v
    return np.where(q > 0.0, z + radii[2] * np.sqrt(np.clip(q, 0.0, 1.0)), _NONE)


def capsule(a, b, ra, rb, za=0.0, zb=0.0):
    """A tapered rod from ``a`` to ``b`` (points on the sheet), ``ra`` and
    ``rb`` thick at its ends, its axis ``za`` and ``zb`` out."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ab = b - a
    t = np.clip(((px - a[0]) * ab[0] + (py - a[1]) * ab[1]) / (ab @ ab), 0.0, 1.0)
    d2 = (px - a[0] - t * ab[0]) ** 2 + (py - a[1] - t * ab[1]) ** 2
    r = ra + (rb - ra) * t
    q = r * r - d2
    return np.where(q > 0.0, za + (zb - za) * t + np.sqrt(np.clip(q, 0.0, None)), _NONE)


def smooth_line(values, n=256):
    """``n`` values through ``values`` (at even places from 0 to 1),
    smoothed so that they bend without kinks."""
    fine = np.linspace(0.0, 1.0, n)
    line = np.interp(fine, np.linspace(0.0, 1.0, len(values)), values)
    for _ in range(2):
        line = np.convolve(np.pad(line, 12, mode="edge"), np.ones(25) / 25, "valid")
    return line


def _nearest(points):
    """For each pixel, the square of its distance to the polyline through
    ``points`` and how far along it (0 to 1) the nearest point lies."""
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


def limb_depth(limb: Limb):
    best, along = _nearest(limb.points)
    fine = np.linspace(0.0, 1.0, 256)
    r = np.interp(along, fine, smooth_line(limb.radii))
    q = r * r - best
    z = np.interp(along, fine, smooth_line(limb.zs))
    return np.where(q > 0.0, z + np.sqrt(np.clip(q, 0, None)), _NONE)


def melt(depths, k):
    """The smooth maximum of several depths: one surface over them all,
    rounded by about ``k`` where they meet."""
    out = depths[0]
    for d in depths[1:]:
        both = (out > _NONE / 2) & (d > _NONE / 2)
        h = np.clip(0.5 + 0.5 * (d - out) / k, 0.0, 1.0)
        mixed = out + (d - out) * h + k * h * (1.0 - h)
        out = np.where(both, mixed, np.maximum(out, d))
    return out


def bump(x0, y0, sx, sy, turn=0.0):
    """A soft round bump of height 1 about (x0, y0), ``sx`` by ``sy``."""
    c, s = np.cos(np.radians(turn)), np.sin(np.radians(turn))
    dx, dy = px - x0, py - y0
    u, v = (dx * c + dy * s) / sx, (-dx * s + dy * c) / sy
    return np.exp(-(u * u + v * v))


def ridge(points, width, heights):
    """A ridge (or with heights below 0, a groove) along a polyline, of
    gaussian section ``width`` wide, its height changing along it."""
    best, along = _nearest(points)
    height = np.interp(along, np.linspace(0, 1, len(heights)), heights)
    return height * np.exp(-best / width**2)


def profile(ys, values, soft=18):
    """A value at every row of the sheet, through ``values`` at the rows
    ``ys`` and smoothed over about ``soft`` rows."""
    rows = np.arange(HEIGHT, dtype=np.float64)
    line = np.interp(rows, ys, values)
    for _ in range(3):
        line = box_blur(line[:, None], soft // 2)[:, 0]
    return line


def loft(ys, half, deep, out, sway, flat=0.45):
    """A body of rounded sections stacked down the sheet: at each height y
    (``ys``) it is ``half`` wide either side of ``sway``, ``deep`` deep and
    stands ``out``. ``flat`` below 0.5 flattens the section's back."""
    row = np.clip(py, 0, HEIGHT - 1).astype(int)
    w = np.maximum(profile(ys, half)[row], 1.0)
    u = (px - profile(ys, sway)[row]) / w
    q = np.clip(1.0 - u * u, 0.0, 1.0)
    z = profile(ys, out)[row] + profile(ys, deep)[row] * q**flat
    there = (np.abs(u) < 1.0) & (py >= ys[0]) & (py <= ys[-1])
    return np.where(there, z, _NONE)


def back_relief():
    """What the bones and the muscles raise and hollow on the back."""
    relief = ridge(SPINE, 10.0, [-1, -3, -4, -9, -8])
    for side in (-1, 1):
        # the long muscles beside the spine, fuller low down
        erector = [(X0 + side * 26, 560), (X0 + side * 32, 690), (X0 + side * 34, 830)]
        relief += ridge(erector, 18.0, [1, 6, 7])
        # the shoulder blade, turned up and out by the raised arm: a low
        # plate, its inner border a soft edge with a hollow inside it
        relief += 6.0 * bump(X0 + side * 94, 490, 48, 62, side * 30)
        relief += ridge(scapula(side), 12.0, [3, 5])
        relief -= 6.0 * bump(X0 + side * 58, 515, 15, 58, side * -26)
        relief += 4.0 * bump(X0 + side * 112, 552, 16, 16)
        relief -= 3.0 * bump(X0 + side * 128, 600, 22, 26)  # (under its point)
        # the trapezius bunched between the neck and the raised shoulder
        relief += 3.0 * bump(X0 + side * 70, 380, 40, 20, side * 20)
        # the dimples above the drape and the side of the waist pulled in
        relief -= 4.0 * bump(X0 + side * 38, 812, 10, 9)
        relief -= 4.0 * bump(X0 + side * 106, 660, 18, 70)
    relief += 4.0 * bump(X0 + 3, 376, 11, 9)  # the seventh vertebra
    return relief


def scapula(side: int):
    """The inner border of a shoulder blade, from its top to its point."""
    return ((X0 + side * 50, 432), (X0 + side * 112, 566))


def body_depth():
    """The torso, the neck and the upper arms, as one surface."""
    torso = loft(TORSO_YS, TORSO_HALF, TORSO_DEEP, TORSO_OUT, TORSO_SWAY)
    neck = capsule((X0 + 2, 290), (X0 + 2, 372), 33, 40, 46, 44)
    z = melt([torso, neck, *map(limb_depth, UPPER_ARMS)], 18.0)
    return z + back_relief()


def arm_depth():
    """The forearms and the hands, the fingers closed round the twist."""
    parts = [limb_depth(limb) for limb in FOREARMS + HANDS]
    for side in (-1, 1):
        parts += [capsule(a, b, 8.0, 6.5, 116, 112) for a, b in fingers(side)]
    return melt(parts, 5.0)


def head_depth():
    (cx, cy), radii, z, turn = HEAD_AT
    head = ellipsoid((cx, cy), radii, z, turn)
    ears = [ellipsoid((cx + 2 + s * 66, cy + 20), (7, 18, 12), z=36) for s in (-1, 1)]
    return melt([head, *ears], 6.0)


def hair_depth():
    """The hair over the back of the head, gathered up into a twist held in
    the hands, and its end above them."""
    (cx, cy), (rx, ry, rz), z, turn = HEAD_AT
    cap = ellipsoid((cx, cy - 4), (rx + 5, ry + 2, rz + 5), z + 2, turn)
    cap = np.where(py < hairline(px), cap, _NONE)
    best, along = _nearest(TWIST)
    fine = np.linspace(0.0, 1.0, 256)
    r = np.interp(along, fine, smooth_line(TWIST_R))
    q = r * r - best
    twist = np.where(q > 0.0, 94 + np.sqrt(np.clip(q, 0, None)), _NONE)
    return melt([cap, twist], 10.0)


def hairline(x):
    """Where the hair ends on the nape: low to a point in the middle, high
    behind the ears."""
    d = (x - X0 - 4) / 70.0
    return HAIRLINE + 14 * np.exp(-(((x - X0 - 4) / 26.0) ** 2)) - 26 * d * d


def pulled_folds():
    """The paths of the folds pulled from the knot."""
    knot = np.array(KNOT)
    paths = []
    for k, (angle, length, _height) in enumerate(PULLED):
        a = np.radians(angle)
        end = knot + length * np.array([np.cos(a), np.sin(a)])
        mid = (knot + end) / 2 + [0, 18 + 6 * k]
        paths.append((knot, mid, end))
    return paths


def hanging_folds():
    return [((X0 + x, 1020), (X0 + 1.12 * x, HEIGHT)) for x, _h in HANGING]


def drape_top(x):
    return DRAPE_Y + 14 * np.cos((x - X0) / 70.0) - 10 + 0.06 * (x - X0)


def drape_depth():
    """A cloth round the hips, its top edge rolled, gathered at her right
    hip and falling over the stool in folds."""
    base = loft(DRAPE_YS, DRAPE_HALF, DRAPE_DEEP, DRAPE_OUT, DRAPE_SWAY, 0.4)
    top = drape_top(px)
    base = np.where(py > top, base + 6, _NONE)
    folds = 5.0 * np.exp(-(((py - top - 7) / 6.0) ** 2))  # (the rolled edge)
    for k, (path, (_a, _l, height)) in enumerate(
        zip(pulled_folds(), PULLED, strict=True)
    ):
        folds += ridge(path, 8.0 + 2 * k, [height, 0.9 * height, 0.2 * height])
    for path, (_x, h) in zip(hanging_folds(), HANGING, strict=True):
        folds += ridge(path, 10.0, [0, h, h])
    folds += 8.0 * bump(KNOT[0], KNOT[1], 22, 18)
    return np.where(base > _NONE / 2, base + folds, _NONE)


# --- outlines -----------------------------------------------------------------


def loft_side(ys, half, sway, side: int, y0=None, y1=None, step=4.0):
    """One side of a lofted body, from row ``y0`` to ``y1``."""
    y = np.arange(y0 or ys[0], (y1 or ys[-1]) + 1, step, dtype=float)
    rows = y.astype(int).clip(0, HEIGHT - 1)
    x = profile(ys, sway)[rows] + side * profile(ys, half)[rows]
    return np.stack([x, y], axis=1)


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
    a = np.radians(np.linspace(start, end, n))
    c, s = np.cos(np.radians(turn)), np.sin(np.radians(turn))
    u, v = radii[0] * np.cos(a), radii[1] * np.sin(a)
    return np.stack([centre[0] + u * c - v * s, centre[1] + u * s + v * c], axis=1)


# --- the whole ----------------------------------------------------------------


@dataclass
class Model:
    """The figure as the crayons need it, every array ``HEIGHT`` by ``WIDTH``."""

    part: np.ndarray  #: what each pixel shows (``WALL``, ``SKIN``, ...)
    depth: np.ndarray  #: how far it stands out (the wall far behind)
    normal: np.ndarray  #: which way it faces, (3, HEIGHT, WIDTH)
    lamp: np.ndarray  #: the light the lamp gives it, 0 to 1, shadows cast in
    tone: np.ndarray  #: the tone wanted there, 0 black to 1 white

    def at(self, field, points):
        """``field`` read at each of ``points``."""
        points = np.asarray(points)
        col = np.clip(np.rint(points[:, 0]).astype(int), 0, WIDTH - 1)
        row = np.clip(np.rint(points[:, 1]).astype(int), 0, HEIGHT - 1)
        return field[row, col]


def _normals(z):
    gy, gx = np.gradient(box_blur(z, 1))
    n = np.stack([-gx, -gy, np.ones_like(z)])
    return n / np.linalg.norm(n, axis=0)


def _cast(z, part):
    """How much of the lamp reaches each pixel (1 lit, 0 in a cast shadow):
    a ray towards the lamp, over the depths."""
    flat = np.hypot(LIGHT[0], LIGHT[1])
    dx, dy, rise = LIGHT[0] / flat, LIGHT[1] / flat, LIGHT[2] / flat
    lit = np.ones_like(z)
    for step in range(3, 240, 3):
        col = np.clip(np.rint(px + dx * step).astype(int), 0, WIDTH - 1)
        row = np.clip(np.rint(py + dy * step).astype(int), 0, HEIGHT - 1)
        over = z[row, col] - (z + rise * step + 4.0)
        lit = np.minimum(lit, np.clip(1.0 - over / 10.0, 0.0, 1.0))
    return np.where(part != WALL, lit, 1.0)


def build() -> Model:
    layers = [
        (body_depth(), SKIN),
        (head_depth(), SKIN),
        (hair_depth(), HAIR),
        (arm_depth(), SKIN),
        (drape_depth(), DRAPE),
    ]
    depth = np.full(px.shape, _NONE)
    part = np.full(px.shape, WALL)
    normal = np.zeros((3,) + px.shape)
    for z, which in layers:
        front = (z > _NONE / 2) & (z > depth)
        depth = np.where(front, z, depth)
        part = np.where(front, which, part)
        n = _normals(np.where(z > _NONE / 2, z, 0.0))
        normal[:, front] = n[:, front]
    normal[2, part == WALL] = 1.0
    depth = np.where(part == WALL, -200.0, depth)
    facing = np.clip(np.tensordot(LIGHT, normal, axes=1), 0.0, 1.0)
    lamp = facing * _cast(depth, part)
    # what the hollows of the surface hide of the light from all round
    hollow = np.clip((box_blur(depth, 12) - depth) / 10.0, 0.0, 1.0)
    around = 0.5 + 0.5 * normal[2] - 0.25 * hollow
    back = 0.12 * np.clip(normal[1], 0.0, 1.0)  # (what the drape throws up)
    tone = 0.04 + 0.78 * lamp + 0.14 * around + back
    return Model(part, depth, normal, lamp, np.clip(tone, 0.0, 1.0))

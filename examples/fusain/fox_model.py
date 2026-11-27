"""The red fox of ``fox.py``, built as solids and lit.

Imported by ``fox.py``, which lays the pastel pencils over it: this module
gives, for every pixel of the sheet, whether the fox is there, which way its
surface faces and how much light it takes; the colour of the coat there
(orange, white or black, in shares); which way the fur lies and how long it
is; and where the eyes, the nose and the mouth are.

The head is turned three-quarters to our left, the far eye showing. In
units of the head's length from the nose to the back of the skull (360 of
the model's units, ``SCALE`` times as many pixels on the sheet): the
muzzle is two fifths of it, narrowing to a nose an eighth of the head
across; the eyes are slanted almonds, their outer corners higher, a third
of the way back; the ears are tall (half the head), broad at the base and
pointed, set far apart on the top of the skull. Below the head the cheeks
flare into a ruff of long fur, and the neck runs down into a deep chest
with a white bib.

The coat: orange over the head, the ears and the shoulders; white on the
upper lip, the jaw, the lower cheeks and the bib, cream inside the ears;
black at the rims and tips of the ears and down the tear lines from the
eyes to the lips (the lids, the lips and the nose, black too, are drawn by
``fox.py`` on its own). The fur lies
back from the nose over the head, up the ears, out and down over the ruff
and down the chest; it is shortest on the muzzle and longest on the ruff.
"""

# cspell:words tensordot

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from solids import NONE, Limb, Solids, melt

from murex.filters import box_blur, smoothstep

WIDTH, HEIGHT = 900, 1200
#: Where the light comes from: high on the left, a little in front.
LIGHT = np.array([-0.55, -0.62, 0.56])
LIGHT = LIGHT / np.linalg.norm(LIGHT)

#: What each pixel shows.
EMPTY, FUR, NOSE = 0, 1, 2

#: The fox is laid out in units of its own, drawn this much larger about
#: the top of the sheet.
SCALE, ORIGIN = 1.15, (430.0, 90.0)
SOLIDS = Solids(WIDTH, HEIGHT, SCALE, ORIGIN)
px, py = SOLIDS.px, SOLIDS.py
on_sheet = SOLIDS.on_sheet

# --- the head ----------------------------------------------------------------

#: The tip of the nose, and the middle of the skull.
NOSE_TIP = (248.0, 548.0)
SKULL = (482.0, 410.0)
MUZZLE = Limb(((440, 448), (338, 506), (262, 545)), (68, 46, 30), (55, 84, 100))
JAW = Limb(((430, 545), (350, 564), (292, 572)), (34, 24, 15), (40, 54, 66))
#: The ears, near (left) and far: the two corners of the base and the tip.
EARS = (
    ((338, 352), (452, 302), (338, 138)),
    ((528, 296), (630, 336), (636, 136)),
)


def ear_frame(ear):
    """For each pixel, how far inside an ear it lies (0 on its edge, 1 at
    its middle, below 0 outside) and how far up it (0 at the base, 1 at
    the tip)."""
    a, b, tip = (np.asarray(p, float) for p in ear)
    inside = np.full(px.shape, np.inf)
    for p, q in ((a, b), (b, tip), (tip, a)):
        edge = (q - p) / np.hypot(*(q - p))
        inside = np.minimum(inside, (px - p[0]) * edge[1] - (py - p[1]) * edge[0])
    # (the corners run clockwise on the sheet, so inside is where all are > 0)
    base = (a + b) / 2
    up = tip - base
    along = ((px - base[0]) * up[0] + (py - base[1]) * up[1]) / (up @ up)
    width = 0.5 * np.hypot(*(b - a)) * np.clip(1.0 - along, 0.05, 1.0)
    return inside / (0.45 * width), along


def ear_depth(ear, z):
    inside, _along = ear_frame(ear)
    # a plate, thicker along its middle and cupped: its rim stands up
    cup = 1.0 - 0.6 * np.exp(-((np.clip(inside, 0, None) - 1.0) ** 2) / 0.3)
    return np.where(inside > 0.0, z + 24.0 * np.sqrt(np.clip(inside, 0, 1)) * cup, NONE)


@dataclass(frozen=True)
class Eye:
    """A slanted almond: its corners and how far its lids open."""

    inner: tuple
    outer: tuple
    open: float

    @property
    def middle(self):
        return (
            (self.inner[0] + self.outer[0]) / 2,
            (self.inner[1] + self.outer[1]) / 2,
        )

    def outline(self, n=40):
        """The upper lid from the inner corner to the outer, then the lower
        back to the inner corner."""
        a, b = np.asarray(self.inner, float), np.asarray(self.outer, float)
        way = (b - a) / np.hypot(*(b - a))
        up = np.array([way[1], -way[0]])
        t = np.linspace(0.0, 1.0, n)
        lid = np.sin(np.pi * t) ** 0.8
        upper = a + np.outer(t, b - a) + np.outer(self.open * lid, up)
        lower = a + np.outer(t, b - a) - np.outer(0.85 * self.open * lid, up)
        return np.vstack([upper, lower[::-1]])

    def inside(self, grow=0.0):
        """Whether each pixel lies in the eye (``grow`` px beyond its lids)."""
        a, b = np.asarray(self.inner, float), np.asarray(self.outer, float)
        length = np.hypot(*(b - a))
        way = (b - a) / length
        t = ((px - a[0]) * way[0] + (py - a[1]) * way[1]) / length
        s = (px - a[0]) * way[1] - (py - a[1]) * way[0]  # (above the line)
        lid = np.sin(np.pi * np.clip(t, 0, 1)) ** 0.8
        top = self.open * lid + grow
        bottom = 0.85 * self.open * lid + grow
        return (
            (t > -grow / length) & (t < 1 + grow / length) & (s < top) & (-s < bottom)
        )


EYES = (Eye((338, 431), (398, 404), 14.0), Eye((500, 411), (542, 392), 12.0))
#: The tear lines, from the inner corner of each eye down to the lips.
TEAR_LINES = (
    ((340, 432), (326, 462), (312, 500), (300, 530)),
    ((501, 414), (488, 446), (470, 482)),
)
#: The line of the lips, from under the nose back to the corner of the mouth.
LIPS = ((262, 566), (300, 572), (350, 573), (400, 566), (430, 556))
#: Where the whiskers grow, on each side of the muzzle.
WHISKER_PADS = ((300, 548), (330, 556), (288, 538))


def head_depth():
    skull = SOLIDS.ellipsoid(SKULL, (128, 112, 104), z=10, turn=-8)
    muzzle, jaw = SOLIDS.limb(MUZZLE), SOLIDS.limb(JAW)
    # the cheeks, swelling below the eyes, and the ruff of long fur flaring
    # back from them under the far ear and down to the throat
    cheeks = SOLIDS.ellipsoid((430, 505), (100, 60, 50), z=56)
    ruff = SOLIDS.ellipsoid((585, 520), (140, 128, 84), z=0, turn=-20)
    throat = SOLIDS.ellipsoid((470, 600), (120, 76, 70), z=10)
    ears = [ear_depth(ear, 40 - 16 * k) for k, ear in enumerate(EARS)]
    return melt([skull, muzzle, jaw, cheeks, ruff, throat, *ears], 14.0)


def nose_depth():
    return SOLIDS.ellipsoid((NOSE_TIP[0] + 6, NOSE_TIP[1] - 2), (24, 18, 18), z=122)


def body_depth():
    """The neck and the chest, under the head, down to the foot of the sheet."""
    ys = (500, 620, 760, 900, HEIGHT)
    half = (165, 195, 215, 220, 215)
    deep = (110, 140, 150, 150, 150)
    out = (-30, -40, -40, -45, -50)
    sway = (565, 530, 500, 482, 472)
    return SOLIDS.loft(ys, half, deep, out, sway, 0.5)


# --- the coat ----------------------------------------------------------------


def white_line(x):
    """Below this line on the face the fur is white: the upper lip, the
    jaw, the lower cheeks and the throat."""
    return np.interp(
        x, (230, 300, 380, 450, 530, 620, 720), (556, 536, 524, 522, 548, 600, 660)
    )


def back_line(y):
    """Behind this line (on our right) the neck and the shoulders are orange."""
    return np.interp(y, (480, 600, 760, 950, 1200), (700, 630, 540, 470, 440))


def coat(part):
    """The share of white and of black in the coat at each pixel (the rest
    is orange), and where the inside of the ears is (cream)."""
    on = part != EMPTY
    white = smoothstep(-6.0, 6.0, py - white_line(px))
    white *= smoothstep(30.0, -30.0, px - back_line(py))
    black = np.zeros_like(px)
    inner = np.zeros_like(px)
    for ear in EARS:
        inside, along = ear_frame(ear)
        there = inside > 0.0
        tip = smoothstep(0.55, 0.75, along)
        rim = smoothstep(0.45, 0.15, inside) * (along > 0.1)
        black = np.maximum(black, there * np.maximum(tip, 0.85 * rim))
        inner = np.maximum(
            inner, there * smoothstep(0.35, 0.6, inside) * smoothstep(0.7, 0.45, along)
        )
    for line in TEAR_LINES:
        best, along = SOLIDS.nearest(line)
        black = np.maximum(
            black,
            0.8 * np.exp(-best / (3.5 + 2 * along) ** 2) * smoothstep(1.0, 0.6, along),
        )
    white = np.where(on, white * (1 - black) * (1 - inner), 0.0)
    return white, np.where(on, black, 0.0), np.where(on, inner, 0.0)


def flow():
    """Which way the fur lies at each pixel (a unit vector), and how long it
    is there in pixels."""

    def way(dx, dy):
        n = np.hypot(dx, dy) + 1e-9
        return dx / n, dy / n

    # back from the nose over the head
    hx, hy = way(px - NOSE_TIP[0], py - NOSE_TIP[1])
    # out and down over the ruff
    rx, ry = way(*way(px - 420, py - 450))
    rx, ry = way(rx + 0.2, ry + 0.9)
    # down the chest, a little out from the bib
    cx, cy = way(0.35 * (px - 440) / 150, np.ones_like(px))
    head = smoothstep(560.0, 500.0, py) * smoothstep(560.0, 470.0, px)
    ruff = smoothstep(470.0, 540.0, px + 0.3 * (py - 500)) * smoothstep(
        720.0, 640.0, py
    )
    ruff = np.maximum(
        ruff,
        smoothstep(540.0, 600.0, py)
        * smoothstep(680.0, 620.0, py)
        * smoothstep(400.0, 470.0, px),
    )
    chest = smoothstep(620.0, 700.0, py)
    total = head + ruff + chest + 1e-6
    fx = (head * hx + ruff * rx + chest * cx) / total
    fy = (head * hy + ruff * ry + chest * cy) / total
    length = (9.0 * head + 24.0 * ruff + 28.0 * chest) / total
    # up the ears
    for ear in EARS:
        depth, _along = ear_frame(ear)
        inside = smoothstep(-0.1, 0.1, depth)
        base = ((ear[0][0] + ear[1][0]) / 2, (ear[0][1] + ear[1][1]) / 2)
        ex, ey = way(ear[2][0] - base[0], ear[2][1] - base[1])
        fx = (1 - inside) * fx + inside * ex
        fy = (1 - inside) * fy + inside * ey
        length = (1 - inside) * length + inside * 12.0
    # short on the muzzle and the jaw, from the nose and the chin back
    best, _along = SOLIDS.nearest(MUZZLE.points)
    muzzle = smoothstep(70.0, 40.0, np.sqrt(best)) * smoothstep(560.0, 520.0, py)
    best, _along = SOLIDS.nearest(JAW.points)
    muzzle = np.maximum(
        muzzle, smoothstep(40.0, 20.0, np.sqrt(best)) * smoothstep(420.0, 380.0, px)
    )
    fx = (1 - muzzle) * fx + muzzle * hx
    fy = (1 - muzzle) * fy + muzzle * hy
    length = (1 - muzzle) * length + muzzle * 6.0
    n = np.hypot(fx, fy) + 1e-9
    return np.stack([fx / n, fy / n]), length


# --- the whole ----------------------------------------------------------------


@dataclass
class Model:
    """The fox as the pencils need it, every array ``HEIGHT`` by ``WIDTH``."""

    part: np.ndarray  #: what each pixel shows (``EMPTY``, ``FUR``, ``NOSE``)
    lamp: np.ndarray  #: the light the lamp gives it, 0 to 1, shadows cast in
    light: np.ndarray  #: how light the coat looks there, 0 to 1, for its colour
    white: np.ndarray  #: the share of white in the coat
    black: np.ndarray  #: the share of black
    inner: np.ndarray  #: the inside of the ears (cream)
    flow: np.ndarray  #: which way the fur lies, (2, HEIGHT, WIDTH)
    length: np.ndarray  #: how long it is, in pixels
    eyes: np.ndarray  #: whether a pixel is in an eye (no fur there)

    def at(self, field, points):
        """``field`` read at each of ``points``."""
        return SOLIDS.at(field, points)


def build() -> Model:
    part, depth, normal = SOLIDS.stack(
        [(body_depth(), FUR), (head_depth(), FUR), (nose_depth(), NOSE)], empty=EMPTY
    )
    depth = np.where(part == EMPTY, -300.0, depth)
    facing = np.clip(np.tensordot(LIGHT, normal, axes=1), 0.0, 1.0)
    lamp = facing * np.where(part != EMPTY, SOLIDS.cast(depth, LIGHT), 1.0)
    hollow = np.clip((box_blur(depth, 10) - depth) / 10.0, 0.0, 1.0)
    around = 0.5 + 0.5 * normal[2] - 0.3 * hollow
    light = np.clip(0.05 + 0.8 * lamp + 0.15 * around, 0.0, 1.0)
    eyes = np.zeros(px.shape, bool)
    for eye in EYES:
        eyes |= eye.inside(grow=2.0)
    white, black, inner = coat(part)
    # (white fur takes the light thrown back from all round into its shadows)
    light = np.maximum(light, (white + inner) * (0.3 + 0.2 * normal[2]))
    way, length = flow()
    return Model(part, lamp, light, white, black, inner, way, SCALE * length, eyes)

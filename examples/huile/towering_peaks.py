"""Towering Peaks, after Bob Ross (The Joy of Painting, series 10, episode 1).

The painting he made in that episode, step by step and stroke by stroke as
he paints it on the show, on an 18 x 24 inch canvas covered in Liquid White:

1. the sky in little criss-cross strokes of phthalo blue with the two-inch
   brush, then phthalo blue and a touch of phthalo green pulled in from the
   sides low down, leaving a light band; all blended with a clean brush;
2. clouds of titanium white and a touch of bright red, scrubbed in with tiny
   circles, blended and fluffed upward with a clean, dry brush;
3. the mountain cut in with the knife (black, Prussian blue, Van Dyke brown,
   alizarin crimson), pulled down with the two-inch brush so it is lighter at
   the base; snow laid on with no pressure, white on the lit faces and white
   with Prussian blue in the shadows, a ridge brought in front; mist tapped in;
3. three layers of foothills tapped in with the oval brush, each darker than
   the one behind, their bases tapped and lifted into mist;
4. little evergreens tapped downward with the fan brush, their reflections
   pulled straight down and brushed across, and the water's edge cut with
   the knife; a few far trunks lifted up with white;
5. three tall evergreens with the big brush; leaf trees blocked in dark,
   their trunks put in with the knife, then the leaves tapped on with the
   one-inch brush in sap green, cadmium yellow, yellow ochre, Indian yellow
   and a touch of bright red, the farthest first; the path in Van Dyke brown
   and grey, and bushes pushed over it.

Positions are read off a frame of the finished painting (640 x 480) and
scaled to this canvas. The brushes, paints and wet-on-wet techniques are
those of ``bob_ross_style.py``, which paints on the same canvas.

    python examples/huile/towering_peaks.py [output.png] [stages]
"""

import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

import bob_ross_style as B

from murex.huile import SKIM, Brush

mix, thin, st, loaded = B.mix, B.thin, B.st, B.loaded
W, H = B.W, B.H
K = W / 640  # the reference frame is 640 px wide


def hand(path, pressure, r=None, n=None, sway=4.0, wander=0.25):
    """A stroke as a hand lays it, along ``path`` (two points or more, a
    line or a curve): never quite on its line (a slight tilt, a gentle sway
    across it, ``sway`` px) and never evenly pressed (the pressure profile
    given rises and falls by up to ``wander``). ``sway=0, wander=0`` gives
    the stroke exactly as drawn. Returns the points and the pressures."""
    r = B.rng if r is None else r
    path = np.asarray(path, float)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    along = np.r_[0, np.cumsum(seg)] / max(seg.sum(), 1e-9)
    n = n or max(8, len(path) * 3)
    t = np.linspace(0, 1, n)
    pts = np.stack([np.interp(t, along, path[:, k]) for k in (0, 1)], 1)
    tang = np.gradient(pts, axis=0)
    normal = (
        np.stack([-tang[:, 1], tang[:, 0]], 1)
        / np.maximum(np.hypot(tang[:, 0], tang[:, 1]), 1e-9)[:, None]
    )
    walk = np.cumsum(r.normal(0, sway * 0.5, n))
    walk -= np.linspace(
        walk[0], walk[-1], n
    )  # (a sway, not a drift: the tilt is the drift)
    pts = pts + ((t - 0.5) * 2 * r.normal(0, sway) + walk)[:, None] * normal
    p = np.interp(t, np.linspace(0, 1, len(pressure)), pressure)
    p = np.clip(
        p * (1 + wander * np.convolve(r.normal(0, 1, n + 2), np.ones(3) / 3, "valid")),
        0,
        1,
    )
    if pressure[-1] == 0:
        p[-1] = 0.0
    return [tuple(q) for q in pts], [float(v) for v in p]


def ref(*pts):
    """Points of the 640 x 480 reference frame, on this canvas."""
    return [(x * K, y * K) for x, y in pts]


# ===========================================================================
# 1. Sky and water
# ===========================================================================
# His phthalo blue: huile's greys with white, so cerulean with a little
# ultramarine stands in for it, and keeps his clean, bright blue
BLUE = mix((B.P.CERULEAN_BLUE, 1), (B.P.ULTRAMARINE_BLUE, 1.0))
SKY = mix(
    (B.P.CERULEAN_BLUE, 1), (B.P.COBALT_BLUE, 1)
)  # (his phthalo blue in the sky: clean and bright)
WATER_BLUE = mix(
    (B.P.CERULEAN_BLUE, 1), (B.PHTHALO_GREEN, 0.3), (B.P.ULTRAMARINE_BLUE, 0.2)
)
BAND = 285 * K  # the light band across the middle, where sky meets water


def sky():
    """A small amount of phthalo blue, tapped into the brush, and little
    criss-cross strokes from the top down: the brush runs out as it works
    down and the Liquid White lightens it. Then phthalo blue and a touch of
    phthalo green low down, pulled very gently from the outside in, so a
    light band stays across the middle. Then a clean brush blends it, still
    in criss-crosses, and lightly right across the bottom."""
    B.stage("sky")

    def reload(br, y):
        t = float(np.clip(y / BAND, 0, 1))
        br.load(thin(SKY), 2.4 * (1 - t) ** 1.5)

    b = loaded(B.TWO_INCH, thin(SKY), 2.4)
    B.criss_cross(b, -40, BAND - 40, size=120, reload=reload)

    # (each pull lifts off as it nears the middle, so the ends fade)
    for y in np.arange(BAND + 25, H + 40, 28):
        depth = float(np.clip((y - BAND) / (H - BAND), 0, 1))
        for side in (-1, 1):
            x0 = W / 2 + side * (W / 2 + 80)
            x1 = W / 2 - side * W * 0.1 * depth
            br = loaded(B.TWO_INCH, thin(WATER_BLUE), 5 + 12 * depth)
            pts, p = hand(
                [(x0, y), (x1, y)], [0.25 + 0.4 * depth, 0.05 + 0.2 * depth, 0.0]
            )
            st(pts, None, brush=br, angle=0, pressure=p)
    # (the brush laid broad, angle 0, as it travels across)
    for y in np.arange(BAND, H + 40, 11):
        pts, p = hand([(-80, y), (W + 80, y)], [0.3], sway=3)
        st(pts, None, brush=Brush(B.TWO_INCH), angle=0, pressure=p)

    # a clean brush: criss-crosses over the sky, then long, light strokes across
    B.criss_cross(Brush(B.TWO_INCH), -40, BAND, size=120, pressure=0.25)
    for y in np.arange(-10, BAND + 20, 14):
        pts, p = hand([(-80, y), (W + 80, y)], [0.22], sway=3)
        st(pts, None, brush=Brush(B.TWO_INCH), angle=0, pressure=p)


# ===========================================================================
# 2. Clouds: white with the least touch of bright red
# ===========================================================================
CLOUD_WHITE = mix((B.TITANIUM_WHITE, 60), (B.BRIGHT_RED, 0.5), (B.P.CERULEAN_BLUE, 1.5))
CLOUDS = [  # billows (x, y, radius) in the reference frame, how far down each
    # mass goes in radii, and how much white; the farthest first: a thin haze
    # of cloud across the top, then the masses on it (the corners stay sky)
    (
        [(90, 34, 40), (170, 26, 44), (250, 30, 44), (330, 26, 44), (410, 30, 44)],
        1.2,
        0.18,
    ),
    ([(285, 125, 26), (325, 98, 34), (372, 80, 34), (415, 100, 26)], 1.8, 0.6),
    ([(420, 42, 26), (465, 20, 32), (520, 16, 34), (572, 26, 28)], 1.5, 0.45),
    ([(72, 44, 26), (116, 24, 34), (166, 32, 32), (212, 52, 26)], 1.6, 0.45),
    ([(140, 96, 26), (195, 70, 32), (248, 88, 26)], 1.8, 0.6),
]


def cloud(billows, drop, white=0.75, seed=0):
    """A cloud the way he paints one: a brush loaded with a lot of white (and
    the least touch of bright red), little circular strokes over the top of
    each billow, then on down into it with what is left; then a clean, dry
    two-inch brush, tiny little circles to blend the bottom of it into the
    sky, higher and lighter each time; then lifted, which fluffs it right up;
    and very lightly across."""
    r = np.random.default_rng(seed)
    bil = [(x * K, y * K, rad * K) for x, y, rad in billows]
    size = float(np.mean([rad for _, _, rad in bil])) * 0.75
    xs = np.arange(
        min(x - rad for x, _, rad in bil), max(x + rad for x, _, rad in bil), 2.0
    )
    base = B.cloud_base(bil, xs, drop)
    path = B.scrub_rows(bil, lambda x: np.interp(x, xs, base), xs, size, r)
    # the white: fullest at the top, running thin towards the base
    along = np.r_[0, np.cumsum(np.linalg.norm(np.diff(path, axis=0), axis=1))] / size
    y_top, y_base = path[:, 1].min(), path[:, 1].max()
    for k in range(int(along[-1] // 6) + 1):
        go = (along >= k * 6 - 0.3) & (along < (k + 1) * 6)
        if go.sum() < 3:
            continue
        part = path[go]
        depth = (part[:, 1] - y_top) / max(1.0, y_base - y_top)
        amount = white * (1 - depth.mean()) ** 2 * B.path_length(part) / size
        b = loaded(B.CLOUD_BRUSH.sized(size), thin(CLOUD_WHITE), amount)
        st(part, None, brush=b, pressure=list(0.14 - 0.04 * depth))
    # blend: little circles, from below the base up to the middle of it
    blender = B.MIST_BRUSH.sized(size * 1.4)
    w = blender.width
    line = np.stack([xs[::8], base[::8]], 1)
    for k, (up, pressure) in enumerate(
        ((-0.5, 0.55), (-0.1, 0.5), (0.3, 0.45), (0.7, 0.38), (1.1, 0.28))
    ):
        pts = line - [0, up * w] + r.normal(0, [0, 3], line.shape)
        st(
            B.scrub_along(pts[:: -1 if k % 2 else 1], w * 0.2, w * 0.3, r),
            None,
            brush=Brush(blender),
            pressure=pressure,
            mixing=1.0,
            pickup=0.0,
        )
    # lifted: up from the base, barely touching
    for x, y in line[:: max(1, int(w * 0.35 / 16))]:
        pts, p = hand([(x, y + w * 0.3), (x, y - w * 0.6)], [0.22, 0.03], r=r, sway=2)
        st(pts, None, brush=Brush(blender), pressure=p, mixing=1.0, pickup=0.0)
    # the edge of the crown softened: little circles along it, just outside
    rim = B.cloud_rim(bil, -0.1 * size)
    if len(rim) > 2:
        st(
            B.scrub_along(rim, size * 0.15, size * 0.25, r),
            None,
            brush=Brush(blender.sized(size * 0.8)),
            pressure=0.2,
            mixing=1.0,
            pickup=0.0,
        )
    # and then very lightly, over all of it, the top too
    top_y = min(y for _, y, _ in bil) - 0.5 * size
    for k, y in enumerate(np.linspace(top_y, float(base.max()), 4)):
        line = np.array(
            [(xs[0], y), ((xs[0] + xs[-1]) / 2, y + r.normal(0, 4)), (xs[-1], y)]
        )
        st(
            B.scrub_along(line[:: -1 if k % 2 else 1], w * 0.25, w * 0.35, r),
            None,
            brush=Brush(blender.sized(w * 1.3)),
            pressure=0.1,
            mixing=1.0,
            pickup=0.0,
        )


def clouds():
    B.stage("clouds")
    for seed, (billows, drop, white) in enumerate(CLOUDS, start=1):
        cloud(billows, drop, white, seed=seed)


# ===========================================================================
# 3. The mountain
# ===========================================================================
RIDGE = ref(
    (60, 262), (110, 228), (150, 200), (195, 168), (230, 138), (252, 150),
    (275, 146), (350, 90), (370, 100), (405, 50), (432, 72), (455, 82),
    (520, 122), (590, 165), (660, 200),
)  # fmt: skip
MOUNTAIN_BASE = 290 * K
# the faces that take the light (from the right): each from its top down
LIT = [
    ref((405, 50), (432, 72), (455, 82)),
    ref((455, 82), (520, 122), (590, 165), (650, 196)),
    ref(
        (230, 138), (300, 180), (370, 214), (440, 234), (520, 244)
    ),  # the peak brought in front
]
# and those in shadow, the other side of each
SHADOW = [
    ref((405, 50), (385, 82), (370, 100)),
    ref((350, 90), (310, 118), (275, 146)),
    ref((230, 138), (195, 168), (150, 200), (100, 236)),
    ref((455, 82), (430, 110), (410, 140)),
    ref(
        (350, 90), (390, 128), (440, 158), (500, 172)
    ),  # the ridge that pushes the peak back
]
# (alizarin and ultramarine: the pink-violet of his lit snow; cerulean and
# Prussian blue would turn it green)
SNOW = mix(
    (B.TITANIUM_WHITE, 15),
    (B.ALIZARIN, 2.2),
    (B.P.ULTRAMARINE_BLUE, 0.6),
)
SHADE = mix(
    (B.TITANIUM_WHITE, 1.1),
    (B.P.ULTRAMARINE_BLUE, 1.1),
    (B.PRUSSIAN_BLUE, 0.3),
    (B.ALIZARIN, 0.1),
)
# black, Prussian blue, Van Dyke brown and alizarin crimson, a little white
ROCK = mix(
    (B.P.ULTRAMARINE_BLUE, 1.5),
    (B.P.CERULEAN_BLUE, 1.2),
    (B.PRUSSIAN_BLUE, 0.5),
    (B.VAN_DYKE_BROWN, 0.4),
    (B.ALIZARIN, 0.5),
    (B.MIDNIGHT_BLACK, 0.3),
    (B.TITANIUM_WHITE, 0.8),
)


def mountain():
    """Black, Prussian blue, Van Dyke brown and alizarin crimson, a small roll
    of paint on the knife, the shape cut in along the ridge; the excess
    scraped off with firm pressure, pushing the paint into the canvas; then
    the two-inch brush grabs it and pulls down, so it is lighter at the
    bottom. Snow with no pressure, the light from the right; shadows of white
    and Prussian blue on the other sides; mist tapped in at the base."""
    B.stage("mountain")
    knife_in(RIDGE, MOUNTAIN_BASE - 60 * K, ROCK, seed=3)
    r = np.random.default_rng(31)
    xs, ys = np.array(RIDGE).T
    # scrape it off, firmly, pushing the paint into the canvas; then grab it
    # with the two-inch brush and pull down (each stroke eased in and out)
    for x in np.arange(xs[0] + 10, xs[-1], 24):
        top = float(np.interp(x, xs, ys)) + r.uniform(10, 40)
        pts, p = hand([(x, top), (x, MOUNTAIN_BASE)], [0.0, 0.4, 0.4, 0.0], r=r, sway=2)
        st(pts, None, brush=Brush(B.KNIFE), angle=0, pressure=p)
    for x in np.arange(xs[0] + 10, xs[-1], 34):
        top = float(np.interp(x, xs, ys)) + r.uniform(30, 90)
        if MOUNTAIN_BASE - top < 40:
            continue
        pts, p = hand(
            [(x, top), (x, MOUNTAIN_BASE)], [0.0, 0.22, 0.15, 0.0], r=r, sway=2
        )
        st(pts, None, brush=Brush(B.TWO_INCH), angle=0, pressure=p)
    for k, line in enumerate(SHADOW):
        snow(line, SHADE, seed=70 + k)
    for k, line in enumerate(LIT):
        snow(line, SNOW, seed=80 + k, rows=5)
    # mist: the base tapped and lifted, then blended with a clean brush
    r = np.random.default_rng(32)
    haze = mix(
        (B.TITANIUM_WHITE, 6), (B.P.ULTRAMARINE_BLUE, 0.5), (B.P.CERULEAN_BLUE, 0.4)
    )
    for y in np.arange(235 * K, 300 * K, 14):
        for x in np.arange(130 * K, W + 30, 30):
            q = (x + r.normal(0, 8), y + r.normal(0, 5))
            amount = 0.4 * (y - 235 * K) / (65 * K) + 0.08
            st(
                [q],
                None,
                brush=loaded(B.MIST_BRUSH.sized(110), haze, amount),
                pressure=0.2,
                mixing=0.5,
            )


def knife_in(ridge, base, dark, seed=0):
    """The dark cut in with the knife, a small roll of paint on its edge:
    set down along the ridge line, just under it, and pulled square to
    itself into the mountain, then turned to come straight down (the knife
    strokes of bob_ross_style's knife_mountain, without its haze)."""
    r = np.random.default_rng(seed)
    segs = B.ridge_segments(ridge, 22)
    lower = mix((dark, 1), (B.TITANIUM_WHITE, 4))
    for j, (x, y, slope) in enumerate(segs):
        if base - y < 8:
            continue
        ln = (base - y) * r.uniform(
            0.75, 0.92
        )  # (all the way down: the dark covers the mountain)
        k = (
            Brush(B.KNIFE)
            .load(dark, 0.25 * ln / B.KNIFE.width)
            .load(lower, 0.2 * ln / B.KNIFE.width, depth="heel")
        )
        lo, hi = max(0, j - 2), min(len(segs) - 1, j + 2)
        bend = abs(segs[hi][2] - segs[lo][2])
        width = B.KNIFE.width * (1.0 if bend < 25 else 0.45)
        nx, ny = np.sin(np.radians(slope)), np.cos(np.radians(slope))
        inset = 0.5 * B.KNIFE.aspect * width + (3 if bend >= 25 else 0)
        x0, y0 = x + nx * inset, y + ny * inset
        x1, y1 = x0 + nx * 0.3 * ln, y0 + ny * 0.3 * ln
        pts = [
            (x0, y0),
            (x1 + r.normal(0, 3), y1),
            (x1 + r.normal(0, 5), y1 + 0.7 * ln),
        ]
        st(
            pts,
            None,
            brush=k,
            width=width,
            angle=0,
            follow_path=True,
            pressure=0.65,
            lift=0.0,
        )


SNOW_PRESSURE = SKIM  # (the measured skim: see snow)


def snow(line, colour, seed=0, blade=None, rows=2):
    """The knife with a small roll of paint on its edge, set down at the top
    of a face with its upper end on the ridge, and pulled down the face with
    no pressure at all (``SKIM``), the blade across the pull, so the paint
    breaks: a thin sheet with ragged holes where the rock shows. One pull a
    face (a second over the same place fills the holes); on a long face, a
    second one lower down, beside it. (huile's measured recipe: see
    docs/huile/README.md, Knives.)"""
    r = np.random.default_rng(seed)
    blade = blade or B.KNIFE
    pts = np.asarray(line, float)
    along = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    total = along[-1]
    width = min(0.8 * blade.width, total)
    # (each row lower on the face than the last, and never over the same
    # place: a second pull over a place fills its holes)
    pulls = [(0, 0.0, r.uniform(0.75, 0.95))]
    pulls += [
        (row, 0.12 * row, r.uniform(0.85, 0.95) - 0.15 * row)
        for row in range(1, rows)
        if total > (2 + row) * width
    ]
    for row, a0, a1 in pulls:
        inset = (0.5 + 0.9 * row) * width + 3
        path = []
        for d in np.linspace(a0 * total, a1 * total, 8):
            x, y = (np.interp(d, along, pts[:, k]) for k in (0, 1))
            a = [
                np.interp(d + 4, along, pts[:, k]) - np.interp(d - 4, along, pts[:, k])
                for k in (0, 1)
            ]
            tx, ty = np.array(a) / np.hypot(*a)
            nx, ny = (-ty, tx) if tx > 0 else (ty, -tx)  # into the mountain
            if y + ny * inset > MOUNTAIN_BASE - 20:
                break
            path.append((x + nx * inset, y + ny * inset))
        if len(path) < 3:
            continue
        path, _ = hand(path, [SNOW_PRESSURE], r=r, sway=1.5, wander=0)
        ln = B.path_length(np.array(path))
        k = Brush(blade).load(colour, max(3.0, 0.42 * ln / width * 3))
        st(
            path,
            None,
            brush=k,
            width=width,
            angle=0,
            follow_path=True,
            # (set down gently, row after row: a hard start would show as a step)
            pressure=[SNOW_PRESSURE * (0.4 if row else 1.0)]
            + [SNOW_PRESSURE] * (len(path) - 2)
            + [0.0],
            lift=0.0,
        )


def mist(line, height, seed=0):
    """A clean, dry brush tapped along the base, then lifted gently upward:
    the tap marks go and the base melts into a soft mist."""
    r = np.random.default_rng(seed)
    brush = B.MIST_BRUSH.sized(110)
    (x0, y0), (x1, y1) = line[0], line[-1]
    for x in np.arange(x0, x1, 18):
        y = y0 + (y1 - y0) * (x - x0) / (x1 - x0) + r.normal(0, 6)
        for dy in (0, -0.4 * height):
            st(
                [(x, y + dy)],
                None,
                brush=Brush(brush),
                pressure=0.5,
                mixing=1.0,
                pickup=0.0,
            )
        st(
            [(x, y + 15), (x + r.normal(0, 3), y - height)],
            None,
            brush=Brush(brush),
            pressure=[0.35, 0.02],
            mixing=1.0,
            pickup=0.0,
        )


# ===========================================================================
# 4. Foothills, with the oval brush
# ===========================================================================
OVAL = B.brushes.make("filbert", 34, "hog", length=0.6, capacity=1.4, name="oval brush")
# the mountain colour, the least touch of sap green, and white
# (his blues as huile's cerulean and ultramarine: Prussian blue greys here)
FOOT = mix(
    (B.MOUNTAIN_DARK, 1),
    (B.P.CERULEAN_BLUE, 0.8),
    (B.P.ULTRAMARINE_BLUE, 1.0),
    (B.SAP_GREEN, 0.05),
)
HILLS = [  # top line, depth, and how much white; the farthest first
    (
        ref(
            (205, 298),
            (250, 290),
            (300, 296),
            (340, 288),
            (390, 280),
            (430, 270),
            (470, 258),
            (505, 248),
            (540, 246),
            (570, 262),
        ),
        40,
        1.2,
    ),
    (
        ref(
            (210, 312),
            (240, 318),
            (275, 326),
            (330, 318),
            (380, 312),
            (420, 300),
            (460, 296),
            (500, 305),
            (540, 312),
        ),
        34,
        0.25,
    ),
    (
        ref(
            (215, 336),
            (260, 340),
            (320, 332),
            (370, 328),
            (420, 322),
            (470, 326),
            (520, 336),
        ),
        30,
        0.0,
    ),
]


def foothill(top, depth, colour, seed=0):
    """Tapped in with the oval brush full of paint: the tops of thousands of
    little trees far off; the brush is tapped, never pulled."""
    r = np.random.default_rng(seed)
    xs, ys = np.array(top).T
    # the top line breaks up into rounded lumps of trees
    lumps = (
        np.convolve(
            r.normal(0, 7, len(np.arange(xs[0], xs[-1], 4)) + 8),
            np.ones(9) / 9,
            "valid",
        )
        * 2.5
    )
    span, d = xs[-1] - xs[0], depth * K
    for _ in range(int(span * d / 14)):
        x = r.uniform(xs[0], xs[-1])
        u = r.uniform(0, 1) ** 1.3  # most taps near the top
        y = float(np.interp(x, xs, ys)) + lumps[int((x - xs[0]) / 4)] + u * d
        st(
            [(x, y)],
            colour,
            width=r.uniform(18, 30),
            brush=OVAL,
            amount=1.2,
            pressure=r.uniform(0.4, 0.6),
            mixing=0.15,
            pickup=0.05,
        )
    base = [(xs[0], ys[0] + depth * K), (xs[-1], ys[-1] + depth * K)]
    mist(base, depth * K * 0.12, seed=seed + 100)


def foothills():
    B.stage("foothills")
    for k, (top, depth, white) in enumerate(HILLS):
        foothill(top, depth, mix((FOOT, 1), (B.TITANIUM_WHITE, white)), seed=40 + k)


# ===========================================================================
# 5. Little evergreens at the water, and their reflections
# ===========================================================================
WATER = 392 * K
TREE_DARK = mix(
    (B.MIDNIGHT_BLACK, 1.3),
    (B.P.CERULEAN_BLUE, 1.5),
    (B.PHTHALO_GREEN, 0.7),
    (B.SAP_GREEN, 0.4),
    (B.ALIZARIN, 0.1),
)


def little_evergreens():
    B.stage("little evergreens")
    r = np.random.default_rng(50)
    # (the fan, tapped on its corner: a small, stiff, full brush)
    fan = B.brushes.make(
        "round", 8, "hog", length=0.5, spread=0.3, name="fan brush, corner"
    )
    # (heights read off the painting: taller at the left end and at the right)
    tall = ref(
        (222, 40),
        (240, 60),
        (260, 40),
        (300, 45),
        (340, 32),
        (380, 35),
        (420, 40),
        (450, 55),
        (468, 85),
        (485, 60),
        (492, 30),
    )
    tx, th = np.array(tall).T
    for x in np.arange(222 * K, 492 * K, 3.5):
        h = float(np.interp(x, tx, th)) * r.uniform(0.6, 1.3)
        if r.random() < 0.15:
            h *= 1.8  # one standing taller than the rest
        h = min(h, 95 * K)
        x, top = x + r.normal(0, 1.5), WATER - h
        for y in np.arange(top, WATER, 3):  # tapped downward: wider as it goes
            hw = 1.0 + 0.11 * (y - top) * r.uniform(0.6, 1.4)
            st(
                [(x, y), (x + r.normal(0, 0.5), y + 4)],
                TREE_DARK,
                brush=fan.sized(max(3.0, 2 * hw)),
                amount=1 + 0.35 * hw,
                pressure=0.7,
                mixing=0.0,
                pickup=0.0,
            )
            # (and, with what is left, a little below the water line: the
            # paint the reflection is pulled from)
            if y > WATER - 0.6 * h:
                yy = 2 * WATER - y
                st(
                    [(x, yy), (x, yy - 4)],
                    TREE_DARK,
                    brush=fan.sized(max(3.0, 2 * hw)),
                    amount=0.25,
                    pressure=0.35,
                    mixing=0.4,
                    pickup=0.0,
                )
    for x in np.arange(222 * K, 492 * K, 10):  # and the dark at their feet
        st(
            [(x + r.normal(0, 3), WATER - r.uniform(4, 14))],
            TREE_DARK,
            width=r.uniform(18, 26),
            brush=fan,
            amount=3,
            pressure=0.5,
        )
    # reflections: grab the wet paint and pull straight down, then three hairs
    # and some air across
    # (the brush takes up the trees' wet paint: no new paint; where the trees
    # are taller, pulled a little further)
    for x in np.arange(222 * K, 490 * K, 22):
        depth = (40 + 25 * r.random()) * K
        pts, p = hand(
            [(x, WATER + 3), (x, WATER + depth)], [0.5, 0.4, 0.0], r=r, sway=1.0
        )
        st(pts, None, brush=Brush(B.TWO_INCH), angle=0, pressure=p, mixing=0.3)
    for y in np.arange(WATER + 6, WATER + 75 * K, 12):
        pts, p = hand(
            [(215 * K, y), (495 * K, y)], [0.0, 0.06, 0.06, 0.0], r=r, sway=1.0
        )
        st(pts, None, brush=Brush(B.TWO_INCH), angle=0, pressure=p)
    # the water's edge, cut with liquid white dulled with dark sienna
    for a, b in ((230, 300), (300, 390), (380, 485)):
        water_line(ref((a, 393), ((a + b) / 2, 393.5), (b, 393)), r, amount=0.2)
    for a, b, y in ((280, 330, 405), (360, 420, 412), (300, 350, 420)):
        water_line(ref((a, y), (b, y)), r, amount=0.08)


# liquid white with the least touch of dark sienna, to dull it down
WATER_LINE = mix((B.TITANIUM_WHITE, 3), (B.DARK_SIENNA, 0.1), (BLUE, 0.5))


def water_line(pts, r, amount=0.8):
    """The knife, a small roll of paint on its edge, pushed firmly into the
    canvas and cut straight across."""
    pts, p = hand(pts, [0.35], r=r, sway=0.6)
    st(
        pts,
        None,
        brush=Brush(B.EDGE_KNIFE).load(WATER_LINE, amount),
        angle=90,
        pressure=[2 * v for v in p],
    )


# ===========================================================================
# 6. Tall evergreens, leaf trees, the path
# ===========================================================================
TALL = [(22, 80, 1.4), (75, 28, 1.6), (157, 65, 1.4)]  # x, top, size
TREE_BASE = 340 * K
# midnight black, Prussian blue, Van Dyke brown, alizarin crimson, sap green
BIG_DARK = mix(
    (B.MIDNIGHT_BLACK, 1),
    (B.PRUSSIAN_BLUE, 1),
    (B.VAN_DYKE_BROWN, 0.5),
    (B.ALIZARIN, 0.2),
    (B.SAP_GREEN, 2),
    (B.PHTHALO_GREEN, 0.3),
)
# the dark under the leaf trees: warmer, with more sap green and Van Dyke
# brown, so the yellow-greens over it stay yellow
LEAF_DARK = mix(
    (B.MIDNIGHT_BLACK, 1),
    (B.VAN_DYKE_BROWN, 1),
    (B.SAP_GREEN, 2.5),
    (B.PRUSSIAN_BLUE, 0.3),
    (B.ALIZARIN, 0.2),
)
# sap green and cadmium yellow (with yellow ochre, Indian yellow, bright red),
# each list from dark to light
S, Y = B.SAP_GREEN, B.CADMIUM_YELLOW
GREENS = [
    mix((S, 2), (LEAF_DARK, 0.6)),
    mix((S, 2), (LEAF_DARK, 0.2)),
    S,
    mix((S, 3), (Y, 1)),
    mix((S, 2), (Y, 1)),
]
OCHRE = [S, mix((S, 1), (B.YELLOW_OCHRE, 1)), mix((B.YELLOW_OCHRE, 2), (S, 1))]
YELLOW = [
    mix((S, 2), (Y, 1)),
    mix((S, 1), (Y, 1)),
    mix((Y, 2), (S, 0.5)),
    mix((B.INDIAN_YELLOW, 1), (Y, 1)),
]
RED = [
    mix((B.BRIGHT_RED, 1), (B.YELLOW_OCHRE, 1), (S, 0.8)),
    mix((B.BRIGHT_RED, 1), (B.YELLOW_OCHRE, 1), (S, 0.3)),
    mix((B.YELLOW_OCHRE, 2), (B.BRIGHT_RED, 0.5)),
]
# leaf trees and bushes (x, base, width, height, colours), the farthest first
LEAF_TREES = [
    (625, 262, 60, 95, GREENS),
    (600, 370, 110, 190, GREENS),
    (588, 335, 96, 140, GREENS),
    (75, 310, 120, 120, GREENS),
    (180, 350, 80, 80, OCHRE),
    (515, 405, 70, 75, YELLOW),
    (35, 420, 100, 150, GREENS),
    (120, 395, 80, 90, GREENS),
    (440, 478, 90, 50, YELLOW),
    (590, 480, 120, 110, GREENS),
]
# the bushes pushed over the path, and the rest of the ground
FRONT_BUSHES = [
    (165, 410, 60, 45, YELLOW),
    (245, 435, 70, 50, RED),
    (310, 480, 70, 45, YELLOW),
    (360, 480, 90, 50, YELLOW),
    (110, 480, 110, 70, GREENS),
    (200, 480, 60, 40, GREENS),
    (30, 482, 90, 60, GREENS),
    (420, 484, 100, 50, GREENS),
    (480, 482, 90, 60, YELLOW),
    (520, 440, 80, 70, GREENS),
    (550, 484, 110, 70, GREENS),
    (640, 484, 110, 90, GREENS),
    (470, 430, 60, 50, OCHRE),
]


EVERGREEN = mix(
    (BIG_DARK, 1), (B.PHTHALO_GREEN, 0.4), (B.SAP_GREEN, 0.5), (B.P.CERULEAN_BLUE, 0.6)
)


def tall_evergreens():
    """The big brush loaded to a chisel edge with the dark (black, Prussian
    blue, Van Dyke brown, alizarin, sap green); a touch at the top, then the
    corner, back and forth, the bristles bent downward, wider as it goes;
    later, sap green on the chisel edge for the highlights. (bob_ross_style's
    evergreen, in these colours.)"""
    B.stage("tall evergreens")
    # (bob_ross_style's evergreens take their colours from its module)
    keep = B.EVERGREEN_DARK, B.HI_GREEN
    B.EVERGREEN_DARK = EVERGREEN
    B.HI_GREEN = mix((B.SAP_GREEN, 3), (B.CADMIUM_YELLOW, 0.4))
    try:
        for k, (x, top, size) in enumerate(TALL):
            # (twice over: his branches are full, the sky hardly shows through)
            for again in (0, 1, 2):
                B.evergreen(
                    x * K,
                    TREE_BASE,
                    TREE_BASE - top * K,
                    size,
                    seed=60 + k + 10 * again,
                )
    finally:
        B.EVERGREEN_DARK, B.HI_GREEN = keep


# where the land begins, down from the top (reference frame): all of it lies
# under the trees and bushes, around the lake
LAND_TOP = np.array(
    [
        (-10, 250),
        (200, 320),
        (232, 395),
        (250, 432),
        (470, 436),
        (486, 392),
        (530, 300),
        (590, 190),
        (650, 170),
    ]
)


def land():
    """The dark under the trees and bushes, blocked in with the big brush."""
    B.stage("land")
    r = np.random.default_rng(65)
    for y in np.arange(150 * K, H + 30, 22):
        for x in np.arange(-20, W + 20, 22):
            xr, yr = x / K, y / K
            if yr < np.interp(xr, *LAND_TOP.T):
                continue
            q = (x + r.normal(0, 6), y + r.normal(0, 6))
            st(
                [q],
                LEAF_DARK,
                width=r.uniform(32, 46),
                brush=B.TAPPER,
                amount=3,
                pressure=0.4,
                mixing=0.03,
                pickup=0.03,
            )


def trunks(x, base, h, seed=0):
    """A trunk or two (dark sienna and white), and sticks and twigs."""
    r = np.random.default_rng(seed)
    bark = mix((B.DARK_SIENNA, 2), (B.TITANIUM_WHITE, 1), (B.PRUSSIAN_BLUE, 0.2))
    st(
        [(x, base), (x + r.normal(0, 4), base - 0.6 * h)],
        bark,
        width=[7, 2],
        brush=B.LINER.sized(7),
        amount=6,
        pressure=0.5,
    )
    for _ in range(3):
        y = base - r.uniform(0.2, 0.6) * h
        side = r.choice((-1, 1))
        st(
            [(x, y), (x + side * r.uniform(10, 30), y - r.uniform(10, 30))],
            bark,
            width=2,
            brush=B.LINER,
            amount=2,
            pressure=0.3,
        )


def leaves(x, base, w, h, colours, seed=0):
    """Leaves tapped on with the corner of the one-inch brush (with a little
    Liquid White, so it sticks to the dark): a few little forms, the farther
    ones first and each lower one overlapping the one above, each tapped on
    its upper part only, thickest along its top towards the light, so the
    dark stays in the hollows under it."""
    r = np.random.default_rng(seed)
    n = max(3, min(6, int(w * h / 4000) + 3))
    for k in range(n):  # the forms, from the top of the tree down
        v = (k + r.uniform(0.2, 0.8)) / n
        fx = x + r.uniform(-0.3, 0.3) * w
        fy = base - h + v * h * 0.85
        size = r.uniform(0.28, 0.42) * min(w, h) + 10
        lit = 1.0 - 0.45 * v  # the lower forms take less of the light
        for _ in range(int(size**2 / 35)):
            # (the upper part of the form only, and most of all its top-right rim)
            b = (
                r.uniform(np.pi * 0.95, np.pi * 2.15)
                if r.random() < 0.85
                else r.uniform(0, np.pi)
            )
            s_ = r.uniform(0.35, 1.0) ** 0.5
            q = (
                fx + s_ * size * np.cos(b),
                fy + s_ * size * 0.7 * np.sin(b) + 0.15 * size,
            )
            up_form = (
                (fy - q[1]) / size
                + 0.4
                + 0.25 * np.cos(b + np.pi * 0.25)
                + 0.4 * (lit - 0.7)
                + r.normal(0, 0.15)
            )
            col = colours[int(np.clip(up_form * len(colours), 0, len(colours) - 1))]
            up = (
                q[0] + r.normal(0, 2),
                q[1] - r.uniform(4, 10),
            )  # (pushed upward: the bristles bend)
            st(
                [q, up],
                col,
                width=r.uniform(9, 15),
                brush=B.TAPPER,
                amount=1.6,
                pressure=[r.uniform(0.15, 0.28), 0.05],
                mixing=0.25,
                pickup=0.0,
            )


def block_in(x, base, w, h, seed=0):
    """The dark of a leaf tree, blocked in with the big brush: touched and
    pushed, so the bristles bend."""
    r = np.random.default_rng(seed)
    for _ in range(int(w * h / 400) + 6):
        a, rr = r.uniform(0, 2 * np.pi), np.sqrt(r.uniform(0, 0.9))
        q = (x + rr * 0.5 * w * np.cos(a), base - h / 2 + rr * 0.5 * h * np.sin(a))
        st(
            [q, (q[0], q[1] - 6)],
            LEAF_DARK,
            width=r.uniform(30, 44),
            brush=B.TAPPER,
            amount=3,
            pressure=[0.45, 0.1],
            mixing=0.03,
            pickup=0.03,
        )


def leaf_trees():
    B.stage("leaf trees and bushes")
    specs = [(x * K, b * K, w * K, h * K, c) for x, b, w, h, c in LEAF_TREES]
    for k, (x, b, w, h, _) in enumerate(specs):
        block_in(x, b, w, h, seed=70 + k)
    for k, (x, b, w, h, _) in enumerate(specs):
        if w > 100:
            trunks(x + w * 0.1, b, h, seed=80 + k)
    for k, spec in enumerate(specs):
        leaves(*spec, seed=90 + k)


def path():
    B.stage("path")
    r = np.random.default_rng(100)
    way = np.array(ref((95, 380), (140, 400), (180, 425), (215, 450), (245, 482)))
    xs = np.interp(np.linspace(0, 4, 40), np.arange(5), way[:, 0])
    ys = np.interp(np.linspace(0, 4, 40), np.arange(5), way[:, 1])
    for x, y in zip(xs, ys, strict=True):  # Van Dyke brown, tapped in
        for _ in range(3):
            st(
                [(x + r.normal(0, 12), y + r.normal(0, 6))],
                B.VAN_DYKE_BROWN,
                width=r.uniform(20, 30),
                brush=B.TAPPER,
                amount=3,
                pressure=0.4,
            )
    # brown, white and a touch of blue: grey, barely touching with the knife
    greys = [
        mix((B.VAN_DYKE_BROWN, 1), (B.TITANIUM_WHITE, w), (B.PRUSSIAN_BLUE, 0.3))
        for w in (1.5, 2.5, 3.5)
    ]
    for _ in range(30):  # rocks: touches along the way, each its own size
        i = int(r.integers(len(xs) - 1))
        tx, ty = xs[i + 1] - xs[i], ys[i + 1] - ys[i]
        n = np.hypot(tx, ty)
        a = (xs[i] + r.normal(0, 14), ys[i] + r.normal(0, 8))
        ln = r.uniform(12, 32)
        b = (
            a[0] + tx / n * ln + r.normal(0, 4),
            a[1] + ty / n * ln * 0.6 + r.normal(0, 3),
        )
        col = greys[int(r.integers(3))]
        st(
            [a, b],
            col,
            brush=B.SMALL_KNIFE.sized(r.uniform(14, 26)),
            amount=0.4,
            angle=70,
            pressure=r.uniform(0.05, 0.12),
            lift=0.0,
        )
    # and bushes pushed over it, so it goes back and hides
    for k, (x, b, w, h, c) in enumerate(FRONT_BUSHES):
        leaves(x * K, b * K, w * K, h * K, c, seed=110 + k)


# (lit with less gloss than bob_ross_style: the tapped paint of the little
# evergreens is thick, and glints in white specks where his shows none)
GLOSS = 0.2

STAGES = [
    B.liquid_white,
    sky,
    clouds,
    mountain,
    foothills,
    little_evergreens,
    tall_evergreens,
    land,
    leaf_trees,
    path,
]


def main(out, upto=None):
    t0 = time.time()
    for stage in STAGES[:upto]:
        stage()
    B.canvas.save(out, relief=B.RELIEF, gloss=GLOSS)
    print(f"wrote {out}: {B.N_STROKES[0]} strokes in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main(
        (
            sys.argv[1]
            if len(sys.argv) > 1
            else os.path.join(os.path.dirname(__file__), "output", "towering_peaks.png")
        ),
        int(sys.argv[2]) if len(sys.argv) > 2 else None,
    )

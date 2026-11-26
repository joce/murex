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
scaled to this canvas, 1200 x 900, about 0.5 mm per pixel for his 18 x 24
inch canvas. Every mark is a ``canvas.stroke(...)``; numpy only decides
where they go.

    python examples/huile/towering_peaks.py [output.png] [stages]
"""

import itertools
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from murex.huile import SKIM, Brush, Canvas, Paint, brushes, surfaces
from murex.huile import palette as P

W, H = 1200, 900
rng = np.random.default_rng(1983)


# ===========================================================================
# His palette (the nearest paints in huile.palette, and simple mixes), his
# brushes at the scale of this canvas (about 0.5 mm per pixel), and his canvas
# ===========================================================================
def mix(*parts):
    return Paint.mix(*parts)


TITANIUM_WHITE = P.TITANIUM_WHITE
PRUSSIAN_BLUE = mix((P.PHTHALO_BLUE, 3), (P.IVORY_BLACK, 1))
MIDNIGHT_BLACK = P.IVORY_BLACK
PHTHALO_GREEN = P.PHTHALO_GREEN
SAP_GREEN = P.SAP_GREEN
ALIZARIN = P.ALIZARIN_CRIMSON
VAN_DYKE_BROWN = mix((P.BURNT_UMBER, 3), (P.IVORY_BLACK, 1))
DARK_SIENNA = mix((P.BURNT_SIENNA, 2), (P.BURNT_UMBER, 1))
CADMIUM_YELLOW = P.CADMIUM_YELLOW
YELLOW_OCHRE = P.YELLOW_OCHRE
INDIAN_YELLOW = mix((P.CADMIUM_YELLOW, 2), (P.CADMIUM_ORANGE, 1))
BRIGHT_RED = P.CADMIUM_RED
# Liquid White: white thinned to a creamy fluid that stays wet and blends
LIQUID_WHITE = mix((TITANIUM_WHITE, 1), (P.MEDIUM, 1.2)).with_body(0.15)

# mixes he makes on the palette
# mixes he makes on the palette
MOUNTAIN_DARK = mix(
    (PRUSSIAN_BLUE, 2),
    (VAN_DYKE_BROWN, 1.5),
    (ALIZARIN, 1),
    (MIDNIGHT_BLACK, 0.3),
    (TITANIUM_WHITE, 1.6),
)

TWO_INCH = brushes.make(
    "flat", 100, "hog", length=0.75, capacity=1.6, name="two-inch brush"
)
FAN = brushes.make("fan", 48, "hog", length=0.7, clumps=7, name="fan brush")
MIST_BRUSH = brushes.MOP.sized(120).with_(softness=0.8, name="soft blender, for mist")
LINER = brushes.RIGGER.sized(3).with_(name="liner brush")
TAPPER = brushes.make(
    "round", 30, "hog", length=0.5, softness=0.25, name="brush corner, tapping"
)
EDGE_KNIFE = brushes.knife("straight", 40, flex=0.5, aspect=0.04, name="knife edge")
KNIFE = brushes.knife("straight", 70, flex=0.5, name="painting knife")
SMALL_KNIFE = brushes.knife("straight", 40, flex=0.5, name="small painting knife")

# pre-primed cotton canvas, as he used: an irregular weave, primed so it drinks no oil
CANVAS = surfaces.COTTON_DUCK.with_(
    absorbency=0.0,
    tooth=0.5,
    relief=1.0,
    scale=3.5,
    irregularity=0.35,
    ground="#f6f4ee",
    name="primed cotton canvas",
)
canvas = Canvas(W, H, surface=CANVAS, seed=1983)
N_STROKES = [0]


def st(pts, paint, width=None, brush=None, **kw):
    N_STROKES[0] += 1
    pts = [tuple(map(float, p)) for p in np.atleast_2d(pts)]
    return canvas.stroke(pts, paint=paint, width=width, brush=brush, **kw)


def loaded(tool, paint, amount, across=None):
    return Brush(tool).load(paint, amount, across=across)


def stage(name):
    print(
        f"[{time.strftime('%H:%M:%S')}] {name}  (strokes so far: {N_STROKES[0]})",
        flush=True,
    )


RELIEF = 0.25  # how the finished canvas is lit (and GLOSS, below)


def thin(paint):
    """Paint thinned to a soft, buttery consistency for wet-on-wet work."""
    return mix((paint, 1), (P.MEDIUM, 0.15)).with_body(0.45)


def liquid_white():
    """A thin, even film over the whole canvas: long horizontal passes with the
    two-inch brush, each loaded with just enough to cover it."""
    stage("liquid white")
    for y in np.arange(30, H + 50, 55):
        b = loaded(TWO_INCH, LIQUID_WHITE, (W + 160) / 100 * 0.6)
        st(
            [(-80, y), (W / 2, y + rng.normal(0, 2)), (W + 80, y)],
            None,
            brush=b,
            pressure=0.15,
        )


def criss_cross(
    brush, y0, y1, x0=-60, x1=W + 60, size=110, pressure=0.55, reload=None, step=0.45
):
    """Little X strokes across a band, as he scrubs in a sky or water,
    going back to the palette for a touch more paint after each one."""
    for y in np.arange(y0, y1, size * step):
        for x in np.arange(x0, x1, size * 0.8):
            jx, jy = rng.normal(0, size * 0.1, 2)
            d = size * 0.5
            st(
                [(x + jx - d, y + jy - d * 0.55), (x + jx + d, y + jy + d * 0.55)],
                None,
                brush=brush,
                pressure=pressure,
            )
            st(
                [(x + jx - d, y + jy + d * 0.55), (x + jx + d, y + jy - d * 0.55)],
                None,
                brush=brush,
                pressure=pressure,
            )
            if reload is not None:
                reload(brush, y)


def scrub_path(a, b, rr, advance, r):
    """Little scrubbing circles of radius ``rr``, travelling from a to b."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ln = np.linalg.norm(b - a)
    n = max(1, int(ln / advance))
    t = np.linspace(0, 2 * np.pi * n, 7 * n + 1)
    phase = r.uniform(0, 2 * np.pi)
    c = a + (b - a) * (t / t[-1])[:, None]
    return c + np.stack([rr * np.cos(t + phase), rr * 0.8 * np.sin(t + phase)], 1)


def scrub_along(pts, rr, advance, r):
    """Little scrubbing circles travelling along the line through ``pts``."""
    path = []
    for p, q in itertools.pairwise(pts):
        path.extend(scrub_path(p, q, rr, advance, r))
    return np.array(path)


def path_length(pts):
    return float(np.linalg.norm(np.diff(pts, axis=0), axis=1).sum())


def ridge_segments(ridge_ctrl, step):
    """Points along a ridge line every ``step`` px, with the ridge's slope
    there as a brush angle on the canvas (degrees, positive rising to the right)."""
    ctrl = np.asarray(ridge_ctrl, float)
    d = np.concatenate(
        [[0.0], np.cumsum(np.linalg.norm(np.diff(ctrl, axis=0), axis=1))]
    )
    out = []
    for t in np.arange(0.0, d[-1], step):
        i = min(int(np.searchsorted(d, t, side="right")) - 1, len(ctrl) - 2)
        (x0, y0), (x1, y1) = ctrl[i], ctrl[i + 1]
        f = (t - d[i]) / max(d[i + 1] - d[i], 1e-9)
        # (the canvas measures a fixed brush angle the other way round from image y)
        out.append(
            (
                x0 + f * (x1 - x0),
                y0 + f * (y1 - y0),
                -float(np.degrees(np.arctan2(y1 - y0, x1 - x0))),
            )
        )
    return out


K = W / 640  # the reference frame is 640 px wide


def hand(path, pressure, r=None, n=None, sway=4.0, wander=0.25):
    """A stroke as a hand lays it, along ``path`` (two points or more, a
    line or a curve): never quite on its line (a slight tilt, a gentle sway
    across it, ``sway`` px) and never evenly pressed (the pressure profile
    given rises and falls by up to ``wander``). ``sway=0, wander=0`` gives
    the stroke exactly as drawn. Returns the points and the pressures."""
    r = rng if r is None else r
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
BLUE = mix((P.CERULEAN_BLUE, 1), (P.ULTRAMARINE_BLUE, 1.0))
SKY = mix(
    (P.CERULEAN_BLUE, 1), (P.COBALT_BLUE, 1)
)  # (his phthalo blue in the sky: clean and bright)
WATER_BLUE = mix((P.CERULEAN_BLUE, 1), (PHTHALO_GREEN, 0.3), (P.ULTRAMARINE_BLUE, 0.2))
BAND = 285 * K  # the light band across the middle, where sky meets water


def sky():
    """A small amount of phthalo blue, tapped into the brush, and little
    criss-cross strokes from the top down: the brush runs out as it works
    down and the Liquid White lightens it. Then phthalo blue and a touch of
    phthalo green low down, pulled very gently from the outside in, so a
    light band stays across the middle. Then a clean brush blends it, still
    in criss-crosses, and lightly right across the bottom."""
    stage("sky")

    def reload(br, y):
        t = float(np.clip(y / BAND, 0, 1))
        br.load(thin(SKY), 1.8 * (1 - t) ** 1.5)

    b = loaded(TWO_INCH, thin(SKY), 1.8)
    criss_cross(b, -40, BAND - 40, size=120, reload=reload)

    # (each pull lifts off as it nears the middle, so the ends fade)
    for y in np.arange(BAND + 25, H + 40, 28):
        depth = float(np.clip((y - BAND) / (H - BAND), 0, 1))
        for side in (-1, 1):
            x0 = W / 2 + side * (W / 2 + 80)
            x1 = W / 2 - side * W * 0.1 * depth
            br = loaded(TWO_INCH, thin(WATER_BLUE), 5 + 12 * depth)
            pts, p = hand(
                [(x0, y), (x1, y)], [0.25 + 0.4 * depth, 0.05 + 0.2 * depth, 0.0]
            )
            st(pts, None, brush=br, angle=0, pressure=p)
    # (the brush laid broad, angle 0, as it travels across)
    for y in np.arange(BAND, H + 40, 11):
        pts, p = hand([(-80, y), (W + 80, y)], [0.3], sway=3)
        st(pts, None, brush=Brush(TWO_INCH), angle=0, pressure=p)

    # a clean brush: criss-crosses over the sky, then long, light strokes across
    criss_cross(Brush(TWO_INCH), -40, BAND, size=120, pressure=0.25)
    for y in np.arange(-10, BAND + 20, 14):
        pts, p = hand([(-80, y), (W + 80, y)], [0.22], sway=3)
        st(pts, None, brush=Brush(TWO_INCH), angle=0, pressure=p)


# ===========================================================================
# 2. Clouds: white with the least touch of bright red
# ===========================================================================
# white with the least touch of bright red: pinker on the crowns, where the
# light catches them, bluer down in the body
CLOUD_WHITE = mix(
    (TITANIUM_WHITE, 25), (BRIGHT_RED, 0.2), (ALIZARIN, 1.0), (P.ULTRAMARINE_BLUE, 1.4)
)
CROWN_WHITE = mix(
    (TITANIUM_WHITE, 35), (BRIGHT_RED, 1.6), (ALIZARIN, 1.8), (P.ULTRAMARINE_BLUE, 0.8)
)
# the masses of cloud (x0, x1, base, height, lumps, white) in the reference
# frame, the farthest first
CLOUDS = [
    (250, 430, 125, 105, 6, 0.08),
    (260, 440, 215, 140, 5, 0.15),
    (360, 660, 140, 175, 7, 0.15),
    (-20, 330, 190, 190, 8, 0.1),
]


def crown(x0, x1, base, height, lumps, r):
    """The top of a cloud: lumps of random widths heaped along x0..x1 (canvas
    px), ragged at small scale, falling to the base at both ends."""
    xs = np.arange(x0, x1, 2.0)
    u = (xs - x0) / (x1 - x0)
    env = np.sin(np.pi * u) ** 0.4  # (rounded, not peaked)
    top = np.zeros_like(xs)
    for _ in range(lumps):
        c, wd = r.uniform(0.05, 0.95), r.uniform(0.08, 0.25)
        top = np.maximum(top, r.uniform(0.45, 1.0) * np.exp(-(((u - c) / wd) ** 2)))
    rag = np.convolve(r.normal(0, 1, len(xs) + 6), np.ones(7) / 7, "valid")
    return xs, base - height * env * (0.35 + 0.65 * top) + 3.0 * rag


# a soft round brush: a dab of it is feathered all round
SOFT_ROUND = brushes.make(
    "round", 26, "squirrel", length=0.5, softness=0.85, name="soft round"
)


def cloud(x0, x1, base, height, lumps, white, seed=0):
    """A cloud the way he paints one: a brush loaded with a lot of white (and
    the least touch of bright red), touched along the top, where its crown
    will be, then little circular strokes on down into it as the brush runs
    out; then a clean, dry two-inch brush, tiny little circles to blend the
    bottom into the sky, higher and lighter each time, never at the top; then
    lifted, which fluffs it right up. The crown is an irregular line, lumps
    heaped along it, never a circle, scrubbed with a soft brush as wide as
    his, and its edge is barely touched with the clean brush, so it has no
    hard edge."""
    r = np.random.default_rng(seed)
    x0, x1, base, height = x0 * K, x1 * K, base * K, height * K
    xs, tops = crown(x0, x1, base, height, lumps, r)
    depth = base - tops
    w = 64  # (his one-inch brush, at this size)

    def scrub(line, paint, load, mixing):
        path = scrub_along(line, 14, 8.4, r)
        for k in range(0, len(path) - 2, 50):  # (reloaded every so often)
            part = path[k : k + 52]
            amount = load * path_length(part)
            brush = Brush(SOFT_ROUND.sized(w)).load(thin(paint), amount)
            st(part, None, brush=brush, pressure=0.3, mixing=mixing, pickup=0.05)

    top = np.flatnonzero(depth > max(0.5 * w, 0.6 * depth.max()))[::5]
    scrub(np.stack([xs[top], tops[top] + 0.35 * w], 1), CROWN_WHITE, white / 80, 0.15)
    for row, inset in enumerate(np.arange(0.8 * w, depth.max(), 0.4 * w)):  # body
        keep = np.flatnonzero(tops + inset < base - 0.3 * height)[::6]
        if len(keep) < 3:
            continue
        line = np.stack([xs[keep], tops[keep] + inset + r.normal(0, 3, len(keep))], 1)
        load = (1 - inset / depth.max()) ** 0.7
        scrub(line[::-1] if row % 2 else line, CLOUD_WHITE, white * load / 50, 0.4)
    blender = MIST_BRUSH.sized(70)
    w = blender.width
    for inset, p in ((0.0, 0.3), (0.45, 0.2)):  # the crown barely touched
        line = np.stack([xs[top], tops[top] + inset * w], 1)
        path = scrub_along(line, w * 0.15, w * 0.25, r)
        st(path, None, brush=Brush(blender), pressure=p, mixing=1.0, pickup=0.0)
    for k, (up, p) in enumerate(
        ((-0.25, 0.75), (0.0, 0.68), (0.25, 0.57), (0.5, 0.45))
    ):
        n = len(xs[::10])
        wave = np.convolve(r.normal(0, 0.12 * height, n + 4), np.ones(5) / 5, "valid")
        line = np.stack([xs[::10], base - up * height + wave], 1)  # (never level)
        path = scrub_along(line[:: -1 if k % 2 else 1], w * 0.2, w * 0.3, r)
        st(path, None, brush=Brush(blender), pressure=p, mixing=1.0, pickup=0.0)
    for x in np.arange(x0 + 10, x1 - 10, 24):
        y = base + r.normal(0, 5)
        up = r.uniform(0.3, 0.75) * height  # (each lifted off at its own height)
        pts, p = hand([(x, y + 10), (x, y - up)], [0.25, 0.02], r=r, sway=2)
        st(pts, None, brush=Brush(blender), pressure=p, mixing=1.0, pickup=0.0)


def clouds():
    stage("clouds")
    for seed, mass in enumerate(CLOUDS, start=1):
        cloud(*mass, seed=seed)


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
    ref((400, 52), (415, 80), (432, 120), (453, 168)),  # (ridges within the
    ref((343, 173), (400, 195), (460, 220), (527, 237)),  # faces, lit too)
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
    (TITANIUM_WHITE, 9),
    (ALIZARIN, 1.0),
    (P.ULTRAMARINE_BLUE, 1.2),
)
SHADE = mix(
    (TITANIUM_WHITE, 1.3),
    (P.ULTRAMARINE_BLUE, 1.1),
    (P.CERULEAN_BLUE, 0.4),
    (PRUSSIAN_BLUE, 0.15),
    (ALIZARIN, 0.1),
)
# black, Prussian blue, Van Dyke brown and alizarin crimson, a little white
ROCK = mix(
    (P.ULTRAMARINE_BLUE, 2),
    (P.CERULEAN_BLUE, 1),
    (PRUSSIAN_BLUE, 0.4),
    (VAN_DYKE_BROWN, 0.1),
    (ALIZARIN, 0.2),
    (MIDNIGHT_BLACK, 0.2),
    (TITANIUM_WHITE, 1.2),
)


def mountain():
    """Black, Prussian blue, Van Dyke brown and alizarin crimson, a small roll
    of paint on the knife, the shape cut in along the ridge; the excess
    scraped off with firm pressure, pushing the paint into the canvas; then
    the two-inch brush grabs it and pulls down, so it is lighter at the
    bottom. Snow with no pressure, the light from the right; shadows of white
    and Prussian blue on the other sides; mist tapped in at the base."""
    stage("mountain")
    knife_in(RIDGE, MOUNTAIN_BASE - 15 * K, ROCK, seed=3)
    r = np.random.default_rng(31)
    xs, ys = np.array(RIDGE).T
    # scrape it off, firmly, pushing the paint into the canvas; then grab it
    # with the two-inch brush and pull down (each stroke eased in and out)
    for x in np.arange(xs[0] + 10, xs[-1], 24):
        # (below the ridge all along the blade, so it never scrapes the sky)
        span = np.linspace(x - KNIFE.width / 2, x + KNIFE.width / 2, 9)
        top = float(np.interp(span, xs, ys).max()) + r.uniform(10, 40)
        pts, p = hand(
            [(x, top), (x, MOUNTAIN_BASE)], [0.0, 0.15, 0.15, 0.0], r=r, sway=2
        )
        st(pts, None, brush=Brush(KNIFE), angle=0, pressure=p)
    for x in np.arange(xs[0] + 10, xs[-1], 20):
        top = float(np.interp(x, xs, ys)) + r.uniform(30, 90)
        if MOUNTAIN_BASE - top < 40:
            continue
        pts, p = hand(
            [(x, top), (x, MOUNTAIN_BASE)], [0.0, 0.15, 0.1, 0.0], r=r, sway=2
        )
        st(pts, None, brush=Brush(TWO_INCH), angle=0, pressure=p)
    for k, line in enumerate(SHADOW):
        snow(line, SHADE, seed=70 + k, rows=5)
    for k, line in enumerate(LIT):
        snow(line, SNOW, seed=80 + k, rows=2)
    # mist: the base tapped and lifted, then blended with a clean brush
    r = np.random.default_rng(32)
    haze = mix((TITANIUM_WHITE, 6), (P.ULTRAMARINE_BLUE, 0.5), (ALIZARIN, 0.15))
    blender = MIST_BRUSH.sized(110)
    for y in np.arange(240 * K, 300 * K, 12):
        f = ((y - 240 * K) / (60 * K)) ** 1.5
        line = [(x, y + r.normal(0, 5)) for x in np.arange(130 * K, W + 60, 60)]
        path = scrub_along(line, 20, 24, r)
        brush = Brush(blender).load(haze, (0.45 * f + 0.03) * path_length(path) / 600)
        st(path, None, brush=brush, pressure=0.05 + 0.25 * f**0.5, mixing=0.5)


def knife_in(ridge, base, dark, seed=0):
    """The dark cut in with the knife, a small roll of paint on its edge:
    set down along the ridge line, just under it, and pulled square to
    itself into the mountain, then turned to come straight down."""
    r = np.random.default_rng(seed)
    segs = ridge_segments(ridge, 22)
    lower = mix((dark, 1), (TITANIUM_WHITE, 4))
    for j, (x, y, slope) in enumerate(segs):
        if base - y < 8:
            continue
        ln = (base - y) * r.uniform(
            0.75, 0.92
        )  # (all the way down: the dark covers the mountain)
        k = (
            Brush(KNIFE)
            .load(dark, 0.25 * ln / KNIFE.width)
            .load(lower, 0.2 * ln / KNIFE.width, depth="heel")
        )
        lo, hi = max(0, j - 2), min(len(segs) - 1, j + 2)
        bend = abs(segs[hi][2] - segs[lo][2])
        width = KNIFE.width * (1.0 if bend < 25 else 0.45)
        nx, ny = np.sin(np.radians(slope)), np.cos(np.radians(slope))
        inset = 0.5 * KNIFE.aspect * width + (3 if bend >= 25 else 0)
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


def snow(line, colour, seed=0, blade=None, rows=1):
    """As he lays it: the knife with a small roll of paint on its edge, held
    across the ridge with its tip just under it, and pulled down along the
    ridge with no pressure at all (``SKIM``), a short way, then again a
    little further down, each pull reaching its own way into the face; on a
    long face, again lower down, reaching less. The paint breaks along the
    pull, so the snow streaks down the slope and its lower edge frays."""
    r = np.random.default_rng(seed)
    blade = blade or KNIFE
    pts = np.asarray(line, float)
    along = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    total = along[-1]
    for row in range(rows):
        d = r.uniform(0, 10) + row * 15
        while d < total - 10:
            ln = min(60 * r.uniform(0.6, 1.4), total - d)
            ds = np.linspace(d, d + ln, 6)
            x, y = (np.interp(ds, along, pts[:, k]) for k in (0, 1))
            tx, ty = x[-1] - x[0], y[-1] - y[0]
            nx, ny = np.array([-ty, tx]) / np.hypot(tx, ty)
            if ny < 0:
                nx, ny = -nx, -ny  # (into the mountain, below the ridge)
            reach = blade.width * r.uniform(0.3, 0.7) * max(0.4, 1 - 0.12 * row)
            off = 3 + row * blade.width * 0.55 + reach / 2
            path = [
                (xi + nx * off + r.normal(0, 1), yi + ny * off + r.normal(0, 1))
                for xi, yi in zip(x, y, strict=True)
            ]
            if max(q[1] for q in path) <= MOUNTAIN_BASE - 10:
                st(
                    path,
                    None,
                    brush=Brush(blade).load(colour, 4.0),
                    width=reach,
                    angle=30 * r.uniform(0.5, 1.5),
                    follow_path=True,
                    pressure=[0.0, SKIM, SKIM, SKIM, SKIM, 0.0],
                    lift=0.0,
                )
            d += ln * r.uniform(0.4, 0.8)


def mist(line, height, seed=0):
    """A clean, dry brush tapped along the base, then lifted gently upward:
    the tap marks go and the base melts into a soft mist."""
    r = np.random.default_rng(seed)
    brush = MIST_BRUSH.sized(110)
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
OVAL = brushes.make("filbert", 34, "hog", length=0.6, capacity=1.4, name="oval brush")
# the mountain colour, the least touch of sap green, and white
# (his blues as huile's cerulean and ultramarine: Prussian blue greys here)
FOOT = mix(
    (MOUNTAIN_DARK, 1),
    (P.CERULEAN_BLUE, 0.8),
    (P.ULTRAMARINE_BLUE, 1.0),
    (SAP_GREEN, 0.05),
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
    stage("foothills")
    for k, (top, depth, white) in enumerate(HILLS):
        foothill(top, depth, mix((FOOT, 1), (TITANIUM_WHITE, white)), seed=40 + k)


# ===========================================================================
# 5. Little evergreens at the water, and their reflections
# ===========================================================================
WATER = 392 * K
TREE_DARK = mix(
    (MIDNIGHT_BLACK, 1.3),
    (P.CERULEAN_BLUE, 1.5),
    (PHTHALO_GREEN, 0.7),
    (SAP_GREEN, 0.4),
    (ALIZARIN, 0.1),
)


def little_evergreens():
    stage("little evergreens")
    r = np.random.default_rng(50)
    # (the fan, tapped on its corner: a small, stiff, full brush)
    fan = brushes.make(
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
        st(pts, None, brush=Brush(TWO_INCH), angle=0, pressure=p, mixing=0.3)
    for y in np.arange(WATER + 6, WATER + 75 * K, 12):
        pts, p = hand(
            [(215 * K, y), (495 * K, y)], [0.0, 0.06, 0.06, 0.0], r=r, sway=1.0
        )
        st(pts, None, brush=Brush(TWO_INCH), angle=0, pressure=p)
    # the water's edge, cut with liquid white dulled with dark sienna
    for a, b in ((230, 300), (300, 390), (380, 485)):
        water_line(ref((a, 393), ((a + b) / 2, 393.5), (b, 393)), r, amount=0.2)
    for a, b, y in ((280, 330, 405), (360, 420, 412), (300, 350, 420)):
        water_line(ref((a, y), (b, y)), r, amount=0.08)


# liquid white with the least touch of dark sienna, to dull it down
WATER_LINE = mix((TITANIUM_WHITE, 3), (DARK_SIENNA, 0.1), (BLUE, 0.5))


def water_line(pts, r, amount=0.8):
    """The knife, a small roll of paint on its edge, pushed firmly into the
    canvas and cut straight across."""
    pts, p = hand(pts, [0.35], r=r, sway=0.6)
    st(
        pts,
        None,
        brush=Brush(EDGE_KNIFE).load(WATER_LINE, amount),
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
    (MIDNIGHT_BLACK, 1),
    (PRUSSIAN_BLUE, 1),
    (VAN_DYKE_BROWN, 0.5),
    (ALIZARIN, 0.2),
    (SAP_GREEN, 2),
    (PHTHALO_GREEN, 0.3),
)
# the dark under the leaf trees: warmer, with more sap green and Van Dyke
# brown, so the yellow-greens over it stay yellow
LEAF_DARK = mix(
    (MIDNIGHT_BLACK, 1),
    (VAN_DYKE_BROWN, 1),
    (SAP_GREEN, 2.5),
    (PRUSSIAN_BLUE, 0.3),
    (ALIZARIN, 0.2),
)
# sap green and cadmium yellow (with yellow ochre, Indian yellow, bright red),
# each list from dark to light
S, Y = SAP_GREEN, CADMIUM_YELLOW
GREENS = [
    mix((S, 2), (LEAF_DARK, 1)),
    mix((S, 3), (LEAF_DARK, 0.5), (YELLOW_OCHRE, 0.5)),
    S,
    mix((S, 3), (Y, 0.25)),
    mix((S, 2), (Y, 0.35)),
]
OCHRE = [S, mix((S, 1), (YELLOW_OCHRE, 1)), mix((YELLOW_OCHRE, 2), (S, 1))]
YELLOW = [
    mix((S, 2), (Y, 1), (LEAF_DARK, 0.3)),
    mix((S, 1.5), (Y, 1), (YELLOW_OCHRE, 0.3)),
    mix((Y, 2), (S, 1), (YELLOW_OCHRE, 0.5)),
    mix((Y, 2), (YELLOW_OCHRE, 1), (S, 0.5)),
]
RED = [
    mix((BRIGHT_RED, 1), (YELLOW_OCHRE, 1), (S, 0.5), (LEAF_DARK, 0.2)),
    mix((BRIGHT_RED, 2), (YELLOW_OCHRE, 1), (S, 0.3)),
    mix((BRIGHT_RED, 1), (YELLOW_OCHRE, 1), (Y, 0.3)),
]
# leaf trees and bushes (x, base, width, height, colours), the farthest first
LEAF_TREES = [
    (625, 262, 60, 95, GREENS),
    (600, 370, 110, 190, GREENS),
    (588, 335, 96, 140, GREENS),
    (85, 335, 120, 100, GREENS),
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
    (30, 482, 90, 60, GREENS),
    (420, 484, 100, 50, GREENS),
    (480, 482, 90, 60, YELLOW),
    (520, 440, 80, 70, GREENS),
    (550, 484, 110, 70, GREENS),
    (640, 484, 110, 90, GREENS),
    (470, 430, 60, 50, OCHRE),
]


EVERGREEN = mix((BIG_DARK, 1), (PHTHALO_GREEN, 0.3), (SAP_GREEN, 0.8))
# sap green on the chisel edge, for the highlights
EVERGREEN_HI = [
    mix((SAP_GREEN, 3), (EVERGREEN, 1)),
    mix((SAP_GREEN, 3), (CADMIUM_YELLOW, 0.35), (EVERGREEN, 0.3)),
]


# the corner of the big brush, loaded to a chisel edge
CORNER = brushes.make(
    "round",
    12,
    "hog",
    length=0.6,
    spread=0.5,
    softness=0.6,
    bristles=1.0,
    name="big brush, corner",
)


def branch(x, y, side, span, droop, w, r):
    """One arm: a few short touches of the corner, out from across the trunk,
    each overlapping the last, the tip bent down."""
    u, a1 = -0.15, -0.15
    while a1 < 1.0:  # (until a touch reaches the tip)
        a0, a1 = u, min(1.0, u + r.uniform(0.3, 0.55))
        p0 = (x + side * span * a0, y + droop * max(a0, 0) ** 2.5 + r.normal(0, 1))
        p1 = (x + side * span * a1, y + droop * a1**2.5 + r.normal(0, 1.5))
        st(
            [p0, p1],
            EVERGREEN,
            width=[w * (1 - 0.3 * max(a0, 0)), w * (1 - 0.3 * a1)],
            brush=CORNER.sized(max(5.0, w)),
            angle=0,
            amount=3 + 0.15 * span,
            pressure=[0.6, 0.4],
            mixing=0.0,
            pickup=0.0,
            streaks=0.0,
        )
        u = a1 - r.uniform(0.05, 0.15)


def conifer(x, base, h, seed=0):
    """An evergreen as he paints one: the big brush full of paint, pulled to a
    chisel edge; a touch at the top; then just the corner, back and forth,
    left and right, down the tree, the bristles pressed and bent downward:
    tufts of little arms, each side out of step with the other, the sky
    showing between them near the top, wider and closer as it comes down;
    then sap green on the chisel edge, lightly, on the tops of the tufts,
    more on the side of the light."""
    r = np.random.default_rng(seed)
    top = base - h
    spine = [(x + r.normal(0, 1), top + f * h) for f in np.linspace(0, 1, 8)]
    st(
        spine,
        EVERGREEN,
        width=[1.0, 0.03 * h, 0.06 * h],
        brush=CORNER,
        angle=90,
        amount=2 + 0.05 * h,
        pressure=[0.3, 0.6],
    )
    tufts = []
    for side in (-1, 1):
        y = top + (0.04 if side < 0 else 0.07) * h * r.uniform(0.7, 1.3)
        while y < base:
            t = (y - top) / h
            thick = (0.015 + 0.05 * t) * h * r.uniform(0.6, 1.4)
            span = (4 + 0.28 * h * t**0.55) * r.uniform(0.45, 1.15)
            n = max(1, int(thick / 5))
            arms = []
            for k in range(n):  # the longest at the bottom of the tuft
                f = k / (n - 1) if n > 1 else 1.0
                yy = y + f * thick + r.normal(0, 1.5)
                s_ = span * (0.6 + 0.4 * f) * r.uniform(0.85, 1.1)
                w = (10 + 24 * t) * r.uniform(0.8, 1.2)
                branch(x, yy, side, s_, s_ * 0.18 * r.uniform(0.5, 1.5), w, r)
                arms.append((side, yy, s_, w))
            tufts.append(arms)
            y += thick + 0.07 * h * max(0.0, 0.6 - t) ** 1.5 * r.uniform(0.4, 1.6)
    for arms in tufts:
        for side, y, span, w in arms[:2]:  # (the top of the tuft)
            if r.random() > (0.95 if side > 0 else 0.6):
                continue
            u0, u1 = r.uniform(0.15, 0.4), r.uniform(0.7, 0.9)
            p0 = (x + side * span * u0, y - w * 0.3)
            p1 = (x + side * span * u1, y + span * 0.18 * u1**2.5 - w * 0.2)
            st(
                [p0, p1],
                EVERGREEN_HI[int(r.random() < 0.3)],
                width=[w * 0.8, w * 0.3],
                brush=SOFT_ROUND.sized(max(6.0, w)),
                angle=0,
                amount=0.5,
                pressure=[0.3, 0.12],
                mixing=0.4,
                pickup=0.0,
            )


def tall_evergreens():
    stage("tall evergreens")
    for k, (x, top, _) in enumerate(TALL):
        conifer(x * K, TREE_BASE, TREE_BASE - top * K, seed=60 + k)


# where the land begins, down from the top (reference frame): all of it lies
# under the trees and bushes, around the lake
LAND_TOP = np.array(
    [
        (-10, 280),
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
    stage("land")
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
                brush=TAPPER,
                amount=8,
                pressure=0.4,
                mixing=0.03,
                pickup=0.03,
            )


def trunks(x, base, h, seed=0):
    """A trunk or two (dark sienna and white), and sticks and twigs."""
    r = np.random.default_rng(seed)
    bark = mix((DARK_SIENNA, 2), (TITANIUM_WHITE, 1), (PRUSSIAN_BLUE, 0.2))
    st(
        [(x, base), (x + r.normal(0, 4), base - 0.6 * h)],
        bark,
        width=[7, 2],
        brush=LINER.sized(7),
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
            brush=LINER,
            amount=2,
            pressure=0.3,
        )


# the corner of the one-inch brush, tapped: lightly, only the tips of its
# longest bristles touch, and the leaves break into little clusters
LEAF_TAP = brushes.make(
    "round", 22, "hog", length=0.5, capacity=1.6, name="one-inch brush corner, tapping"
)


def leaves(x, base, w, h, colours, seed=0):
    """Leaves tapped on with the one-inch brush (with a little Liquid White,
    so it sticks to the dark): a few rounded forms, each lower one
    overlapping the one above; the darker colours first over all of them,
    then the lighter ones higher up on each form and towards the light,
    where it falls, so the dark stays in the hollows and never comes back
    over a light. Tapped lightly, the brush prints the tips of its bristles,
    as his does."""
    r = np.random.default_rng(seed)
    n = max(3, min(6, int(w * h / 4000) + 3))
    forms = []
    for k in range(n):  # from the top of the tree down
        v = (k + r.uniform(0.2, 0.8)) / n
        size = r.uniform(0.8, 1.2) * 0.5 * min(w, h) + 10
        fy = base - h + 0.6 * size + v * (h - 0.6 * size) * 0.85
        forms.append((x + r.uniform(-0.3, 0.3) * w, fy, size))
    for c, col in enumerate(colours):
        frac = c / max(1, len(colours) - 1)  # 0 dark .. 1 light
        for fx, fy, size in forms:
            m = int(2.0 * size**2 / 110 * (0.9 + 0.1 * frac))
            pts = []
            for _ in range(m):
                if r.random() < 0.6 + 0.35 * frac:  # (the lighter, the higher)
                    b = r.uniform(
                        np.pi * (1 - 0.1 * (1 - frac)), np.pi * (2 + 0.1 * (1 - frac))
                    )
                else:
                    b = r.uniform(0, 2 * np.pi)
                # (thinning out past the form's edge, not stopping at it)
                s_ = min(1.1, abs(r.normal(0, 0.5))) * (1 - 0.2 * frac)
                pts.append(
                    (
                        fx + s_ * size * np.cos(b) + 0.15 * size * frac,
                        fy + s_ * size * 0.7 * np.sin(b) + 0.2 * size * (1 - frac),
                    )
                )
            pressure = 1.3 * r.uniform(0.18, 0.32, len(pts)) * (1.1 - 0.3 * frac)
            canvas.stipple(
                pts,
                col,
                amount=5 + 0.03 * m,
                brush=LEAF_TAP.sized(r.uniform(16, 24)),
                pressure=list(pressure),
                mixing=0.05,
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
            brush=TAPPER,
            amount=3,
            pressure=[0.45, 0.1],
            mixing=0.03,
            pickup=0.03,
        )


def leaf_trees():
    stage("leaf trees and bushes")
    specs = [(x * K, b * K, w * K, h * K, c) for x, b, w, h, c in LEAF_TREES]
    for k, (x, b, w, h, _) in enumerate(specs):
        block_in(x, b, w, h, seed=70 + k)
    for k, (x, b, w, h, _) in enumerate(specs):
        if w > 100:
            trunks(x + w * 0.1, b, h, seed=80 + k)
    for k, spec in enumerate(specs):
        leaves(*spec, seed=90 + k)


def path():
    """Van Dyke brown with the knife, a band laid down the way to the water;
    then brown, white and a touch of blue, grey, very lightly, barely
    touching, short strokes across: the stones; and bushes pushed over it,
    so it goes back and hides."""
    stage("path")
    r = np.random.default_rng(100)
    way = np.array(ref((95, 372), (140, 395), (180, 422), (215, 448), (250, 482)))
    for i in range(len(way) - 1):
        (xa, ya), (xb, yb) = way[i], way[i + 1]
        for off in (-40, -26, -12, 2, 16, 30):
            a, b = (xa + off * 0.6, ya + off * 0.3), (xb + off * 0.6, yb + off * 0.3)
            pts, p = hand([a, b], [0.6], r=r, sway=2)
            st(
                pts,
                VAN_DYKE_BROWN,
                brush=KNIFE.sized(40),
                amount=4,
                angle=90,
                pressure=p,
            )
    greys = [
        mix((VAN_DYKE_BROWN, 0.5), (TITANIUM_WHITE, w), (PRUSSIAN_BLUE, 0.5))
        for w in (1.0, 1.6, 2.4)
    ]
    us = np.linspace(0, len(way) - 1, 120)
    xs = np.interp(us, np.arange(len(way)), way[:, 0])
    ys = np.interp(us, np.arange(len(way)), way[:, 1])
    for _ in range(260):  # (each stone its own size)
        i = int(r.integers(len(xs)))
        a = (xs[i] + r.normal(0, 30), ys[i] + r.normal(0, 14))
        ln = r.uniform(18, 50)
        st(
            [a, (a[0] + ln, a[1] + r.normal(0, 1.5))],
            greys[int(r.integers(3))],
            brush=SMALL_KNIFE.sized(r.uniform(4, 8)),
            amount=1.5,
            angle=0,
            pressure=r.uniform(0.45, 0.6),
            lift=0.0,
        )
    for k, (x, b, w, h, c) in enumerate(FRONT_BUSHES):
        leaves(x * K, b * K, w * K, h * K, c, seed=110 + k)


# the letters of "Claude", in a hand: x across, y down, 1 the height; each a
# stroke of the liner, the brush lifted between
SIGNATURE = [
    [
        (0.58, 0.18),
        (0.4, 0.02),
        (0.15, 0.12),
        (0.02, 0.45),
        (0.1, 0.82),
        (0.35, 0.98),
        (0.6, 0.86),
    ],
    [(0.8, 0.0), (0.76, 0.5), (0.76, 0.95), (0.86, 1.0)],
    [
        (1.2, 0.6),
        (1.07, 0.5),
        (0.95, 0.62),
        (0.94, 0.86),
        (1.04, 1.0),
        (1.17, 0.92),
        (1.22, 0.72),
    ],
    [(1.23, 0.5), (1.22, 0.9), (1.29, 1.0)],
    [(1.4, 0.5), (1.39, 0.85), (1.47, 1.0), (1.6, 0.9), (1.65, 0.7)],
    [(1.66, 0.5), (1.66, 0.92), (1.72, 1.0)],
    [
        (2.02, 0.6),
        (1.9, 0.5),
        (1.79, 0.62),
        (1.78, 0.86),
        (1.87, 1.0),
        (2.0, 0.92),
        (2.04, 0.75),
    ],
    [(2.06, 0.0), (2.04, 0.9), (2.1, 1.0)],
    [
        (2.2, 0.78),
        (2.38, 0.72),
        (2.35, 0.53),
        (2.23, 0.52),
        (2.18, 0.75),
        (2.26, 0.97),
        (2.44, 0.9),
    ],
]


def sign():
    """The liner brush, a little paint thinned on it, bright red: signed in
    the corner where he signs his."""
    stage("signature")
    r = np.random.default_rng(1983)
    red = thin(mix((BRIGHT_RED, 3), (ALIZARIN, 1)))
    x0, y0, size = 16 * K, 436 * K, 15 * K
    for letter in SIGNATURE:
        pts = np.array(letter) * size + (x0, y0)
        along = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
        s = np.linspace(0, along[-1], max(8, int(along[-1] / 2)))
        line = np.stack([np.interp(s, along, pts[:, k]) for k in (0, 1)], 1)
        path, p = hand(line, [0.35, 0.5, 0.45, 0.3], r=r, sway=0.4, wander=0.2)
        st(path, red, width=2.2, brush=LINER, amount=0.6 * len(path), pressure=p)


# (little gloss: the tapped paint of the little evergreens is thick, and
# glints in white specks where his shows none)
GLOSS = 0.2

STAGES = [
    liquid_white,
    sky,
    clouds,
    mountain,
    foothills,
    little_evergreens,
    tall_evergreens,
    land,
    leaf_trees,
    path,
    sign,
]


def main(out, upto=None):
    t0 = time.time()
    for stage in STAGES[:upto]:
        stage()
    canvas.save(out, relief=RELIEF, gloss=GLOSS)
    print(f"wrote {out}: {N_STROKES[0]} strokes in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main(
        (
            sys.argv[1]
            if len(sys.argv) > 1
            else os.path.join(os.path.dirname(__file__), "output", "towering_peaks.png")
        ),
        int(sys.argv[2]) if len(sys.argv) > 2 else None,
    )

"""A red fox in pastel pencils on black paper: a portrait of the head and
the chest, three-quarters to the left, the fur drawn hair by hair.

Run from the repository root: ``python examples/fusain/fox.py``. Writes
``examples/fusain/output/fox.png``.

The fox is a solid model (``fox_model.py``) lit from the upper left, with
the colour of its coat and the way its fur lies at every place. The paper
is black and is left for the deepest shadows. The pencils go on as for a
pastel pencil portrait. First the tooth is covered with the pencils held
on their side, rust and orange over the orange, grey in the shadows of the
white and cream in its light. Then the point, in passes of short strokes
along the lie of the fur, as long as the fur is there: rust, orange and
gold, grey, cream and white, from the darks to the lights, dark strokes
among the orange in the shadows; then single hairs, longer and firmer.
Where the fur is long (the ruff, the chest, the shoulders) it is drawn in
locks, a few hairs meeting at a tip, each parted from the next by a dark
line. Then what makes the face: the black of the ear tips and rims, the
tear lines, the eyes (amber irises, the pupils left black, a white touch
of light in each), the nose (glossy black leather, so a dark grey rimmed
with light) and the lips; the whiskers in white last, and loose hairs
breaking the outline of the ruff and the ears. The chest fades into the
paper at the foot of the sheet.
"""

# cspell:words fox's

from __future__ import annotations

from pathlib import Path

import fox_model as fm
import numpy as np

from murex.fusain import Sheet, Stick, papers, pastels

#: The pastel pencils, by the colour of their cores.
RUST, ORANGE, GOLD = "#8a3a12", "#c8641e", "#e9a650"
GREY, CREAM, WHITE = "#6f6b66", "#e6d9c0", "#f6f3ec"
DARK, BLACK, AMBER = "#2c1a10", "#141312", "#d99a2c"
NOSE_GREY, PARTING = "#4a4642", "#4d4a47"

#: How much of the drawing is laid, row by row: the chest fades into the
#: paper towards the foot of the sheet.
FADE = (
    np.clip((1010.0 - np.mgrid[0 : fm.HEIGHT, 0 : fm.WIDTH][0]) / 230.0, 0.0, 1.0)
    ** 1.4
)


def pencil(color, width=2.6):
    return Stick(pastels.pencil(color), width=width)


def fur_paths(model, points, rng, scale=1.0, bend=0.25):
    """A stroke from each of ``points`` along the lie of the fur, as long
    as the fur is there (times ``scale``): five points following the flow,
    each turned a little at random as a hair is."""
    n = len(points)
    length = model.at(model.length, points) * scale * rng.uniform(0.7, 1.3, n)
    paths = np.empty((n, 5, 2))
    paths[:, 0] = points
    turn = rng.normal(0.0, bend, n)
    for k in range(1, 5):
        fx = model.at(model.flow[0], paths[:, k - 1])
        fy = model.at(model.flow[1], paths[:, k - 1])
        c, s = np.cos(turn * k / 4), np.sin(turn * k / 4)
        step = (length / 4)[:, None] * np.stack([fx * c - fy * s, fx * s + fy * c], 1)
        paths[:, k] = paths[:, k - 1] + step
    return paths


def scatter(model, rng, spacing, where):
    """Points over the fox, about ``spacing`` apart, where ``where`` holds."""
    ys, xs = np.mgrid[0 : fm.HEIGHT : spacing, 0 : fm.WIDTH : spacing].astype(float)
    pts = np.stack([xs.ravel(), ys.ravel()], 1) + rng.uniform(0, spacing, (xs.size, 2))
    keep = model.at(where, pts)
    return pts[keep]


def lay(
    sheet, model, rng, color, want, spacing, scale=1.0, width=2.6, firm=0.7, tilt=0.0
):
    """A pass of one pencil over the fur: a stroke from about every
    ``spacing`` px where ``want`` (0 to 1) asks for it, as firm as it asks,
    held ``tilt`` over on its side."""
    want = want * FADE * (model.part == fm.FUR) * ~model.eyes
    pts = scatter(model, rng, spacing, want > 0.04)
    if len(pts) == 0:
        return
    # (fewer strokes where less is wanted: a light tone is a sparser one)
    w = model.at(want, pts)
    keep = rng.uniform(0, 1, len(w)) < 0.35 + 0.65 * w
    pts, w = pts[keep], w[keep]
    stick = pencil(color, width)
    for path, p in zip(fur_paths(model, pts, rng, scale), w, strict=True):
        sheet.stroke(
            [tuple(q) for q in path],
            stick,
            lambda u, p=p: firm * p * np.sin(np.pi * (0.1 + 0.85 * u)) ** 0.5,
            tilt=tilt,
        )


def fur(sheet, model, rng):
    """The coat, in passes from the darks to the lights."""
    light = model.light
    white = model.white + model.inner
    orange = np.clip(1.0 - white - model.black, 0.0, 1.0)
    # first the tooth is covered with the pencils held on their side, the
    # colours of the coat in its light and its shadow
    # (the white fur pressed harder: on black paper the tooth must be filled
    # for it to read white)
    under = (
        (RUST, orange * np.clip(0.1 + 0.9 * light, 0, 1), 0.6),
        (GREY, white * np.clip(1.0 - 0.9 * light, 0.2, 1), 0.9),
        (ORANGE, orange * np.clip(1.5 * light - 0.2, 0, 1), 0.6),
        (CREAM, white * np.clip(1.8 * light - 0.1, 0, 1), 0.95),
    )
    for color, want, firm in under:
        lay(sheet, model, rng, color, want, 6, 1.0, firm=firm, tilt=0.55)
    # then with the point, along the fur
    passes = (
        # (pencil, where and how firm, spacing, length)
        (RUST, orange * np.clip(0.1 + 0.9 * light, 0, 1), 5, 1.0),
        (GREY, white * np.clip(0.2 + 0.9 * light, 0, 1), 5, 1.0),
        (ORANGE, orange * np.clip(1.5 * light - 0.2, 0, 1), 4.5, 1.0),
        (CREAM, white * np.clip(1.4 * light - 0.15, 0, 1), 4.5, 1.0),
        (GOLD, orange * np.clip(2.0 * (light - 0.42), 0, 1), 5, 0.9),
        (WHITE, white * np.clip(2.0 * (light - 0.35), 0, 1), 5, 0.9),
        # dark hairs among the orange in the shadows
        (DARK, orange * np.clip(0.7 - light, 0, 1), 7, 1.1),
    )
    for color, want, spacing, scale in passes:
        lay(sheet, model, rng, color, want, spacing, scale)
    # the black markings
    lay(sheet, model, rng, BLACK, model.black, 4, 0.8, firm=0.9)
    # last, single hairs drawn with a sharp point, longer and firmer: light
    # ones where the light falls, dark ones parting the fur in its shadows
    hairs = (
        (GOLD, orange * np.clip(1.6 * (light - 0.3), 0, 1), 10),
        (WHITE, white * np.clip(1.6 * (light - 0.2), 0, 1), 10),
        (DARK, orange * np.clip(1.2 * (0.55 - light), 0, 1), 11),
        (GREY, white * np.clip(1.4 * (0.6 - light), 0, 1), 11),
    )
    for color, want, spacing in hairs:
        lay(sheet, model, rng, color, want, spacing, 1.5, width=1.7, firm=0.95)


def locks(sheet, model, rng):
    """Where the fur is long (the ruff, the chest, the shoulders), clumps of
    it: a few hairs from roots spread across the lie of the fur, meeting at
    a tip, each lock lit on its top and parted from the next by a dark
    line on its shadow side."""
    where = (model.part == fm.FUR) & (model.length > 20) & (FADE > 0.15)
    pts = scatter(model, rng, 14, where & ~model.eyes)
    middles = fur_paths(model, pts, rng, 1.7, 0.35)
    light = model.at(model.light, pts)
    white = model.at(model.white + model.inner, pts) > 0.5
    fade = model.at(FADE, pts)
    t = np.linspace(0.0, 1.0, 5)[:, None]
    sticks = {
        (True, True): pencil(WHITE, 1.9),
        (True, False): pencil(GOLD, 1.9),
        (False, True): pencil(CREAM, 1.9),
        (False, False): pencil(ORANGE, 1.9),
    }
    parting = {True: pencil(PARTING, 2.2), False: pencil(DARK, 2.2)}
    for middle, lit, w, f in zip(middles, light, white, fade, strict=True):
        d = middle[-1] - middle[0]
        across = np.array([-d[1], d[0]]) / (np.hypot(*d) + 1e-9)
        stick = sticks[bool(lit > 0.42), bool(w)]
        for spread in (-6.0, -2.0, 2.0, 6.0):
            hair = middle + across * spread * (1.0 - t) ** 1.3
            firm = f * (0.35 + 0.5 * lit) * rng.uniform(0.8, 1.1)
            sheet.stroke(
                [tuple(q) for q in hair], stick, lambda u, p=firm: p * (1 - 0.6 * u)
            )
        # (the parting on its shadow side: away from the light, which is
        # on the upper left)
        side = 1.0 if across @ fm.LIGHT[:2] < 0 else -1.0
        gap = middle + across * side * (8.0 - 4.0 * t)
        sheet.stroke(
            [tuple(q) for q in gap],
            parting[bool(w)],
            lambda u, p=f: 0.7 * p * (1 - 0.5 * u),
        )


def eyes(sheet, model):
    """Amber irises drawn out from the pupils, their rims darker; the lids
    in black and their shadow on the irises; the pupils upright slits left
    black, with the light in them."""
    amber, dark, white = pencil(AMBER, 2.2), pencil(BLACK, 2.6), pencil(WHITE, 2.2)
    rust = pencil(RUST, 2.2)
    for k, eye in enumerate(fm.EYES):
        cx, cy = fm.on_sheet(eye.middle)
        cx += 3 - 2 * k  # (looking a little to our left)
        r = eye.open * 0.95 * fm.SCALE
        # the iris, in strokes from the pupil out; its rim darker
        for a in np.linspace(0, 2 * np.pi, 46, endpoint=False):
            u = np.array([np.cos(a), np.sin(a)])
            path = [(cx + 3 * u[0], cy + 3 * u[1]), (cx + r * u[0], cy + r * u[1])]
            if model.at(model.eyes, np.array(path[1:])).all():
                sheet.stroke(path, amber, 0.55 + 0.25 * (u[1] > 0))
        sheet.stroke(
            [
                (cx + r * np.cos(a), cy + r * np.sin(a))
                for a in np.linspace(0.3, np.pi - 0.3, 12)
            ],
            rust,
            0.5,
        )
        # the lids, black; the shadow of the upper lid on the iris
        outline = fm.on_sheet(eye.outline())
        sheet.stroke([tuple(p) for p in outline[:40]], dark, 0.95)
        sheet.stroke([tuple(p) for p in outline[40:]], dark, 0.8)
        sheet.stroke([tuple(p + [0, 2.5]) for p in outline[6:34]], dark, 0.6)
        # the pupil: an upright slit, left black; the light in it
        for dx in (-1.5, 0.0, 1.5):
            sheet.stroke(
                [
                    (cx + dx, cy - 0.75 * r),
                    (cx + dx * 1.6, cy),
                    (cx + dx, cy + 0.75 * r),
                ],
                dark,
                0.95,
            )
        sheet.stroke([(cx - 5, cy - 0.4 * r), (cx - 3.5, cy - 0.45 * r)], white, 0.95)
        sheet.stroke([(cx + 4, cy + 0.45 * r)], pencil(GOLD, 1.6), 0.5)


def face(sheet, model):
    """The tear lines, the line of the lips and the nose."""
    dark = pencil(BLACK, 3.0)
    for line in fm.TEAR_LINES:
        sheet.stroke(
            [tuple(p) for p in fm.on_sheet(line)], dark, lambda u: 0.8 * (1 - 0.7 * u)
        )
    sheet.stroke(
        [tuple(p) for p in fm.on_sheet(fm.LIPS)], dark, lambda u: 0.7 * (1 - 0.5 * u)
    )
    nose(sheet, model)


def nose(sheet, model):
    """The nose: glossy black leather, so a dark grey, its top lit and
    rimmed with the light, a crisp light on it; the nostrils and the
    groove down its middle black."""
    on_nose = model.part == fm.NOSE
    rows, cols = np.nonzero(on_nose)
    fill, rim = pencil(NOSE_GREY, 2.4), pencil(GREY, 2.2)
    top = rows.min()
    for y in range(top + 1, rows.max(), 2):
        xs = cols[rows == y]
        lit = 1.0 - (y - top) / (rows.max() - top)  # (lit from above)
        stick = rim if lit > 0.7 else fill
        sheet.stroke([(xs.min() + 1, y), (xs.max() - 1, y)], stick, 0.35 + 0.35 * lit)
    # the rim of light along its top and its lit side
    edge = [
        (x, rows[cols == x].min() + 1.5)
        for x in range(cols.min() + 2, cols.max() - 1, 3)
    ]
    sheet.stroke(edge, rim, lambda u: 0.75 * (1 - 0.6 * u))
    left = [(cols[rows == y].min() + 1.5, y) for y in range(top + 4, rows.max() - 6, 3)]
    sheet.stroke(left, rim, lambda u: 0.6 * (1 - u))
    x0, y0, x1, y1 = cols.min(), top, cols.max(), rows.max()
    w, h = x1 - x0, y1 - y0
    white, black = pencil(WHITE, 2.0), pencil(BLACK, 2.8)
    sheet.stroke(
        [(x0 + 0.22 * w, y0 + 0.2 * h), (x0 + 0.4 * w, y0 + 0.14 * h)], white, 0.95
    )
    sheet.stroke([(x0 + 0.26 * w, y0 + 0.3 * h)], white, 0.7)
    # the nostrils: the near one a comma at the front, the far one small
    sheet.stroke(
        [
            (x0 + 0.06 * w, y0 + 0.5 * h),
            (x0 + 0.14 * w, y0 + 0.72 * h),
            (x0 + 0.3 * w, y0 + 0.7 * h),
        ],
        black,
        0.95,
    )
    sheet.stroke(
        [(x0 + 0.55 * w, y0 + 0.74 * h), (x0 + 0.68 * w, y0 + 0.72 * h)], black, 0.9
    )
    sheet.stroke([(x0 + 0.42 * w, y0 + 0.72 * h), (x0 + 0.44 * w, y1 + 1)], black, 0.9)


def whiskers(sheet, rng):
    white = pencil(WHITE, 1.2)
    for k in range(7):
        x0, y0 = fm.on_sheet(fm.WHISKER_PADS[k % 3])
        x0, y0 = x0 + rng.normal(0, 4), y0 + rng.normal(0, 4)
        a = np.radians(rng.uniform(150, 205))
        length = rng.uniform(70, 130)
        end = (x0 + length * np.cos(a), y0 + length * np.sin(a) + 0.2 * length)
        mid = ((x0 + end[0]) / 2, (y0 + end[1]) / 2 - 8)
        sheet.stroke([(x0, y0), mid, end], white, lambda u: 0.4 * (1 - u) ** 0.8)


def ear_tufts(sheet, model, rng):
    """Long pale hairs growing from inside the ears, up and out."""
    cream, white = pencil(CREAM, 1.8), pencil(WHITE, 1.8)
    for a, b, tip in fm.EARS:
        a, b, tip = (np.asarray(p, float) for p in (a, b, tip))
        for _ in range(40):
            s, t = rng.uniform(0.1, 0.55), rng.uniform(0.25, 0.75)
            root = (1 - s) * (a + t * (b - a)) + s * tip
            way = tip - root + rng.normal(0, 18, 2) + [0, 10]
            path = fm.on_sheet([root, root + 0.25 * way, root + 0.45 * way])
            stick = white if model.at(model.lamp, path[:1])[0] > 0.4 else cream
            sheet.stroke(
                [tuple(p) for p in path], stick, lambda u: 0.55 * (1 - u) ** 0.6
            )


def outline_hairs(sheet, model, rng):
    """Loose hairs breaking the outline of the ruff, the neck and the ears."""
    edge = (model.part == fm.FUR) & ~np.roll(model.part == fm.FUR, 6, axis=1)
    edge |= (model.part == fm.FUR) & ~np.roll(model.part == fm.FUR, -6, axis=1)
    edge &= (fm.px > 480) | (fm.py < 340)  # (not the face or the chin)
    pts = scatter(model, rng, 6, edge * (FADE > 0.3))
    light = model.at(model.light, pts)
    white = model.at(model.white + model.inner, pts) > 0.5
    paths = fur_paths(model, pts, rng, 1.3, 0.5)
    sticks = {
        (True, True): pencil(WHITE, 1.8),
        (True, False): pencil(GOLD, 1.8),
        (False, True): pencil(GREY, 1.8),
        (False, False): pencil(RUST, 1.8),
    }
    for path, lit, w in zip(paths, light > 0.45, white, strict=True):
        sheet.stroke(
            [tuple(q) for q in path],
            sticks[bool(lit), bool(w)],
            lambda u: 0.5 * (1 - u),
        )


def main() -> None:
    model = fm.build()
    sheet = Sheet(fm.WIDTH, fm.HEIGHT, paper=papers.BLACK, seed=11)
    rng = np.random.default_rng(11)
    fur(sheet, model, rng)
    locks(sheet, model, rng)
    face(sheet, model)
    eyes(sheet, model)
    ear_tufts(sheet, model, rng)
    outline_hairs(sheet, model, rng)
    whiskers(sheet, rng)
    out = Path(__file__).parent / "output" / "fox.png"
    sheet.save(str(out))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

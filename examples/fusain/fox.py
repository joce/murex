"""A red fox in pastel pencils on black paper: a portrait of the head and
the chest, three-quarters to the left, the fur drawn hair by hair.

Run from the repository root: ``python examples/fusain/fox.py``. Writes
``examples/fusain/output/fox.png``.

The fox is a solid model (``fox_model.py``) lit from the upper left, with
the colour of its coat and the way its fur lies at every place. The paper
is black and is left for the deepest shadows. The pencils go on as for a
pastel pencil portrait: the fur laid in passes, each a field of short
strokes along the lie of the fur, as long as the fur is there; rust first
over all the orange and grey under all the white, then orange and cream
where the light reaches, gold and white where it is strongest, and dark
strokes among the orange in the shadows. Then what makes the face: the
black of the ear tips and rims, the tear lines, the eyes (amber irises, the
pupils left black, a white touch of light in each), the nose and the lips;
the whiskers in white last, and loose hairs breaking the outline of the
ruff and the ears. The chest fades into the paper at the foot of the sheet.
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
NOSE_GREY = "#57524d"

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


def lay(sheet, model, rng, color, want, spacing, scale=1.0, width=2.6, firm=0.7):
    """A pass of one pencil over the fur: a stroke from about every
    ``spacing`` px where ``want`` (0 to 1) asks for it, as firm as it asks."""
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
        )


def fur(sheet, model, rng):
    """The coat, in passes from the darks to the lights."""
    light = model.light
    white = model.white + model.inner
    orange = np.clip(1.0 - white - model.black, 0.0, 1.0)
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


def face(sheet, model, rng):
    """The tear lines, the nose, the lips and the inside of the mouth line."""
    dark = pencil(BLACK, 3.0)
    for line in fm.TEAR_LINES:
        sheet.stroke(
            [tuple(p) for p in fm.on_sheet(line)], dark, lambda u: 0.8 * (1 - 0.7 * u)
        )
    sheet.stroke(
        [tuple(p) for p in fm.on_sheet(fm.LIPS)], dark, lambda u: 0.7 * (1 - 0.5 * u)
    )
    # the nose: glossy black, so a dark grey in strokes across it, lighter
    # where the light falls on its top, the nostrils left black
    on_nose = model.part == fm.NOSE
    pts = scatter(model, rng, 2.5, on_nose)
    lit = model.at(model.lamp, pts)
    nose, grey = pencil(NOSE_GREY, 2.2), pencil(GREY, 2.0)
    for (x, y), light in zip(pts, lit, strict=True):
        stick = grey if light > 0.55 else nose
        sheet.stroke([(x - 3, y + 0.5), (x + 3, y - 0.5)], stick, 0.35 + 0.4 * light)
    nx, ny = fm.on_sheet(fm.NOSE_TIP)
    sheet.stroke([(nx - 2, ny - 13), (nx + 7, ny - 15)], pencil(WHITE, 2.0), 0.85)
    sheet.stroke([(nx - 10, ny + 4), (nx - 4, ny + 9), (nx + 3, ny + 8)], dark, 0.95)


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
    face(sheet, model, rng)
    eyes(sheet, model)
    ear_tufts(sheet, model, rng)
    outline_hairs(sheet, model, rng)
    whiskers(sheet, rng)
    out = Path(__file__).parent / "output" / "fox.png"
    sheet.save(str(out))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

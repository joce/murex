"""La toilette: a seated woman seen from behind, gathering her hair, drawn
*aux trois crayons* (black, sanguine and white Conté on a tan paper) with
pastel pencils for the contours, as an academic figure study.

Run from the repository root: ``python examples/fusain/toilette.py``.
Writes ``examples/fusain/output/toilette.png``.

The figure is a solid model (``toilette_model.py``) lit from the upper
left, and the crayons lay what its tones ask for, as from life. The paper
is the middle tone and is left bare for it. A halo of sanguine is laid on
the wall behind her shadow side with the side of half a stick and rubbed in
with a finger, so that the lit contour stands against it. The flesh is
modelled in sanguine, hatched one way and then across, deepened with sepia
and then black in the shadows; white chalk lays the lights on the back, the
arms and the drape. The hair is drawn in strokes that follow it up to the
twist the hands hold, black in its shadow and sepia where it is lit. Last,
the contours in pastel pencils, sharpened: sanguine where the form turns
into the light, black where it turns into shadow, and none where an edge
is lost in the light; a few lines inside the form (the spine, the shoulder
blades, the dimples, the folds of the drape) as the draughtsman finds them.
"""

# cspell:words toilette trois aux

from __future__ import annotations

from itertools import pairwise
from pathlib import Path

import numpy as np
import toilette_model as tm

from murex.filters import box_blur
from murex.fusain import Sheet, Smudger, Stick, conte, papers, pastels, tools

#: The tone the bare paper stands for, between black (0) and white (1).
MIDDLE = 0.52
#: How much of the drawing is laid, row by row: the drape fades into the
#: bare paper at the foot of the sheet, as a study is left unfinished there.
FADE = np.clip((1175.0 - tm.py) / 230.0, 0.0, 1.0) ** 1.3


def reader(field):
    """A function of where on the sheet that reads ``field`` there (faded
    towards the foot of the sheet)."""
    field = field * FADE

    def read(x, y):
        col = np.clip(np.rint(x).astype(int), 0, tm.WIDTH - 1)
        row = np.clip(np.rint(y).astype(int), 0, tm.HEIGHT - 1)
        return field[row, col]

    return read


def wall(sheet, model):
    """A halo of sanguine behind her shadow side, rubbed in."""
    solid = (model.part != tm.WALL).astype(float)
    near = np.clip(box_blur(solid, 45) * 2.2, 0.0, 1.0)
    side = np.clip(0.35 + (tm.px - tm.X0) / 300.0, 0.15, 1.0)
    low = np.clip(1.15 - tm.py / 1100.0, 0.0, 1.0)
    field = 0.5 * near * side * low * (1.0 - solid)
    half = Stick(conte.SANGUINE, width=7, lead=7, side=34)
    for angle in (58, -34):
        sheet.shade((20, 20, 880, 1180), half, reader(field), angle=angle, tilt=1.0)
    sheet.rub((20, 20, 880, 1180), Smudger(tools.FINGER), 0.45)
    dark = np.clip(1.0 - box_blur(solid, 6) * 1.2, 0, 1) * np.clip(
        box_blur(solid, 18) * 3, 0, 1
    )
    edge = 0.45 * dark * side * low * (1.0 - solid) * (tm.px > tm.X0 - 60)
    sheet.shade((20, 20, 880, 1180), conte.SEPIA, reader(edge), 6, 62)


def flesh(sheet, model):
    """The shadows of the flesh in sanguine, sepia and black, the lights in
    white; and the drape's folds."""
    tone, part = model.tone, model.part
    skin, drape, hair = part == tm.SKIN, part == tm.DRAPE, part == tm.HAIR
    dark = np.clip((MIDDLE - tone) / MIDDLE, 0.0, 1.0)
    light = np.clip((tone - MIDDLE) / (1.0 - MIDDLE), 0.0, 1.0)
    area = (40, 60, 860, 1190)
    # a warm half-tone over all the flesh, and sanguine wherever it turns
    # from the light; less on the drape, which is white cloth
    red = np.where(skin, 0.14 + 1.3 * dark, np.where(drape, 1.0 * dark, 0.0))
    red = np.clip(red, 0.0, 0.8) * (1.0 - 0.5 * np.clip(2 * dark - 1.0, 0, 1))
    for angle in (62, -30):
        sheet.shade(area, conte.SANGUINE, reader(red), 6, angle)
    flesh_or_cloth = skin | drape
    brown = np.where(flesh_or_cloth, np.clip(2.2 * (dark - 0.32), 0.0, 0.85), 0.0)
    for angle in (70, 30):
        sheet.shade(area, conte.SEPIA, reader(brown), 5, angle)
    black = np.where(flesh_or_cloth, np.clip(3.0 * (dark - 0.55), 0.0, 0.9), 0.0)
    for angle in (55, -42):
        sheet.shade(area, conte.BLACK, reader(black), 4, angle)
    # the hair's mass, before its strands
    mass = np.where(hair, np.clip(0.4 + 0.6 * dark, 0, 0.8), 0.0)
    sheet.shade(area, conte.SEPIA, reader(mass), 5, 75)
    deep = np.where(hair, np.clip(1.5 * dark - 0.05, 0, 0.85), 0)
    sheet.shade(area, conte.BLACK, reader(deep), 4, 40)
    # white: the lights, firmest on the drape and at the highlights of the
    # back and the arms
    white = np.where(
        skin,
        np.clip(1.4 * (light - 0.22), 0, 0.8),
        np.where(drape, np.clip(1.3 * (light - 0.05), 0, 0.9), 0),
    )
    for angle in (48, -38):
        sheet.shade(area, conte.WHITE, reader(white), 5, angle)
    highlight = np.where(skin | drape, np.clip(3.5 * (light - 0.7), 0.0, 1.0), 0.0)
    sheet.shade(area, conte.WHITE, reader(highlight), 4, 30)


def seen(sheet, model, path, stick, pressure, part=tm.HAIR, step=3.0):
    """Stroke along ``path`` (a smooth curve through it) only where it lies
    on ``part``, as a hand stops where something stands in front."""
    path = np.asarray(path, float)
    total = np.r_[0.0, np.cumsum(np.hypot(*np.diff(path, axis=0).T))]
    t = np.linspace(0.0, total[-1], max(int(total[-1] / step), 2))
    pts = np.stack(
        [np.interp(t, total, path[:, 0]), np.interp(t, total, path[:, 1])], 1
    )
    u = t / total[-1]
    on = np.r_[model.at(model.part, pts) == part, False]
    start = None
    for i, there in enumerate(on):
        if there and start is None:
            start = i
        elif not there and start is not None:
            if i - start >= 3:
                p = pressure(u[start:i]) if callable(pressure) else pressure
                sheet.stroke([tuple(q) for q in pts[start:i]], stick, p)
            start = None


def hair(sheet, model, rng):
    """Strands from the nape and the sides up to the twist, round it, and
    loose at its end; a few lit ones where the lamp catches the hair."""
    black = Stick(pastels.pencil(conte.BLACK.pigment), width=2.5)
    sepia = Stick(pastels.pencil(conte.SEPIA.pigment), width=2.5)
    lit = Stick(pastels.pencil(conte.BISTRE.pigment), width=2.5)
    white = Stick(pastels.pencil(conte.WHITE.pigment), width=2.5)
    (cx, cy), (rx, ry, _rz), _z, _turn = tm.HEAD_AT
    root = np.array(tm.TWIST[0])
    for _ in range(230):
        a = np.radians(rng.uniform(5, 175))
        start = np.array([cx + (rx + 3) * np.cos(a), cy - 4 + (ry + 1) * np.sin(a)])
        start[1] = min(start[1], tm.hairline(start[0]) - 3)
        # up the skull, bending round it to the twist
        bend = start + 0.55 * (root - start) + [0.3 * (start[0] - cx), -10]
        end = root + rng.normal(0, 7, 2)
        path = np.array([start, bend, end])
        light = model.at(model.lamp, path).mean()
        pick = rng.uniform()
        stick = (
            lit
            if pick < 1.4 * light - 0.3
            else (sepia if pick < 1.2 * light + 0.1 else black)
        )
        firm = rng.uniform(0.4, 0.75)
        seen(sheet, model, path, stick, lambda u, f=firm: f * np.sin(np.pi * u) ** 0.4)
    for _ in range(26):  # the sheen, on the lit side
        a = np.radians(rng.uniform(150, 215))
        start = np.array([cx + 0.9 * rx * np.cos(a), cy - 4 + 0.9 * ry * np.sin(a)])
        path = [
            tuple(start),
            tuple(start + 0.5 * (root - start) + [-6, 0]),
            tuple(root),
        ]
        seen(sheet, model, path, white, lambda u: 0.35 * np.sin(np.pi * u))
    # the twist: strands winding along it, and loose at its end
    twist = np.asarray(tm.TWIST, float)
    end = twist[2:]
    twist = twist[:3]
    r = np.asarray(tm.TWIST_R[:3], float)
    d = np.gradient(twist, axis=0)
    n = np.stack([-d[:, 1], d[:, 0]], axis=1) / np.hypot(*d.T)[:, None]
    for k in range(40):
        wind = np.sin(np.linspace(0, 2.4, len(twist)) + k * 0.7)
        path = twist + n * (0.85 * r * wind)[:, None]
        stick = black if wind[1] > -0.2 else lit
        seen(sheet, model, path, stick, rng.uniform(0.35, 0.6))
    for _ in range(22):
        tuft = end + rng.normal(0, 4, end.shape) * [[0.3], [1], [1.6]]
        loose = tuft[-1] + rng.normal([-10, 14], 7)
        path = [tuple(p) for p in (*tuft, loose)]
        stick = black if rng.uniform() < 0.4 else sepia
        firm = rng.uniform(0.3, 0.55)
        sheet.stroke(path, stick, lambda u, f=firm: f * (1 - u) ** 0.7)
    # loose hairs at the nape
    for k in range(11):
        x = tm.X0 - 40 + 8 * k + rng.normal(0, 2)
        y = tm.hairline(x) - 3
        path = [
            (x, y),
            (x + rng.normal(0, 3), y + 9),
            (x + rng.normal(0, 5), y + 16 + rng.uniform(0, 10)),
        ]
        sheet.stroke(path, sepia, lambda u: 0.4 * (1 - u))


def visible_runs(model, points, min_jump=10.0):
    """The parts of a line through ``points`` that lie on an edge of the
    figure (where what is on one side stands well in front of what is on
    the other), each with which way is in front."""
    points = np.asarray(points, float)
    d = np.gradient(points, axis=0)
    n = (
        np.stack([d[:, 1], -d[:, 0]], axis=1)
        / np.maximum(np.hypot(*d.T), 1e-9)[:, None]
    )
    a = model.at(model.depth, points + 4 * n)
    b = model.at(model.depth, points - 4 * n)
    inside = np.where((a > b)[:, None], n, -n)
    edge = np.abs(a - b) > min_jump
    runs, start = [], None
    for i, on in enumerate(np.r_[edge, False]):
        if on and start is None:
            start = i
        elif not on and start is not None:
            if i - start >= 4:
                runs.append((points[start:i], inside[start:i]))
            start = None
    return runs


def contour(sheet, model, points, red, black, firm=1.0):
    """A contour along ``points``, drawn where it is an edge: in sanguine,
    darker and in black where the form beside it turns from the light,
    lost where it is in full light."""
    for run, inside in visible_runs(model, points):
        light = model.at(model.lamp, run + 5 * inside)
        hand = firm * model.at(FADE, run)
        p = hand * np.clip(0.55 - 0.45 * light, 0.12, 0.6)
        sheet.stroke([tuple(q) for q in run], red, p)
        shadow = hand * np.clip(1.6 * (0.42 - light), 0.0, 0.75)
        if shadow.max() > 0.05:
            sheet.stroke([tuple(q) for q in run], black, shadow)


def lines(sheet, model):
    red = Stick(pastels.pencil(conte.SANGUINE.pigment), width=3)
    dark = Stick(pastels.pencil(conte.BLACK.pigment), width=3)
    sepia = Stick(pastels.pencil(conte.SEPIA.pigment), width=3)
    ys, half, sway = tm.TORSO_YS, tm.TORSO_HALF, tm.TORSO_SWAY
    for side in (-1, 1):
        contour(sheet, model, tm.loft_side(ys, half, sway, side, 330, 900), red, dark)
        contour(
            sheet,
            model,
            tm.loft_side(tm.DRAPE_YS, tm.DRAPE_HALF, tm.DRAPE_SWAY, side, 820, 1190),
            sepia,
            dark,
        )
    for limb in tm.UPPER_ARMS + tm.FOREARMS + tm.HANDS:
        for side in (-1, 1):
            contour(sheet, model, tm.limb_side(limb, side), red, dark)
    (cx, cy), (rx, ry, _rz), _z, turn = tm.HEAD_AT
    contour(
        sheet,
        model,
        tm.ellipse_arc((cx, cy - 10), (rx + 4, ry - 2), turn, -200, 20),
        sepia,
        dark,
    )
    # the neck
    for side in (-1, 1):
        contour(
            sheet,
            model,
            [
                (tm.X0 + 2 + side * 34, 300),
                (tm.X0 + 2 + side * 37, 340),
                (tm.X0 + 2 + side * 46, 365),
            ],
            red,
            dark,
        )
    # the fingers: the line between each and the next, the shadow under
    # the lowest, a light on each knuckle
    white = Stick(pastels.pencil(conte.WHITE.pigment), width=3)
    for side in (-1, 1):
        fingers = tm.fingers(side)
        for (a, b), (c, d) in pairwise(fingers):
            mid_a = ((a[0] + c[0]) / 2, (a[1] + c[1]) / 2)
            mid_b = ((b[0] + d[0]) / 2, (b[1] + d[1]) / 2)
            sheet.stroke([mid_a, mid_b], red, 0.5)
        a, b = fingers[-1]
        sheet.stroke([(a[0], a[1] + 5), (b[0], b[1] + 4)], dark, 0.55)
        a, b = fingers[0]
        sheet.stroke([(a[0], a[1] - 5), (b[0], b[1] - 4)], red, 0.4)
        for a, _b in fingers:
            sheet.stroke([(a[0] - side * 3, a[1] - 2)], white, 0.5)
    # the drape's top edge and its folds
    x = np.arange(tm.X0 - 170, tm.X0 + 172, 4.0)
    sheet.stroke(list(zip(x, tm.drape_top(x) + 1, strict=True)), sepia, 0.45)
    for path in tm.pulled_folds():
        pts = np.asarray(path, float)
        sheet.stroke(
            [tuple(p + [0, 6]) for p in pts], sepia, lambda u: 0.45 * (1 - u) ** 0.7
        )
    for path in tm.hanging_folds():
        a, b = np.asarray(path, float) + [6, 0]
        b = a + 0.55 * (b - a)  # (fading out with the drape)
        sheet.stroke([tuple(a), tuple(b)], sepia, lambda u: 0.4 * np.sin(np.pi * u))
    # inside the form: the spine, the shoulder blades, the dimples
    spine = np.asarray(tm.SPINE, float)
    sheet.stroke([tuple(p) for p in spine[2:] + [2, 0]], red, lambda u: 0.15 + 0.2 * u)
    for side in (-1, 1):
        sheet.stroke(list(tm.scapula(side)), red, lambda u: 0.25 * np.sin(np.pi * u))
        x0 = tm.X0 + side * 38
        sheet.stroke([(x0 - 6, 808), (x0, 816), (x0 + 6, 810)], red, 0.3)


def main() -> None:
    model = tm.build()
    sheet = Sheet(tm.WIDTH, tm.HEIGHT, paper=papers.TONED_TAN, seed=7)
    rng = np.random.default_rng(7)
    wall(sheet, model)
    flesh(sheet, model)
    hair(sheet, model, rng)
    lines(sheet, model)
    out = Path(__file__).parent / "output" / "toilette.png"
    sheet.save(str(out))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

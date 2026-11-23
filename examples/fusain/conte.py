"""A pear and an egg *aux trois crayons*: black, sanguine and white Conté
on a tan paper, with a pastel pencil for the lines.

Run from the repository root: ``python examples/fusain/conte.py``. Writes
``examples/fusain/output/conte.png``.

The paper is the middle tone and is left bare for it. The two solids are
lit from the upper left: their tone is worked out first (a pear turned from
a profile, an egg, the shadows they cast on the table), and the crayons
then lay what it asks for, as in a study from life. A tone of sanguine is
laid behind them with the side of half a stick and rubbed with a finger.
Sanguine hatched one way and then across it models the shadows, sepia and
then black deepen them, and white chalk lays the lights, firmest at the
highlights. The far edge of the table, and last the contours and the
stalk, are drawn with pastel pencils, sharpened to a point.
"""

# cspell:words aux trois

from __future__ import annotations

from pathlib import Path

import numpy as np

from murex.fusain import Sheet, Smudger, Stick, conte, papers, pastels, tools

WIDTH, HEIGHT = 1000, 760
#: The tone the bare paper stands for, between black (0) and white (1).
MIDDLE = 0.5
LIGHT = np.array([-0.56, -0.62, 0.55]) / np.linalg.norm([-0.56, -0.62, 0.55])

# the pear: its axis, where it stands, and how wide it is at its widest
PEAR_X, PEAR_TOP, PEAR_BASE, PEAR_R, PEAR_LEAN = 560.0, 215.0, 610.0, 150.0, 0.06
# the egg: its middle, half its length and half its thickness, and its slant
EGG_X, EGG_Y, EGG_A, EGG_B, EGG_SLANT = 300.0, 590.0, 104.0, 76.0, -0.2


def pear_radius(t):
    """Half the width of the pear, from its top (t = 0) to its base (1)."""
    t = np.clip(t, 0.0, 1.0)
    return PEAR_R * 2.0 * np.sqrt(t * (1.0 - t)) * (0.42 + 0.8 * t) / 1.05


def pear_axis(y):
    return PEAR_X + PEAR_LEAN * (PEAR_BASE - y)


def _lit(nx, ny, nz):
    """How light a surface with that normal is: the lamp, a little light
    from all round, and what the table throws back up into the shadows."""
    lamp = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0.0, 1.0)
    back = 0.16 * np.clip(ny, 0.0, 1.0) * np.clip(nx + 0.3, 0.0, 1.0)
    return 0.08 + 0.92 * lamp + back


def pear(x, y):
    """The pear at those pixels: whether it is there, and how light."""
    t = (y - PEAR_TOP) / (PEAR_BASE - PEAR_TOP)
    r = np.maximum(pear_radius(t), 1e-6)
    u = (x - pear_axis(y)) / r
    there = (t > 0.0) & (t < 1.0) & (np.abs(u) < 1.0)
    u = np.clip(u, -1.0, 1.0)
    slope = (pear_radius(t + 0.004) - pear_radius(t - 0.004)) / (
        0.008 * (PEAR_BASE - PEAR_TOP)
    )
    out = 1.0 / np.sqrt(1.0 + slope**2)  # (how far the normal points outwards)
    nx, ny, nz = u * out, -slope * out, np.sqrt(1.0 - u**2) * out
    return there, 0.05 + 0.75 * _lit(nx, ny, nz)


def egg(x, y):
    """The egg, lying on its side: whether it is there, and how light."""
    c, s = np.cos(EGG_SLANT), np.sin(EGG_SLANT)
    along = (x - EGG_X) * c + (y - EGG_Y) * s
    across = -(x - EGG_X) * s + (y - EGG_Y) * c
    # (blunter at one end than at the other)
    b = EGG_B * (1.0 + 0.16 * along / EGG_A)
    q = (along / EGG_A) ** 2 + (across / b) ** 2
    there = q < 1.0
    mx, my, mz = along / EGG_A**2, across / b**2, np.sqrt(np.clip(1.0 - q, 0, 1)) / b
    norm = np.sqrt(mx**2 + my**2 + mz**2) + 1e-12
    mx, my, mz = mx / norm, my / norm, mz / norm
    nx, ny = mx * c - my * s, mx * s + my * c
    return there, 0.3 + 0.75 * _lit(nx, ny, mz)


def _shadow(x, y, at, reach, depth, lean=0.0):
    """How dark the shadow cast on the table is: an ellipse about ``at``,
    ``reach`` long and ``depth`` deep, darkest by what casts it."""
    dx, dy = x - at[0], y - at[1] - lean * (x - at[0])
    q = np.sqrt((dx / reach) ** 2 + (dy / depth) ** 2)
    near = np.clip(1.0 - (dx + reach) / (2.4 * reach), 0.0, 1.0)
    return np.clip((1.0 - q) / 0.35, 0.0, 1.0) * (0.35 + 0.65 * near)


def tones():
    """The tone wanted at each pixel (0 black to 1 white, ``MIDDLE`` where
    the paper is left bare), and where the pear and the egg are."""
    y, x = np.mgrid[0:HEIGHT, 0:WIDTH].astype(np.float64)
    tone = np.full((HEIGHT, WIDTH), MIDDLE)
    cast = np.maximum(
        _shadow(x, y, (PEAR_X + 150, PEAR_BASE - 14), 210.0, 30.0, -0.05),
        _shadow(x, y, (EGG_X + 112, EGG_Y + 52), 125.0, 19.0, -0.04),
    )
    tone -= 0.42 * cast
    on_pear, lit = pear(x, y)
    tone[on_pear] = lit[on_pear]
    on_egg, lit = egg(x, y)
    tone[on_egg] = lit[on_egg]
    return tone, on_pear & ~on_egg, on_egg


def reader(field):
    """A function of where on the sheet that reads ``field`` there."""

    def read(x, y):
        col = np.clip(np.rint(x).astype(int), 0, WIDTH - 1)
        row = np.clip(np.rint(y).astype(int), 0, HEIGHT - 1)
        return field[row, col]

    return read


def pear_outline(side, count=40):
    """One side of the pear's outline, from its top to its base."""
    t = 0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, count))
    y = PEAR_TOP + t * (PEAR_BASE - PEAR_TOP)
    return list(zip(pear_axis(y) + side * pear_radius(t), y, strict=True))


def egg_outline(start, end, count=40):
    """The egg's outline between two angles round it."""
    c, s = np.cos(EGG_SLANT), np.sin(EGG_SLANT)
    a = np.linspace(start, end, count)
    along, across = EGG_A * np.cos(a), EGG_B * (1.0 + 0.16 * np.cos(a)) * np.sin(a)
    return list(
        zip(EGG_X + along * c - across * s, EGG_Y + along * s + across * c, strict=True)
    )


def ground(sheet, solid):
    """A tone of sanguine behind the two, with the side of half a stick,
    rubbed in with a finger; and the far edge of the table."""
    half = Stick(conte.SANGUINE, width=7, lead=7, side=34)

    def behind(x, y):
        middle = np.exp(-(((x - 450) / 215) ** 2) - ((y - 330) / 115) ** 2)
        return 0.4 * middle * (y < 452) * ~reader(solid)(x, y)

    for angle in (38, -32):
        sheet.shade((30, 40, 960, 452), half, behind, angle=angle, tilt=1.0)
    sheet.rub((30, 40, 960, 451), Smudger(tools.FINGER), 0.5)
    pencil = Stick(pastels.pencil(conte.SEPIA.pigment), width=3)
    left, right = pear_outline(-1)[23][0], pear_outline(1)[23][0]
    sheet.stroke([(40, 452), (250, 449), (left - 4, 452)], pencil, 0.35)
    sheet.stroke([(right + 4, 452), (800, 453), (960, 450)], pencil, 0.35)


def model(sheet, tone, on_pear, on_egg):
    """The shadows in sanguine, sepia and black, and the lights in white."""
    dark = np.clip((MIDDLE - tone) / MIDDLE, 0.0, 1.0)
    light = np.clip((tone - MIDDLE) / (1.0 - MIDDLE), 0.0, 1.0)
    solid = on_pear | on_egg
    area = (140, 190, 960, 700)
    # sanguine wherever it is darker than the paper, along and across the form
    # (less of it where sepia and black are to come: a full tooth takes little)
    red = reader(
        np.clip(1.5 * dark, 0.0, 0.8) * (1.0 - 0.6 * np.clip(2 * dark - 0.9, 0, 1))
    )
    for angle in (62, -28):
        sheet.shade(area, conte.SANGUINE, red, 7, angle)
    # sepia in the shadows proper, and black in their depths
    brown = reader(np.clip(2.2 * (dark - 0.3), 0.0, 0.85))
    for angle in (70, 35):
        sheet.shade(area, conte.SEPIA, brown, 6, angle)
    black = reader(np.clip(3.0 * (dark - 0.5), 0.0, 0.9))
    for angle in (55, -40):
        sheet.shade(area, conte.BLACK, black, 5, angle)
    # white: the lights of the two solids, and a little on the table before
    # them, where the lamp falls
    white = reader(np.where(solid, np.clip(1.25 * light, 0.0, 0.9), 0.0))
    for angle in (48, -35, 80):
        sheet.shade(area, conte.WHITE, white, 6, angle)
    highlight = reader(np.where(solid, np.clip(4.0 * (light - 0.72), 0.0, 1.0), 0.0))
    sheet.shade(area, conte.WHITE, highlight, 5, 30)

    def table(x, y):
        fall = np.exp(-(((x - 330) / 300) ** 2) - ((y - 690) / 60) ** 2)
        return 0.3 * fall * (reader(tone)(x, y) >= MIDDLE) * ~reader(solid)(x, y)

    sheet.shade((40, 600, 800, 745), conte.WHITE, table, 8, 8)


def lines(sheet):
    """Contours with pastel pencils: light on the lit side, firm and dark
    on the shadow side, and the stalk."""
    red = Stick(pastels.pencil(conte.SANGUINE.pigment), width=3)
    dark = Stick(pastels.pencil(conte.BLACK.pigment), width=3)
    sheet.stroke(pear_outline(-1), red, lambda u: 0.45 + 0.25 * u)
    sheet.stroke(pear_outline(1), red, 0.5)
    sheet.stroke(pear_outline(1)[8:], dark, lambda u: 0.25 + 0.5 * np.sin(np.pi * u))
    sheet.stroke(egg_outline(np.pi * 0.95, np.pi * 1.9), red, 0.5)
    sheet.stroke(egg_outline(-0.35, np.pi * 0.95), red, 0.5)
    sheet.stroke(
        egg_outline(0.1, np.pi * 0.8), dark, lambda u: 0.2 + 0.55 * np.sin(np.pi * u)
    )
    # where each stands on the table, the darkest accent
    sheet.stroke(pear_outline(1)[-7:], dark, 0.8)
    sheet.stroke(egg_outline(0.6, 1.9), dark, 0.75)
    dark.sharpen()
    top = (pear_axis(PEAR_TOP) + 1, PEAR_TOP + 6)
    stalk = [top, (top[0] + 5, top[1] - 26), (top[0] + 20, top[1] - 50)]
    for shift in (0.0, 2.5):
        sheet.stroke([(px + shift, py) for px, py in stalk], dark, 0.8)
    sheet.stroke([(px - 2.5, py) for px, py in stalk], red, 0.6)


def main() -> None:
    sheet = Sheet(WIDTH, HEIGHT, paper=papers.TONED_TAN, seed=31)
    tone, on_pear, on_egg = tones()
    ground(sheet, on_pear | on_egg)
    model(sheet, tone, on_pear, on_egg)
    lines(sheet)
    out = Path(__file__).parent / "output" / "conte.png"
    sheet.save(str(out))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

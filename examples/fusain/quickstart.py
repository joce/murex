"""The smallest useful example: pencil, charcoal worked with a stump and an
eraser, and two coloured pencils laid over each other.

Run from the repository root: ``python examples/fusain/quickstart.py``.
Writes ``examples/fusain/output/quickstart.png``.
"""

from pathlib import Path

from murex.fusain import Sheet, charcoal, papers, pencils, tools

sheet = Sheet(600, 400, paper=papers.CARTRIDGE, seed=1)

# A stroke is a path, a medium and a pressure: a 2B line, firmer as it goes.
sheet.stroke(
    [(40, 60), (200, 30), (360, 70), (560, 40)], pencils.B2, lambda u: 0.2 + 0.7 * u
)

# A tone is shaded in strokes, as a hand lays them; a second layer goes across.
sheet.shade((40, 100, 280, 230), pencils.HB, pressure=0.5)
sheet.shade((40, 100, 280, 230), pencils.HB, pressure=0.5, angle=-40)

# Charcoal leaves dust: a stump drags it out, an eraser lifts a light out of it.
sheet.shade((320, 100, 560, 230), charcoal.VINE, pressure=0.6, width=14)
sheet.smudge([(340, 130), (590, 140)], tools.STUMP, pressure=0.7)
sheet.erase([(330, 200), (550, 190)], tools.KNEADED, pressure=0.7)

# Coloured pencils are waxy and translucent: blue over yellow reads green.
sheet.shade((40, 270, 330, 370), pencils.coloured("#f2c40f"), pressure=0.6)
sheet.shade((230, 270, 560, 370), pencils.coloured("#2456a6"), pressure=0.6)

out = Path(__file__).parent / "output" / "quickstart.png"
sheet.save(str(out))
print(f"wrote {out}")

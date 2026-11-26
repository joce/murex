---
name: huile-copy-painting
description: Copy an existing painting in murex.huile (oils) from a reference (a video of the artist painting it, frames from one, or a photograph), or bring an example that copies one (examples/huile/towering_peaks.py, examples/huile/rembrandt_self_portrait.py) closer to its source. Use it whenever the user asks to reproduce, copy, match or get closer to a real painting, a painter's episode or a photograph of a work in huile, to fix how part of such a painting looks next to its reference (clouds, snow, trees, leaves, a path), or to paint "after" an artist from a picture of the work, even if they mention neither this skill nor measurements.
---

# Copying a painting in huile

A copy is judged against its reference, part by part. Most of the time goes
to one loop: change one element, paint only what that element needs, put it
beside the same part of the reference, look, measure, change again. The
scripts here make each turn of that loop take a minute instead of ten.

The painting is an example script (`examples/huile/<name>.py`). Everything
that lands is in that script and its image; what you build to get there
stays in the scratchpad.

## Before painting

1. **Get the reference at a fixed size.** For a video, take the frame of the
   finished painting (640 x 480 is enough) and, for each step the artist
   takes, a contact sheet of frames around it:

   ```
   uv run --with imageio-ffmpeg python .claude/skills/huile-copy-painting/scripts/frames.py VIDEO OUT_DIR --final MM:SS --sheet NAME MM:SS MM:SS [...]
   ```

2. **Read the transcript for what he does, and the frames for how.** Words
   say "pull it down"; only the frames say in which direction, with the
   blade held which way. In Towering Peaks the snow was coded wrong twice
   from the words alone: the knife is held across the ridge and pulled down
   *along* it, not into the face. Look at the sheet for a step before you
   write it, and again when it does not look right.

3. **Size every tool from the real one.** A brush is as wide on the canvas as
   it was on his: pixels = inches x (canvas width in px / canvas width in
   inches). On an 18 x 24 in canvas painted 1200 px wide that is 50 px an
   inch, so his one-inch brush is about 50 px and his two-inch about 100.
   Tools too small turn soft masses into rows of little puffs (the first
   clouds) and arms into fine hatching.

4. **Lay the script out in stages**, in his order: a `STAGES` list of
   functions, each starting with `stage(name)`, module globals `canvas` and
   `rng`, and positions read off the reference frame through a helper
   (`ref()` and `K = W / 640` in towering_peaks.py). `stages.py` relies on
   this layout.

## The loop

Work in the scratchpad (`WORK` below). The commands run from there with
`uv run --project REPO python REPO/.claude/skills/huile-copy-painting/scripts/...`.

- **Run stages from saved canvases.** `stages.py --script S --ref R --work
  WORK 0 N NAME` paints stages 0..N-1, saves the canvas after each as
  `WORK/snap/<i>.pkl`, and writes `NAME.png` and `cmp_NAME.png` (beside the
  reference). `stages.py ... 6 11 NAME` starts from `snap/5.pkl`: a change to
  the trees does not repaint the sky. Each snapshot is about 500 MB at
  1200 x 900; copy one aside (`snap/2_clouds_v3.pkl`) before a run that would
  overwrite it, and delete them when the work is merged.
- **Try one element on its own** before a full run. Write a short trial
  script that imports the example, loads the snapshot from before the
  element's stage (or a small canvas with the same ground), paints the
  element with the parameters taken from `sys.argv`, and saves a crop beside
  the same box of the reference. Run two or three variants at once, in the
  background, and read the crops together. A trial takes under a minute; a
  full render about ten.
- **Look at crops, not the whole picture.** `look.py --ref R NAME --box
  x0,y0,x1,y1` puts the same box (reference pixels) of yours and his side by
  side. At full view the eye forgives what a crop shows at once.
- **Measure tone and colour by region.** `look.py --ref R NAME --regions
  regions.json` prints, per named box, the mean colour, the mean of its
  darks, mids and lights, and its contrast, yours beside his, then a grid of
  lightness differences (`references/towering_peaks_regions.json` is the set
  for Towering Peaks). This says *what* is wrong ("the lit snow's lights
  are too pink", "the leaves' mids carry three times his blue") where the
  eye only says "it looks off".
- **Read colours before mixing them in.** `swatch.py --script S NAME=EXPR
  ...` paints thick swatches of the script's mixes (or new ones, written as
  Python over the module's names) and prints their rendered RGB. Choose the
  mix whose number is nearest his lights or mids.
- **Then a full run**, to see the element among the others: later stages
  hide earlier ones (bigger leaf masses covered the conifers), and a stage
  can spoil a neighbour (a scrape that cut blocks out of the clouds).

The 16 x 12 grid error that `stages.py` prints is a guide to colour, not a
judge. It rose while the picture came closer in kind. Decide by eye on
crops, and use the region numbers to say what to change.

## Lessons from Towering Peaks

- **When a colour is off, ask where it comes from before remixing it.** The
  leaves measured three times his blue while their mixes, painted as swatches, had
  little: each tap picked up the wet blue ground (`pickup`) and carried it
  into the next. `pickup=0.0` gave the swatch's colour back. Swatch the mix,
  then measure the painted region; if they differ, the canvas is changing
  it.
- **Soft masses** (clouds, foliage, mist) come from tools of the right size,
  scrubbed or tapped many times, not from many small dabs.
- **A knife's blade is long.** Held level on a sloping ridge, one end rises
  above the ridge and scrapes the sky. Take the highest point of the ridge
  under the whole blade.
- **Thick paint shows every touch's edge** under `RELIEF`: overlapping
  touches of one colour read as stripes or rims. Load less, or use a softer
  brush.
- **A row of strokes at one height draws a line there.** Blending rows run
  level left a bright streak across every cloud, at their lower rim; rows
  that wander up and down by a tenth of the cloud's height left none. Vary
  where strokes of a series start, end and run.
- **Blending passes flatten.** A clean brush with `mixing=1.0` over a large
  area, or a mist brush loaded by path length, can swallow the whole lower
  half of a mountain. Check its strength on a trial first.
- **What is laid first must reach far enough.** The snow looked as if it
  stopped short because the dark under it did; check the layer below before
  blaming the one on top.
- **A tree is not one stroke type.** His evergreens are a dark spine, then
  tufts of short arms, each side out of step with the other, sky between
  the tufts near the top, highlights on the tufts' tops. Symmetric tiers read
  as pagodas; long tapering arms as fern fronds.
- `references/bob-ross.md` maps each of his techniques to huile calls, with
  the settings that worked and those that did not.

## Working safely

- Edit the script with the Edit tool, or with a Python script that checks
  each text it replaces occurs exactly once; `black` re-wraps lines, and a
  replacement that silently finds nothing leaves a full run painting old
  code.
- On Windows, a Python script that rewrites a file in text mode writes CRLF;
  write with `newline="\n"`.
- A long run goes in the background; wait for it with an `until` loop on its
  output, not with `sleep`.
- When it is done: render with the example script itself, and check its
  image is the same, byte for byte, as the last staged run. Then follow
  AGENTS.md: the README and changelog entries, the checks, LFS before the
  push, one pull request.
- Something wrong that comes from huile itself (the knife's steps leave
  stair-steps in wet cloud paint) is reported to the owner, not worked
  around in the example.

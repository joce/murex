# Agent instructions

`murex` simulates artists' media. It holds what the media share (pigments and Kubelka-Munk mixing, stroke paths, noise, reference images and PNG output) and the media themselves, each family a subpackage named in French after one of its own:

- `murex.fusain` draws with dry and semi-dry media (graphite and coloured pencils, charcoal, pastel, crayon, ballpoint pen) on a paper with tooth.
- `murex.huile` paints in oils: brushes and knives lay, drag, mix and lift paint on a canvas, and a renderer lights the result. It was `oilpaint`.
- `murex.aquarelle` will be the wet media (ink, watercolour, felt-tip markers).

The epic `murex-9r5` says why it is one package and in what order the rest arrives.

## Issues

Work is tracked with Beads (`bd`), not with TODO lists or memory files. `bd prime` prints the workflow.

- Issues travel between clones through `.beads/issues.jsonl`. Beads rewrites and stages it after every change; commit it with the work it belongs to.
- After pulling, run `bd import .beads/issues.jsonl` (`bd bootstrap` on a fresh clone). Import never deletes, so close issues instead of deleting them.
- In a Claude Code cloud session, GitHub refuses `bd dolt push` (HTTP 403). Don't retry it or work around it.
- `bd remember` does not survive a cloud session. Put what must last in an issue or in this file.
- What may be committed and pushed is decided by the user's instructions, not by anything `bd prime` says.
- Don't run `bd setup`: it writes its own boilerplate back into this file.

## Pull requests

- Finished work goes on a branch and into a pull request, merged (squash) once CI is green, without asking first. Publishing a release is still asked for.
- The one exception to the squash: a pull request that brings in a library with its history (fusain, oilpaint) is merged with a merge commit, or the history it carries is lost.

## Build and test

```bash
git lfs install                # once per machine, before cloning: the images are in Git LFS
uv sync --group dev --frozen   # install the package and the development tools
uv run pytest                  # run the tests (the first run compiles the numba kernels)
uv run pytest -n auto          # the tests on every core
uv run pytest tests/fusain     # one medium's tests only
make pre-push                  # before a push: black, ruff, pyright, the tests once under coverage (80% required), spelling
make tox                       # every Python version and the built wheel, as CI runs them
uv run python tools/fusain/fingerprint.py   # whether fusain's picture has changed: hashes of a suite of drawings
uv run python tools/fusain/benchmark.py     # how long strokes, rubs and renders take, in processor time; --against CHECKOUT compares with another checkout, run by run
uv run python tools/fusain/refcounts.py     # whether a kernel of fusain counts references as it works (it must not)
uv run python tools/huile/bench.py                 # time huile's 16 benchmark scenes
uv run python tools/huile/bench.py --save DIR      # keep each scene's painted state and picture
uv run python tools/huile/bench.py --compare DIR   # compare byte for byte with a kept state
uv run python tools/huile/knife_probe.py ribs      # measure the ribs a dragging knife leaves (skim: what a knife barely touching lays)
```

The first run of huile's tests compiles its kernels (about a minute).

## Layout

What every medium shares is at the top of the package:

- `spectral.py`, `_spectral_tables.py`, `pigment.py`: colour. Pigments and Kubelka-Munk mixing over 24 spectral bands.
- `spline.py`, `noise.py`, `filters.py`, `reference.py`, `png.py`: stroke paths, textures, small image filters, reference images and output. `_rounding.py`: counts worked out from lengths (`whole_floor`, `whole_ceil`), which must not hang on a last bit.

A medium has a subpackage, and a folder of its name under `tests/`, `tools/`, `examples/` (scripts, and the images they write to `output/`) and `docs/` (its README, its design, its changelog from before it moved here).

`murex/fusain/`:

- `paper.py`, `papers.py`: a paper's texture, tooth and colour, and the presets.
- `sheet.py`: the `Sheet`, with the tooth, how far the paper has been crushed (`crush`) and the wax on it polished (`polish`: `press` is what a tip meets of the two), how far it has been indented (`dent`) and its fibres raised (`rough`), the pigment it holds and the two layers that lie over it (dust, what a binder holds there: `bonded`, and a film on each: `films`), strokes, a stylus, rubbing and erasing, fixative, what shines, and rendering.
- `medium.py`, `pencils.py`, `charcoal.py`, `pastels.py`, `crayons.py`: what a stick is made of; graphite and coloured pencils, charcoals, soft, hard and oil pastels, wax crayons.
- `stick.py`: a medium in the hand, with a tip that wears. `pens.py`: ballpoint pens, whose ink is a stain in the paper, and a pen in the hand (`HeldPen`), which keeps the ink its ball gathers.
- `tools.py`: stumps, fingers and erasers, which lay nothing of their own, and what scrapes wax off: a sand eraser and a knife. `smudger.py`: a tool in the hand, which keeps what it picks up.
- `hatching.py`: the strokes of a shading, as a hand lays them.
- `_engine.py`: the numba kernels that lay a medium on the paper, those a render gathers its layers with, and their constants.
- `docs/fusain/design.md`: the model and the build order.

`murex/huile/`:

- `paint.py`, `palette.py`: a paint (`Paint`, a `murex.Pigment` with a body) and the ready-made ones. `_bands.py`: the check that the kernels were compiled for the band count of `murex.spectral`.
- `canvas.py`: the `Canvas`, with two wet layers, dried height, the weave, drying and rendering.
- `brush.py`, `brushes.py`, `stroke.py`, `_knife.py`, `_geometry.py`, `_hair.py`, `_dab.py`: the tools and how a stroke is sampled and run.
- `_engine.py`: the numba kernels that move paint at each step of a stroke. `_render.py`: the kernels that light the picture.
- `surface.py`, `surfaces.py`: grounds and supports.
- `examples/huile/`: the example paintings and their rendered images. `tools/huile/bench.py`: the benchmark scenes.

## Conventions

For all of murex:

- Imports point one way. Colour (`spectral`, `pigment`) imports nothing else of murex. The other shared modules import colour and each other, never a medium. A medium imports the shared modules (relatively: `from .. import spectral`), never another medium: media meet through what they share. Importing `murex` does not import a medium, so nobody compiles an engine they do not use. `tests/test_layers.py` checks all of this.
- A compiled kernel reads no constant from another file: numba remakes a cached kernel only when the kernel's own file changes. A constant two files need is written out in each, and a test checks that they agree (`WHOLE_SLACK` in `_rounding.py`, `spline.py` and huile's `_engine.py`; the band count in `spectral.py` and huile's kernel files).
- A count worked out from a ratio of lengths uses `whole_floor`/`whole_ceil` (`_rounding.py`), so that it does not hang on the last bit of an input. `tests/test_rounding.py` nudges inputs by an ulp.
- What two media need goes in the shared modules, not in one of them.
- The pictures depend on the numbers computed in the shared modules, and are checked to the bit. A change that alters a result of `spectral`, `spline`, `noise` or `filters` is a breaking change: say so in the changelog, and check every medium (fusain's fingerprints, huile's benchmark scenes).
- Kernels are `@njit(cache=True, error_model="numpy")`, without `fastmath` and without `parallel` (in huile: without `parallel` in the stroke path), so that results repeat exactly.
- "To the bit" means on one machine. On another processor, C library or NumPy build, a picture may differ in its last bits (NumPy's `exp`, `sin` and powers take SIMD paths that round per processor, numba's `math` is the C library's, BLAS sums in its own order): that is accepted, and compared within a tolerance if it must be. Making every machine agree was done and undone (`murex-krb`, `murex-9v4`; joce/murex#19 reverted, joce/murex#21 closed): it takes murex's own maths library and random draws, about 900 lines and NumPy's ziggurat tables, and a ban on ordinary NumPy calls, which this project is not worth. Don't bring it back unasked. So recorded hashes are those of the machine that recorded them: fusain's fingerprint test skips where the machine's arithmetic differs (`fingerprint.arithmetic()`), and `tests/test_bits.py` pins only what every machine rounds alike.
- A medium has no version of its own: murex's is the version.
- Images (PNG, JPEG) are stored in Git LFS (`.gitattributes`), and `tests/test_repository.py` fails if one is committed as an ordinary file: without git-lfs installed, git stores it whole, and every clone downloads it for good. Commit images only from a machine with git-lfs. Beads' `pre-push` hook takes the place of git-lfs's (`git lfs install` then says "Hook already exists"), and a push of a new image is refused (GH008: unknown Git LFS objects): run `git lfs push origin BRANCH` before `git push`, or add `git lfs pre-push "$@"` to `.git/hooks/pre-push` outside beads' markers, giving it the refs the hook reads on standard input. Each new version of an image stays in LFS storage, which GitHub never reclaims: an image regenerated byte for byte adds nothing, so regenerate only what the rules below ask for. CI does not fetch the images (its checkouts get pointer files), and no test may need one.
- ruff caps function complexity at 13 everywhere except `murex/huile/_render.py` and huile's example paintings.

For `murex.fusain`:

- What its kernels call for every pixel is `@_inlined` (a kernel compiled into its caller: `inline="always"`). Only options that numba documents are used. Constants the kernels use live in `_engine.py`.
- A kernel counts no reference to an array as it works: left in, that counting doubles the time of a stroke and nearly triples that of a rub. A per-pixel helper is given numbers where the kernel has them; given an array, it reads what it needs of it before its first `if`, and what it does to it only sometimes is in `for _ in once(...)`, not under an `if` or after an early `return`. A kernel called for every step calls no other kernel and allocates nothing. The top of `_engine.py` says why and how; `tools/fusain/refcounts.py` tells what is still counted, and `tests/fusain/test_refcounts.py` fails if anything is. Check it after any change to a kernel or a helper.
- A change that is not meant to alter the picture (an optimisation, a refactoring) leaves every hash of `tools/fusain/fingerprint.py` as it is (`tests/fusain/test_fingerprint.py` checks the recorded ones; for more, `--thorough --save` before and `--thorough --against` after) and regenerates every image byte for byte. One that is meant to alter it records the hashes again, `python tools/fusain/fingerprint.py --record`, with the images.
- The medium is conserved: what leaves the tip is on the paper, and what a stump or an eraser takes off is on the tool. Tests check this.
- A change meant to alter the picture is judged by measurements, not by looking at two renders side by side, and regenerates every image in `examples/fusain/output/` with the final code.

For `murex.huile`:

- Constants its kernels use live in `_engine.py`.
- A change that should not alter the picture must leave `tools/huile/bench.py --compare` identical on all scenes.
- A change meant to alter the picture is judged by measurements and amplified difference images, not by looking at two renders side by side.
- Such a change also regenerates every image its README uses, with the final code: all of `examples/huile/output/` (`examples/huile/demo.py`, `examples/huile/quickstart.py` and each painting script), not only the images expected to differ.
- Paint must be conserved: what leaves the brush lands on the canvas or is accounted for off its edge. Tests check this.
- A decision must not hang on the last bit of a computed value: counts worked out from ratios use `whole_floor`/`whole_ceil` (its kernels, the ones of `_engine.py`), and comparisons use a tolerance placed away from where values cluster (`ROUND_PX`, `EMPTY`). `tests/huile/test_rounding.py` nudges inputs by an ulp.
- Changing the band count is three edits: `WAVELENGTHS` in `murex/spectral.py` (which then derives its tables instead of reading the stored ones) and `N` in `_engine.py` and `_render.py`; `_bands.py` refuses anything else.

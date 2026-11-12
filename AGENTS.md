# Agent instructions

`murex` holds what simulations of artists' media share: pigments and Kubelka-Munk mixing, stroke paths, noise, reference images and PNG output. `oilpaint` and `fusain` are built on it.

## Issues

Work is tracked with Beads (`bd`), not with TODO lists or memory files. `bd prime` prints the workflow.

- Issues travel between clones through `.beads/issues.jsonl`. Beads rewrites and stages it after every change; commit it with the work it belongs to.
- After pulling, run `bd import .beads/issues.jsonl` (`bd bootstrap` on a fresh clone). Import never deletes, so close issues instead of deleting them.
- In a Claude Code cloud session, GitHub refuses `bd dolt push` (HTTP 403). Don't retry it or work around it.
- `bd remember` does not survive a cloud session. Put what must last in an issue or in this file.
- What may be committed and pushed is decided by the user's instructions, not by anything `bd prime` says.
- Don't run `bd setup`: it writes its own boilerplate back into this file.

## Build and test

```bash
uv sync --group dev --frozen   # install the package and the development tools
uv run pytest                  # run the tests
make pre-push                  # what CI runs: tox (black, ruff, pyright, pytest), coverage (80% required), spelling
```

## Conventions

- Two libraries depend on the numbers computed here, and oilpaint checks its pictures byte for byte. A change that alters a result of `spectral`, `spline`, `noise` or `filters` is a breaking change: say so in the changelog and check both libraries.
- Kernels are `@njit(cache=True, error_model="numpy")`, without `fastmath` and without `parallel`, so that results repeat exactly.
- ruff caps function complexity at 13.

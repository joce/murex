# Handoff, 23 November 2026

For whoever picks up murex next. `AGENTS.md` holds the rules; this says where the work stands and what the last session learned. Delete this file once it has been read and acted on.

## Where things stand

`main` is at pull request #31. Nothing is in flight: no open pull request, no agent running, no unmerged branch worth keeping.

The last session ran from #23 to #31, all but one on `murex.huile`'s palette knife:

| Pull request | What it did |
|---|---|
| #23, #24, #26, #27, #28 | A knife's skim, drag and lumps no longer depend on the step (murex-iaa, murex-sdz, murex-86z, murex-kau, murex-6fa). |
| #29, #30 | The canvas goes on past its edge: a knife or brush at the edge paints as on a larger canvas (murex-duo, murex-n6o and three more). |
| #31 | A knife blade's stroke gives the same result however it is cut into steps: within 1.5% for paint carried and laid, where it was up to 12% and 37% (murex-5gw, murex-dq0). |

None of this changes a picture much at arm's length. It is footing for the knife work that will: the Bob Ross mountain.

## Open issues (14)

Waiting on the owner:

- **murex-bua** (P2): the owner provides an image of a Bob Ross mountain. It is the reference for the knife work, and blocks murex-dnj (a skimming knife breaks in patches) and murex-bja (ribbing as stick-slip of stiff paint). Where the image is kept is undecided; it is copyrighted, so outside the repository is the safer place.
- **murex-9t4** (P3): a stroke's textures depend on how it is cut into steps. Fixing it alters every huile picture, so it needs the owner's go-ahead.
- **murex-1gp** (P3): the owner tries white wax over heavy graphite by hand.

Knife, ready but of little visible worth until the reference image is there:

- **murex-dl9** (P3): a loaded knife leaves a heap where the pull stops. The owner chose to leave it rather than lay it out automatically, which cost 5 to 41% of what loaded pulls carry. Still open: neither easing the pressure nor `lift` lays it off.
- **murex-h6u** (P3): the riding blade's sub-steps show as ripple. The same at every cut now, but at a stroke's own steps slightly larger than before. Halving `RIDE_CFL` cures it and costs about 30% on knife scenes.
- **murex-ffp** (P3): a comb knife still depends strongly on the cut (a factor 2.5). Blades were fixed in #31, combs were not touched.
- **murex-088** (P3): a knife stroke on uneven wet paint does not vary continuously with its path. #31 removed the one reproducer that was run; not shown closed.
- **murex-uof** (P4): the pressure under a knife (Reynolds lubrication).

Elsewhere:

- **murex-sc8**, **murex-zvp** (P3): fusain's pastel pencils, the chalk crayons and colours. Independent of the knife, different files, and they produce something to look at. The best candidates to start next.
- **murex-6wh** (P3): calibrate graphite tones against scans of real pencil. Needs scans.
- **murex-252** (P4): places a last bit could still decide an outcome.

## Known limits of the knife, as of #31

All are in the changelog with their figures.

- Edge-on drags (a blade pulled along its own length) carry and move up to about twice what they did. The spill now takes the paint that lay there before the blade's own film: a reading of the model, not forced by it.
- Cut-independence is weaker on thin paint in patches (13%) and for a wide blade leaving over the edge (10%).
- Knife pulls over dried relief take up to 2.7 times the processor time.
- Paint is kept no further than 128 px past the canvas edge (`_knife._KEPT_FAR`). Strokes that reach further lose what they leave there.

## How the work was run

One coordinating session, with agents doing the work:

1. An author agent in its own worktree, branched from `origin/main`, told not to push, open pull requests, change issues or commit images. It writes before, after and difference pictures to the scratchpad.
2. The coordinator shows the pictures to the owner.
3. A fresh, independent reviewer gets the diff and questions, not the author's conclusions. It measures with its own scripts and marks each finding as caused by the change or already so, and as "must fix" or "acceptable".
4. Findings go back to the same author as new commits. Repeat until clean.
5. The coordinator lands it: applies the diff on the session's branch, closes the issues, regenerates every image of `examples/huile/output/`, runs the checks, opens the pull request, and squash-merges on green CI.

What held up well:

- The independent reviewer found real faults in every change: false conservation, out-of-bounds reads, a behaviour change of tens of percent the author had measured only on smooth grounds.
- "Step independence" as the criterion: own steps against cuts of 4, 2, 1 and 0.5 px with the `same_textures` fixture.

## What to do differently

The session ran well over a day for a small visible result. The causes, plainly:

- **Too much process for small fixes.** The strongest model as author and a deep review each round is right for kernel rewrites, not for narrow fixes. Use a lighter author and a single review unless the change rewrites a mechanism.
- **Serial by construction.** Every knife change touches `_knife.py` and `_engine.py`, so agents could not run side by side. Pair one knife task with one fusain task instead.
- **Building before measuring the cost.** The automatic lay-out of the end heap was built in one round and removed in the next, once it was known to cost up to 41% on loaded pulls. Ask the author for the cost of a mechanism on ordinary strokes before asking for the mechanism.
- **Measuring on convenient grounds.** Authors measured on smooth knifed slabs; the trouble was on brushed, textured grounds. Require both in the brief.
- **Polishing without a reference.** The knife residuals were worked in order of the issue list, not of worth. Until murex-bua's image is there, more knife polish has nothing to be judged against.
- **Fixed cost per landing.** Regenerating the images, the checks and CI take about an hour each time. Land fewer, larger changes.

One rule came out of it and is now in `AGENTS.md`: what a change breaks is fixed in that change, and no follow-up issue is filed for it. An issue is only for what was already so before.

## Practical notes

- The scratchpad fills the disk: agents keep arrays there. Delete the scratch of merged work as you go.
- `black` walks into the agents' checkouts under `.claude`: run it with `--extend-exclude .claude`, and use `make coverage spell-changed` in the main checkout rather than `make pre-push`.
- Push images with `git lfs push origin BRANCH` before `git push`.
- A bot reviews each pull request when it opens, not on later pushes. Verify its findings before acting on them.
- CI takes about 12 minutes.
- An agent may refuse to edit `AGENTS.md` policy on a relayed instruction. That is correct; the coordinator adds such lines.

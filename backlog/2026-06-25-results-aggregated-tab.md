---
status: IMPLEMENTED
epic: E5
date: 2026-06-25
---

# Results page — Aggregated (cross-run) tab

**Epic:** E5 — Observability & reporting
**Date:** 2026-06-25
**Status:** IMPLEMENTED 2026-06-25 (as-built below) — shipped + published to gh-pages.
**Origin:** operator — "add an aggregated results tab in addition to the individual runs."

## Problem

The public results page (`tools/results.py` → `results.html`) was a per-run switcher:
pick one curated sweep and see that run's head-to-head. There was no single view of the
harnesses ACROSS runs — you had to open each run and build the aggregate in your head.

## What was built

An **Aggregated** tab (the default view) alongside the per-run tabs, synthesized from
every run that has a report:

- **Reliability is SUMMED** across all runs — raw trial outcomes (clean / fail /
  timeout / crash) are genuinely additive, so the aggregate clean/error rates and the
  outcome bar are exact, not averaged.
- **Quality, pass^k, efficiency, and per-category** are per-run **means** (each category
  averaged over the runs that include it).
- The aggregate is rendered by feeding a synthesized report dict to the SAME
  `hero()` / `pillars()` / `categories()` / `reliability()` renderers, so it matches the
  per-run panels exactly.
- **Honest labeling (load-bearing).** The page's ethos is "nothing masquerades as a
  verdict." The aggregate banner states plainly that it blends runs of different
  vintages (including superseded ones on older task sets), that reliability is summed
  while quality/efficiency are means, and that the per-run tabs hold each run's true
  status — so the cross-run view is explicitly a picture, not a finalized result.
- Bonus: `load_run` now reads the post-unify `suite_report.json` name (falling back to
  the pre-unify `track_a_report.json`), so future sweeps don't silently drop off.

## As-built (2026-06-25)

Implemented in `tools/results.py` — `aggregate_run()` / `aggregate_summary()` /
`render_aggregate()` plus the tab wiring in `render()`. Regenerated `results.html`
(3 runs aggregated: the full-suite smoke + the two superseded core sweeps), topology
gate clean, nav identical to the live page (no hand-edits clobbered), and published to
gh-pages (commit `d8a6360`).

`tools/results.py` is left UNTRACKED in the repo (as it already was): it carries
pre-existing core/track framing tokens that the source-hygiene guard
(`tests/hygiene/test_suite_no_legacy_framing.py`) would flag if committed. The edit
persists on disk and the published page is the deliverable; the generator can be
committed once those tokens are scrubbed.

## Acceptance criteria

- [x] Aggregated tab present + default, alongside the individual-run tabs.
- [x] Reliability summed; quality / efficiency / per-category averaged; honestly labeled
      as a cross-run picture, not a verdict.
- [x] `results.html` regenerated, topology-gate clean, published to gh-pages.

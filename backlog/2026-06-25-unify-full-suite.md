---
status: IMPLEMENTED
epic: E4
date: 2026-06-25
---

# Unify the full test suite — remove "core eleven vs non-core" AND Track-A/Track-B

**Epic:** E4 — Task Suite (validity)
**Date:** 2026-06-25
**Status:** IMPLEMENTED 2026-06-25 (commit `7be4767`; as-built below) — originally APPROVED 2026-06-25 — operator directive: "remove all concept of eleven
core vs twenty-one non-core; have a full test suite; every single task is valid and
important to work on." Two forks resolved same-day: (1) scrub **live + forward**
material, leave dated backlog specs as historical record but **note the framing is
deprecated**; (2) **collapse Track-A/Track-B too** — one unified bar.
**Origin:** the core-eleven was a curated discriminator subset (`configs/core-suite.yaml`)
with the other 21 as "non-core," and tasks were further split Track-A
("must discriminate") vs Track-B ("valid general-capability"). The operator wants
**one full suite of equally-important tasks under one validation bar.**

## Decision (what "unified" means)

- **One suite.** All **33 active eval tasks** (`tasks/**/task.toml`, minus the 2
  `_verify` fixtures) are *the suite*. No privileged subset, no "core"/"non-core".
- **One bar.** Every task must be **valid + graded + ungameable**: flat numeric
  `reward.json` + `answer_present`; no telegraphing; no bypass/grader-gaming;
  format-robust; crash fallback; `FROM harbor-agents-rich`; topology-clean. **Whether
  a task discriminates the harness is an OUTCOME measured per-task at n≥3 — not a
  pre-assigned track.** Delete the Track-A/Track-B labels and the
  must-discriminate-vs-general framing.
- Approval gate is unchanged in spirit: `approved=true` after the task's **oracle =
  1.0** AND an **n≥3** run shows it behaves as intended (graded, ungameable, and — if
  it's meant to — separates the harnesses).

## Work list

Mechanical scope is broad; keep the 244 offline tests green and topology clean
throughout. **Behavior of task graders/fixtures must not change** — this is a
rename/reword/de-tier refactor, not a grading change.

1. **Docs (live):**
   - `RESULTS.md`: replace "11 core + 21 non-core" / "core suite" / Track-A/Track-B
     with "the suite (33 tasks)" + the single bar; the validation ladder stays, but
     Tier-3/4 language drops track tiers (discrimination is per-task outcome).
   - `AGENTS.md`: drop the "core suite" selection framing + Track-A/Track-B in the
     methodology; describe one full suite + one bar. Update the "Running a sweep"
     command to the renamed driver/config (below).
2. **Configs (rename + consolidate):**
   - `configs/core-suite.yaml` → **`configs/suite.yaml`** = the canonical sweep config:
     all 33 eval tasks (the union currently in `smoke-n1.yaml` + the 11), both
     harnesses (thin + deepseek-v4-pro), `n_attempts` overridable.
   - `configs/core-suite-claude.yaml` → `configs/suite-claude.yaml`.
   - Retire the track configs: `track-a-harness.yaml`, `track-a-focused.yaml`,
     `track-b-general.yaml`, `oracle-core.yaml` (superseded by `oracle-full.yaml`).
     `track-a-weights.toml` → `suite-weights.toml` (drop track partitioning; if
     per-category weights remain, keep them under the neutral name).
   - `smoke-n1.yaml` stays as the n=1 form (or fold into `suite.yaml` + `N_ATTEMPTS=1`);
     `oracle-full.yaml` stays (the oracle).
3. **Driver + metrics (rename, update all refs):**
   - `tools/run_track_a.sh` → **`tools/run_suite.sh`** (update every doc/comment/config
     reference; keep behavior identical — Infisical + wipe/seed hooks + one-job-per-harness).
   - `metrics/track_a_weighted.py` → `metrics/suite_weighted.py` (+ its `track_a_report.json`
     output → `suite_report.json`); update importers.
4. **task.toml:** remove any `[metadata]` `track`/`core`/tier flag; keep
   `approved`/`status`. (Discrimination is no longer a task attribute.)
5. **Offline tests (`tests/`):** rename `noncore.py`→`suite_helpers.py`,
   `test_noncore_*`→`test_suite_*` and fix all imports; the `tests/{s4,wipe,regrade,
   exploits,hygiene}` suites keep their assertions (behavior unchanged), only the
   "noncore"/"core" naming goes. Add one **acceptance guard test** that greps the live
   tree (excluding `backlog/` + `archive/`) and FAILS if "core eleven", "non-core",
   "Track-A/Track-B", "core-suite", or "run_track_a" reappear.
6. **Dashboards:** `tools/roadmap.py`, `tools/task_catalog.py`, `tools/agent_status.py`
   — remove core/non-core + Track-A/B grouping; present one suite. Regenerate the HTML.
7. **Backlog (historical — DO NOT rewrite bodies):** add a deprecation banner to
   `backlog/README.md` and a one-line note at the top of the core-eleven / core-suite /
   noncore specs: "**DEPRECATED FRAMING (2026-06-25):** the core/non-core split and
   Track-A/Track-B are retired — see `2026-06-25-unify-full-suite.md`; the suite is now
   unified." The dated content stays as the accurate record of what happened.

## Acceptance criteria

1. **No live mention** of "core eleven", "non-core"/"noncore", "Track-A"/"Track-B"/
   "track_a"/"track-b", "core-suite", or "run_track_a" anywhere outside `backlog/` and
   `archive/` (the guard test enforces this; `check_topology.sh`-style grep clean).
2. **244 offline tests green** under the renamed files/imports; the new guard test passes.
3. `configs/suite.yaml` covers all 33 eval tasks, both harnesses; `tools/run_suite.sh`
   runs it; `oracle-full.yaml` still oracle-validates.
4. RESULTS.md + AGENTS.md describe one suite + one bar; reproduce commands use the new
   names. Dashboards regenerate without track/core grouping.
5. Backlog specs carry the deprecation note; their dated bodies are unchanged.
6. Topology gate clean; no behavior change to any task grader/fixture (oracle still
   1.0 on the same tasks — spot-check, full oracle is a post-merge gate).

## Out of scope

Task grader/fixture *behavior* (this is naming/de-tiering only); rewriting dated
backlog spec bodies; the both-zero fixes + n≥3 run (separate, tracked in RESULTS.md
"Open work"); any harness/substrate change.


## As-built (2026-06-25 — commit `7be4767`)

Single rename/de-tier refactor; grader/fixture behavior unchanged.

- **Configs:** `core-suite.yaml`→`suite.yaml`, rebuilt to cover **all 33** active
  tasks (the prior 11 + 21 + `prod-behavioral/basic-knowledge-qa`, which *neither*
  old config listed); `core-suite-claude`→`suite-claude` (kept as a cost-bounded
  alt-model subset); `track-a-weights`→`suite-weights`; retired `track-a-harness`,
  `track-a-focused`, `track-b-general`, `oracle-core`.
- **Driver/metrics:** `run_track_a.sh`→`run_suite.sh` (CONFIG default→`suite.yaml`,
  WEIGHTS→`suite-weights.toml`); `track_a_weighted.py`→`suite_weighted.py`
  (`track_a_report.json`→`suite_report.json`).
- **Tests:** `noncore.py`→`suite_helpers.py`; 8 `test_noncore_*`/`test_s1_noncore_wipe`
  → `test_suite_*`; imports + function names fixed; `test_s5_drift` repointed to
  `suite.yaml`. NEW acceptance guard `tests/hygiene/test_suite_no_legacy_framing.py`.
- **Dashboards:** `roadmap.py`/`task_catalog.py` de-tiered; `task_catalog` dropped the
  Track-A "focused n=5" set (it read the retired `track-a-focused.yaml`). HTML regen'd.
- **Docs:** RESULTS.md, AGENTS.md, README.md → one suite + one bar; CLAUDE.md restored
  to a symlink → AGENTS.md.
- **Backlog:** deprecation banners on the core-eleven/core-suite/noncore specs + README;
  dated bodies unchanged.

**Verification:** 252 prior offline tests still green + the new guard = **253 passed**
(`pytest tests/`); topology gate clean; guard confirms zero live framing mentions.

**Deviation:** acceptance #1 ("no live mention") reconciled with item 7 ("keep backlog
filenames + facts") — the guard strips dated spec-slug citations (`YYYY-MM-DD-…[.md]`)
before matching, so code/configs/tasks may still cite a spec by slug as provenance.

**Not done here** (explicit post-merge / operator gates, criteria #3 + #6): the live
`tools/run_suite.sh` sweep and the full Docker oracle (`oracle-full.yaml`). The driver +
config are wired for both.

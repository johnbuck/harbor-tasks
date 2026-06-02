# Task Suite page (was "Task Catalog") — visual review + work tracker for every eval task

**Epic:** E5 — Observability & reporting
**Status:** first draft shipped 2026-05-31; **evolved to the "Task Suite" view 2026-06-02** (renamed, card→accordion, work-status + operator-approval axes — see Revision history).
**Sibling of:** `tools/agent_status.py` → `agent-status.html` (the harness-status board).
**Generator:** `tools/task_catalog.py` → `task-catalog.html` (filename unchanged; the page now *titles* itself "Task Suite").

## Problem

We have 48 tasks across 19 categories in `tasks/`, authored over several weeks in
two formats (single-step `task.toml` + multi-step `[[steps]]`). The only ways to
review what a task actually *does* today are (a) opening each task's files by hand
or (b) reading a finished job's trial transcripts in the `harbor view` dashboard —
both per-task, neither giving a human a single "here is the whole suite, in detail"
view. The operator asked for a page where **every job/test we created can be
reviewed visually, with a super-clear definition of each**, so a human can audit
the suite for coverage, grading correctness, and discrimination intent.

This is a **definition** view (what each task asks, how it's graded, what the
oracle is), NOT a **results** view (that's the `harbor view` dashboard on :8089).
The two are complementary.

## Goals

1. One self-contained static HTML page listing **every** task in `tasks/`
   (excluding the `_verify` scaffold), grouped by category.
2. For each task, surface — without leaving the page — the four things a reviewer
   needs to judge it:
   - **What is asked** — full `instruction.md` (every step, for multi-step).
   - **How it's graded** — the verifier/`reward.json` logic verbatim, plus a
     derived **Graded vs Binary** badge (graded = emits a fractional reward;
     binary all-or-nothing tasks are the ones that go BLUNT — see the discriminating
     suite spec).
   - **The oracle** — `solution/solve.sh` (or per-step solutions).
   - **The environment** — `environment/Dockerfile` (confirms `FROM
     harbor-agents-rich:latest`; a prebaked/other base is the #1 silent footgun —
     see `harbor-tasks-rich-base-required`).
3. Show each task's **discrimination metadata**: category weight (from
   `configs/track-a-weights.toml`), `harness-discriminating` tag, difficulty,
   multi-step + step count, and whether it's in the focused n=5 set
   (`configs/track-a-focused.yaml`).
4. **Accessible from the same area** as the agent-status board: all pages carry a
   shared top nav (`Agent status` · `Task Suite` · `Roadmap`).
5. Client-side filter/search (by category, difficulty, graded, discriminating,
   focused, free text) so a reviewer can slice the 48 quickly.
6. Drift-proof: read entirely from the on-disk task tree + config files at generate
   time. No hand-typed task data (same principle as `agent_status.py`).

## Non-goals

- No run results, scores, or pass^k here — that's the results dashboard.
- No live container introspection (unlike `agent_status.py`, this reads only the
  repo, so it's fast and needs no docker).
- Not wired into `harbor view`'s server — it's a static file opened from disk or
  served from the repo root alongside `agent-status.html`.

## Design

`tools/task_catalog.py` (stdlib only: `tomllib` for `task.toml`, manual scan for the
focused-set YAML so there's no `pyyaml` dependency):

**Discovery.** Walk `tasks/*/<task>/task.toml`. Skip `tasks/_verify/`. For each:
- Parse `[task]` (name, description, keywords), `[metadata]` (difficulty, category,
  shape, tags), and `multi_step_reward_strategy`.
- Multi-step iff a `steps/` dir (or `[[steps]]`) exists; step count = number of
  step dirs.
- Category weight = `configs/track-a-weights.toml` lookup (default 1.0 if absent).
- Focused-set membership = task name ∈ `configs/track-a-focused.yaml` `task_names`.

**File embedding (modal viewer, same pattern as `agent_status.py`).** Collect, per
task, the reviewer-relevant files and embed their contents in a JS map keyed by an
index; a chip click opens the existing modal. Files collected:
- single-step: `instruction.md`, `tests/*` (verifier), `solution/*`,
  `environment/Dockerfile`.
- multi-step: `environment/Dockerfile`, and per step `steps/NN-*/instruction.md`,
  `steps/NN-*/tests/*`, `steps/NN-*/solution/*`, `steps/NN-*/workdir/setup.sh`
  (the pre-agent state reset — the cheat-proofing that makes context tasks real).
- Each file is truncated at ~80k chars (same cap as agent-status).

**Graded-vs-binary detection.** A task is "graded" if any verifier file emits a
non-constant reward — heuristic: the reward line references a computed fraction
(`round(`, `/N`, a `$s`-style accumulator, or `reward` set from a variable rather
than a literal `0`/`1`). Surfaced as a badge; reviewers can open the verifier to
confirm. (Heuristic only — the badge is a hint, the embedded verifier is truth.)

**Layout.**
- Shared nav header (links to `agent-status.html`).
- Summary strip: total tasks, # categories, difficulty histogram, # multi-step,
  # graded, # harness-discriminating, # in focused set.
- Filter bar (category select, difficulty select, toggles for graded /
  discriminating / focused, free-text search) → client-side show/hide via
  `data-*` attributes.
- Category sections ordered by weight desc; each header shows weight + count.
- Task card: name, shape, difficulty badge, weight, single/multi (+step count),
  graded/binary badge, discriminating + focused badges, full description, a
  step list (multi-step) with each step's instruction snippet, and a row of file
  chips (instruction / verifier / solution / Dockerfile / per-step).
- Modal viewer reused verbatim (showFile / Esc-to-close / `<\/` script-escape).

**Style.** Reuse the agent-status dark palette and chip/badge/modal CSS so the two
pages read as one tool.

## Refresh

```bash
python3 tools/task_catalog.py            # writes task-catalog.html
python3 tools/task_catalog.py --open     # + open in browser
```

Re-run after authoring/editing any task. No docker, no network.

## Revision history

**2026-06-02 — "Task Suite" view (granular work + approval tracking).** The page
grew from a static *definition* index into the granular **work tracker** for the
Task Suite epic (E4). Changes:

- **Renamed** the visible title + nav label `Task catalog` → **`Task Suite`** (the
  `task-catalog.html` filename and `tools/task_catalog.py` generator are unchanged,
  so no links break). All three dashboards' shared nav updated.
- **Card grid → accordion.** Each task is now a collapsed row (name + status
  badges); click expands to the full detail (work note, description, steps, tags,
  file chips). Added expand-all / collapse-all. Scans 52 tasks at a glance.
- **Work-status axis** (derived, like the graded badge; overridable via
  `[metadata] work_status`): one of `discriminating` (tagged harness discriminator,
  pending grid confirmation), `needs-validation` (graded, not yet proven to
  separate the harnesses), `needs-hardening` (binary / likely BLUNT), `retired`
  (deprecated by the adversarial review, pending rework — task #89). Surfaced as a
  header badge + an expanded "Work:" note + a summary "work remaining" count + a
  filter. This is the per-task answer to "what's done vs. what's left."
- **Operator-approval axis.** Every task shows **NEEDS REVIEW** until its
  `task.toml` sets `[metadata] approved = true` (absence ⇒ not vetted). Surfaced as
  the leading header badge, a summary count, and an approval filter. Opt-in, so no
  bulk file churn — the operator approves tasks one at a time as they vet them.

Both new axes are orthogonal: a task can be a tagged discriminator (work-status)
yet still un-vetted (NEEDS REVIEW). Both read from `task.toml` at generate time, so
they can't drift.

## Follow-ups (not yet done)

- Link each task row to its latest trial result in the `harbor view` dashboard
  (needs a stable task→job URL scheme).
- Render the graded-vs-binary badge from an actual dry-run of the verifier against
  the oracle output rather than the source heuristic.
- A "coverage matrix" (category × difficulty × graded) heatmap at the top.

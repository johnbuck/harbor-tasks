# Roadmap page — the plan/progress view, by epic

**Epic:** E5 — Observability & reporting
**Status:** IMPLEMENTED 2026-06-02.
**Sibling of:** `tools/agent_status.py` → `agent-status.html` (the HARNESS view) and
`tools/task_catalog.py` → `task-catalog.html` (the TASK SUITE view).
**Generator:** `tools/roadmap.py` → `roadmap.html`.

## Problem

The repo had two status surfaces — the harness board and the task catalog — but no
**plan** view: nothing answered "what's the overall thesis, which epics make up the
work, what's done, and what's blocking the next trustworthy run?" The backlog holds
~28 per-feature specs but a reader had to open each to reconstruct the shape of the
project. The operator asked for a clear, simple roadmap that represents the work
completed thus far and what remains, broken out by epic.

## Goals

1. One self-contained static HTML page (same dark palette + shared nav as the other
   two dashboards) stating: the **thesis**, a **"where we stand right now"** callout
   at the top, the **epics**, and a short milestone read.
2. Break the work into **epics**; under each, list **every backlog spec** that rolls
   up to it, with a per-spec status dot (done / in progress / blocked / to do /
   deprecated).
3. Each spec row is an **accordion**: click to expand a curated one-paragraph detail,
   plus an **"open full spec"** button that shows the *entire* backlog `.md` in a
   modal (content baked in at generate time → works offline, no server).
4. Stay honest: status labels mirror reality, not optimism (the broken provider pin
   and the unsurfaced openclaw browser show as `blocked`, not `done`).

## Design

`tools/roadmap.py` (stdlib only). Unlike the other two dashboards, the epic→spec
mapping + per-row detail are **hand-curated** in an `EPICS` table at the top of the
generator (it's a narrative, not drift-derived) — but each row references a real
`backlog/` file, and that file's full text is read from disk and embedded at
generate time, so the "open full spec" modals never drift from the specs. Edit the
`EPICS` table and re-run.

### The epic model (current)

| Epic | Title | Gist |
|---|---|---|
| E1 | Harness runtime & adapters | Run both harnesses identically on Harbor (foundation). |
| E2 | Fair-comparison controls | Same model, same provider pin, isolated state. |
| E3 | Capability infrastructure | Recall memory + the shared browser the harnesses use. |
| **E4** | **Task Suite** | Author the tests AND prove they measure the harness — one feedback loop. |
| E5 | Observability & reporting | The three dashboards + the published RESULTS.md verdict. |

**E4 is a merge.** "Task suite authoring" and "Discrimination & validity" were
separate epics until 2026-06-02; they were merged into one **Task Suite** epic
because authoring and validity are a single feedback loop (a blunt task routes
straight back to re-authoring). Observability was renumbered E6→E5 at the same time.

### Epics live in two places, kept in sync

- **Source of truth for presentation:** the `EPICS` table in `tools/roadmap.py`.
- **Per-spec documentation:** every backlog spec carries an `Epic:` line in its
  frontmatter (e.g. `Epic: E4 — Task Suite`). The backlog directory stays **flat**
  (no per-epic folders); epic membership is documented per-spec, not by folder.
  Convention recorded in `backlog/README.md`.

A spec referenced by two epics (e.g. the tau3 spec, an E4 task + the deprecated E1
adapter row) is tagged with its **primary** epic in frontmatter.

## Refresh

```bash
python3 tools/roadmap.py                 # writes roadmap.html
```

Re-run after any backlog change (so the embedded full-spec modals stay current) or
after editing the `EPICS` table. No docker, no network.

## Non-goals

- Not a results view (that's `harbor view` / RESULTS.md) and not a live tracker —
  it's a hand-curated plan, refreshed on demand.
- Does not auto-derive epics from frontmatter (the curated detail/status per row is
  richer than frontmatter); the `Epic:` tags are the reverse documentation.

## Follow-ups

- Optional: a lint that checks every spec's frontmatter `Epic:` matches the epic it
  appears under in `EPICS` (today they're kept in sync by hand, derived from the
  same table when tagging).

# Context-rot scoring integrity — false-zero audit + metric normalization

**Epic:** E4 — Task Suite
**Status:** PARTIAL — audit grader + result correction SHIPPED 2026-06-02; metric
normalization PROPOSED (task #93).
**Date:** 2026-06-02
**Origin / triggered-by:** reviewing the context-rot runs in `harbor view`, a hermes
trial showed reward 0 after burning huge tokens; investigation found the 0 was an
instrument artifact, not a hermes failure.

## Problem

Three distinct scoring-integrity bugs surfaced on the `context-rot` tasks, each of
which can fabricate or distort a harness "gap":

1. **False zero from non-persisted answer.** On `context-rot-02` (the 8-chain
   multi-hop variant), hermes recalled **all 8 chains correctly** (recovered verbatim
   from `agent/trajectory.json`) and wrote them to `/app/answer.md`, but its staged
   diff-write never landed in `/app`, so the verifier read an **empty file** and scored
   **0**. openclaw's direct write landed → 0.875. Result: a `0.875`-vs-`0` "gap" that
   was **pure plumbing**, not context-rot capability. The recall grader scored a
   missing/empty file identically to a wrong answer — silently.
   - (The hermes *write-persistence* root cause is tracked separately as **task #92**.)

2. **`rewards` schema is strict.** `harbor.models.verifier.result.VerifierResult.rewards`
   is typed **`dict[str, float | int]`**. A first version of the audit grader emitted a
   string `status` field; that makes `TrialResult.model_validate_json` raise, and the
   viewer's scanner then **silently drops the whole trial** ("Failed to parse trial
   result"). A bad reward.json doesn't show an error in the UI — the trial just vanishes.

3. **Cross-task metric blending.** A job groups both context-rot tasks under one eval
   key (`…__context-rot`). `context-rot-01` scores **`facts`** (12-fact recall, no
   `chains`); `context-rot-02` scores **`chains`** (8 chains, no `facts`). Harbor's
   default `Mean` metric averages every key over **all** trials, scoring a *missing*
   key as **0**. So `chains` = (0 + 8)/2 = **4.0** and `facts` = (12 + 0)/2 = **6.0** —
   both meaningless. Only `reward` (already normalized to [0,1]) is trustworthy across
   tasks. The raw-count sub-metrics (`facts`, `chains`, `early/middle/late`) are
   task-specific counts on different scales and must not be blended.

## What shipped (2026-06-02)

- **Audit grader** (commits `3b2d93d`, `1a29a8c`) on both
  `tasks/context-rot/context-rot-0{1,2}/steps/19-recall/tests/test.sh`:
  - `cp /app/answer.md` into the persisted verifier dir → the raw answer is **auditable**.
  - emits numeric `answer_present` (1/0) + `answer_chars`; **`answer_present == 0` is the
    "agent never persisted an answer" (VOID) signal**, distinct from a present-but-wrong 0.
  - audit fields kept **numeric only** (string `status` removed) so `rewards` stays
    `dict[str, float|int]`. Validated against the real `VerifierResult` model + 3 cases.

- **Data correction (transparent stopgap, NOT a code change).** The recorded
  `context-rot-02` hermes trial was corrected 0 → 1.0:
  - recovered answer archived at `steps/19-recall/verifier/answer.md`;
  - per-trial `result.json` + step-19 `reward.json` updated to the re-scored 8/8;
  - the **job-level** `jobs/ctx-rot-n1__hermes/result.json` is a SEPARATE cached
    aggregate — regenerated from the corrected trials with Harbor's own
    `JobStats.from_trial_results()` + `Mean().compute()` (reward mean 0.5 → **1.0**);
  - originals preserved as `result.json.orig-falsezero` + `CORRECTION.md` in each dir.
  - `jobs/` is gitignored, so these are local-only corrections.
  - **Caveat:** hand-patching recorded runs is a stopgap. The durable source of truth is
    a **re-run** of `context-rot-02` hermes once task #92 lands.

## Proposed (task #93) — metric normalization

Make the cross-task aggregates meaningful instead of blended:

- Both context-rot graders emit a **shared, normalized recall metric** (fractions in
  [0,1], identical key names across tasks) — e.g. `recall` (= reward), plus normalized
  `early/middle/late` fractions. Drop the task-specific raw counts (`facts`/`chains`)
  from the scored `rewards`, or rename to one shared key, so there are **no missing-key
  zeros** to average.
- Keep the **audit fields out of the scored `rewards`** so `answer_present`/`answer_chars`
  stop polluting job-level metric means (today they average to `0.5` / `42.5`). Options:
  a separate sidecar file, or a reserved non-aggregated namespace.
- Re-score existing context-rot trials under the new keys (or re-run).
- Do **not** change Harbor's global `Mean` to "average over present keys only" — for
  pass-rate metrics, missing-as-0 (an errored trial = failure) is intentional; changing
  it globally would silently inflate other jobs' pass rates.

## Design decisions

- **Soften/audit, never hide.** A 0 must be self-describing: `answer_present` distinguishes
  VOID (plumbing) from a real miss, and the raw answer is archived for inspection.
- **Numeric-only rewards.** Anything written to `reward.json` flows into
  `VerifierResult.rewards` (strict `dict[str,float|int]`) — strings/bools/nesting break
  the whole trial's parsing in the viewer. Provenance/notes go in sidecar files.
- **Regenerate, don't hand-edit, job aggregates.** The job-level `result.json` is derived;
  use `JobStats.from_trial_results()` + the dataset `Mean` so it stays consistent.

## Acceptance criteria

- [x] Recall grader archives `answer.md` and emits numeric `answer_present`/`answer_chars`;
      validated vs the real `VerifierResult` model + correct/empty/missing inputs.
- [x] hermes `context-rot-02` recorded result corrected to 1.0 (trial + job aggregate),
      with originals + `CORRECTION.md` preserved.
- [ ] **Normalized shared recall metric across both context-rot tasks; audit fields out
      of scored rewards; existing trials re-scored or re-run** — task #93.
- [ ] hermes `context-rot-02` re-run cleanly once write-persistence (task #92) is fixed,
      replacing the hand-patched result.

## Findings worth remembering

- The `0.875`-vs-`0` "gap" was a **false zero**; hermes actually scored **8/8** on
  context-rot-02 (beating openclaw's 7/8). A lone 0 on a completed multi-step trial is a
  prime construct-validity trap (task #79) — treat `answer_present==0` as VOID, not a loss.
- A multi-step trial that never reaches its scoring step (e.g. the aborted
  `ctx-rot-n1-hermes__hermes` run, killed at step 5/19) records no reward → defaults to 0;
  that is a VOID/abort to re-run, not a capability failure either.

## Follow-up tickets

- **task #92** — hermes write-persistence (staged diff-write not landing in `/app`).
- **task #93** — normalize context-rot recall metrics + keep audit fields out of scored
  rewards + re-score/re-run.

# Context-rot scoring integrity — false-zero audit + metric normalization

**Epic:** E4 — Task Suite
**Status:** SHIPPED 2026-06-02 — audit grader + result correction + metric
normalization (task #93) all landed. Only remaining open item is the hermes
`context-rot-02` re-run, which is blocked on write-persistence (task #92).
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

## What shipped (task #93, 2026-06-02) — metric normalization

Both recall graders (`context-rot-0{1,2}/steps/19-recall/tests/test.sh`) now emit a
`reward.json` containing **only normalized [0,1] keys with identical names across both
tasks**, so Harbor's per-key cross-trial `Mean` is comparable PER HARNESS:

| key | meaning | range |
|---|---|---|
| `reward` | overall accuracy (`correct / total`) | [0,1] |
| `correctness` | 1 iff every item solved | {0,1} |
| `early` / `middle` / `late` | per-depth accuracy = the rot curve (`bucket_correct / bucket_size`) | [0,1] |

Normalizing the depth buckets to **fractions** is what makes the rot curve comparable
across rot-01 (4 questions/bucket) and rot-02 (2–3 questions/bucket) — `middle: 0.0`
reads the same on both. No raw-count keys remain in the scored dict, so the
missing-key-averages-to-0 blend (`chains` 8→4.0, `facts` 12→6.0) is gone.

Everything else moved to a sibling **`reward-details.json`** written to the same
verifier dir but **never parsed into `VerifierResult.rewards`** (Harbor only reads
`reward.json`/`reward.txt`): raw `correct`/`total`, the task-specific count
(`facts`/`chains`), per-bucket `*_correct`/`*_total`, and the answer audit
(`answer_present`, `answer_chars`). It's downloaded with the rest of the verifier dir,
so a 0 is still fully auditable — it just can't masquerade as a score (`answer_chars`
85 → 42.5 is dead).

Validated against the real archived hermes `context-rot-02` answer (→ `reward 1.0`,
`early/middle/late 1.0`) plus a VOID case (all-0, `answer_present 0`) and a synthetic
middle-rot bare list (`reward 0.625`, `early 1.0 / middle 0.0 / late 1.0`).

- **Existing recorded trials are NOT re-scored in place** — the per-trial `reward.json`
  under `jobs/` still carries the old keys. The durable correction is a **re-run** under
  the new graders (cheap, deterministic). `reward` was always correct in the old data, so
  the headline per-harness comparison (hermes 1.0 vs openclaw 0.854) needs no patch.
- Did **not** change Harbor's global `Mean` to "average over present keys only" — for
  pass-rate metrics, missing-as-0 (an errored trial = failure) is intentional; changing
  it globally would silently inflate other jobs' pass rates. Fix stays grader-local.

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
- [x] **Normalized shared recall metric across both context-rot tasks; audit fields out
      of scored rewards** — task #93 (graders emit only `reward`/`correctness`/normalized
      `early`/`middle`/`late`; raw counts + answer audit moved to `reward-details.json`).
      Existing trials get the new keys on re-run (not back-patched).
- [x] **Live oracle validation (2026-06-03)** — both context-rot tasks run through the full
      Docker build + multi-step + verifier stack (`configs/validate-ctx-rot.yaml`, oracle, no
      LLM): `reward.json` = the 5 normalized keys only, `reward-details.json` sibling written
      + downloaded, job aggregate clean (no `chains`/`facts`/`answer_chars`), reward 1.0 both.
      Proves the #93 grader integration, not just the offline logic.
- [x] **Write-persistence (task #92) fixed + verified** — root cause was hermes's file
      tools being workspace-rooted at `terminal.cwd: "."` while the adapter never cd'd to
      the workdir (writes shadowed off `/app`). Fix: `cd /app` in `lib/hermes_thin.py`
      (commit e1c4541). Verified on the `_verify/file-persistence-01` probe: hermes
      `answer_present` 0→1, reward 1.0 (with openclaw + oracle 1.0). Also required re-pinning
      both harnesses deepseek→novita (deepseek endpoint went training-flagged → 404 under deny).
- [ ] hermes `context-rot-02` full re-run to replace the hand-patched stopgap result —
      now UNBLOCKED (#92 fixed); the ~$5 19-step run can fold into the core-suite n=1.
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

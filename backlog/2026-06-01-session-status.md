# Session status / next-session pickup (2026-06-01, pre-compact)

Single source of truth for where things stand. Read this first after the compact.

## Done this session (all committed + pushed to origin/main, each oracle-green)

### Context-ROT family (NEW category `tasks/context-rot/`)
The in-window sibling of the context-fill OVERFLOW family. Two rungs built:
- `context-rot-01` — positional / lost-in-the-middle; 12 paraphrased needles at
  early/middle/late depth; ~345K in-window; line-anchored /12 w/ early/middle/late
  subscores. Oracle 1.0. (commit 5d24888)
- `context-rot-02` — multi-hop; 8 two-hop chains via bridge entities; rot on
  either hop breaks the chain. Oracle 1.0. (commit 574649f)
- rot-03 (aggregation/distractor) — NOT built (operator chose "build 02 only,
  then reassess"; then approved the real n=1 instead).

### REBUILD trio (deprecated tasks with no other home → un-deprecated)
- `ops-debugging/failure-recovery-loop-01` → adaptive recovery (dfetch fails with
  different actionable errors; blind retry can't win → correctness discriminates).
  Oracle 1.0. (53c02d4)
- `ops-debugging/diagnose-from-logs-01` → narration stripped, ~100k-line buried
  corpus, computed-value anti-dump gate (~155s). Oracle 1.0. (22bc3eb)
- `real-world-workflows/update-record-with-cleanup-01` → answer-key leak removed
  (grader computes expected at grade time), scaled ~55 rows, per-decision credit.
  Oracle 1.0. (1717f02)

### Cover-task fixes (so the redundant deprecated tasks can later be dropped)
- `conversation-persona/multistep-memory-conversational-01/02/03` → added the
  SIBLING PENALTY the graders lacked (hedging/dumping both real+distractor value
  used to score 1.0). Also fixed 01's oracle being TRUNCATED to 6/12 answers (it
  was never green). All three oracle 1.0; honest descriptions. (1a793e4, e1eac24)

### Infra
- **Provider pin REBUILT + verified** under side tag `harbor-agents-rich:pinned-v2`
  (`only:[deepseek], allow_fallbacks:false` baked in BOTH harnesses). Confirmed the
  live `:latest` (2 days old) was genuinely UNPINNED — the regression was real, so
  every run since b11f743 (incl. the in-flight eval) is cost-contaminated (accuracy
  still valid). **PENDING: `docker tag harbor-agents-rich:pinned-v2
  harbor-agents-rich:latest` AFTER the in-flight eval finishes** (promoting mid-run
  splits the two harnesses across images). See memory [[harbor-provider-pin]].
- **Infisical Cloud purged** — every command now carries
  `--domain=http://internal-host:8380`; never Cloud. (bde3852) Memory
  [[feedback-infisical-never-cloud]].
- **Methodology evidence base** documented (`2026-06-01-methodology-evidence-base.md`)
  — harness-vs-model, pass^k (Sierra/τ-bench, NOT METR), telegraphing=construct
  validity, effective-window calibration, provider pin all sourced.

## ctx-rot n=1 real eval — COMPLETE (both harnesses) + a scorer bug found & fixed

The combined run finished BOTH harnesses (the original `bfpb67r6w` background
job completed ~18:15; an earlier mid-run check wrongly read its not-yet-flushed
result.json as "dead" and a redundant hermes-only re-run was launched, then
KILLED once the original was confirmed complete — no double-spend of note).

**RAW results as first graded (one BROKEN):**
| task | openclaw | hermes (raw) |
|---|---|---|
| context-rot-01 (positional) | 0.833 (E3/M4/L3) | 1.0 (E4/M4/L4) |
| context-rot-02 (multi-hop)  | 0.875 (E1/M3/L3) | **0.0 (0 chains)** ← FALSE ZERO |

**The hermes rot-02 0.0 was a SCORER FORMAT ARTIFACT, not a result.** hermes wrote
`answer.md` as a bare one-answer-per-line list (`Lyon`/`Jackfield`/…) — all 8
chains CORRECT — but the old scorer's `ans_line()` `grep -iE "^\s*N[.)]"`
REQUIRED a numbered prefix, so a content-perfect bare list scored 0/8. That fake
0.875-vs-0.0 "gap" would have been published as discrimination.

**FIX (this session):** both recall scorers rewritten format-robust — per
question, match an enumerated `N.` line if present, ELSE the Nth non-empty line
(positional fallback); strip markdown/enumerator before the pattern test.
Anti-dump preserved (each question maps to ONE line; a one-line blob of all
candidates scores 1/8, verified). Re-graded the SAVED answer.md files (no re-run,
$0): hermes rot-02 0.0 → **1.0 (8/8)**; oracles still 1.0; openclaw's genuine Q1
miss preserved at 0.875. Oracle re-validation in Docker: `jobs/oracle-rot0{1,2}-regrade`.

**CORRECTED, VERIFIED verdict:**
| task | openclaw | hermes |
|---|---|---|
| context-rot-01 (positional) | 0.833 (10/12) | 1.0 (12/12) |
| context-rot-02 (multi-hop)  | 0.875 (7/8)   | 1.0 (8/8) |

**ctx-rot is BLUNT for the openclaw-vs-hermes pair at ~345K.** Both harnesses
recall middle-buried, paraphrased facts near-perfectly; NO lost-in-the-middle
collapse for either; hermes is marginally ahead (missed no hop). At ~345K we're
just under the ~300–400K effective-window knee, and these strong harness+model
combos hold. To make the rot family discriminate it must push PAST the effective
window (bigger corpus, more needles) — otherwise it measures a model-strong,
harness-agnostic capability. Cost numbers from this run are NOT trustworthy
(unpinned `:latest`); accuracy is.

**Methodology lesson (durable):** a position/line-anchored recall scorer that
REQUIRES one specific answer format manufactures false zeros when a harness picks
a different (content-correct) format — and false zeros masquerade as harness
discrimination. Recall scorers must grade CONTENT and tolerate format. See memory
[[harbor-recall-scorer-format-robust]].

## Open work (priority order)
1. **Promote the pin:** `docker tag harbor-agents-rich:pinned-v2
   harbor-agents-rich:latest` — safe now (the symmetric ctx-rot run is done). Do
   before any cost-sensitive grid. (Accuracy verdict above does not need it.)
2. **Deprecated-set remainder** (matrix `2026-06-01-retired-task-coverage-matrix.md`):
   - ✅ Run-config exclusion DONE — `tools/run_track_a.sh` auto-excludes
     `status=deprecated` (scans dataset dirs, injects `exclude_task_names`);
     `INCLUDE_DEPRECATED=1` opts out. Verified 20 excluded, REBUILD trio active.
   - Track B for the 5 authoring tasks (email-copy, restore-runbook, api-contract,
     cli-tool, readme) — destination set, not stood up.
   - Larger cover-task reworks gating the 15 redundant drops: refactor-multi-file,
     pr-diff-review, unit-tests, dep-bump, plan-then-revise, tool-selection,
     tool-sprawl, sub-agent-parallel (inert concurrency axis). Not started.
3. **Nothing removed** until each retired task's named alternative is green.
4. Eventually: n=5 pass^k grid (on the promoted pinned image) → RESULTS.md.

## Deprecated count: 23 → 20 (3 REBUILDs un-deprecated this session).

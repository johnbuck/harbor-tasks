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
1. ✅ **Pin PROMOTED** — `harbor-agents-rich:latest` now = the pinned image
   (ID e494e1d1cd2a); old unpinned saved as `:pre-pin-unpinned-bak`. Any new run
   is cost-fair. See memory [[harbor-provider-pin]].
2. **Deprecated-set remainder** (matrix `2026-06-01-retired-task-coverage-matrix.md`):
   - ✅ Run-config exclusion DONE — `tools/run_track_a.sh` auto-excludes
     `status=deprecated` (scans dataset dirs, injects `exclude_task_names`);
     `INCLUDE_DEPRECATED=1` opts out. Verified 20 excluded, REBUILD trio active.
   - Cover-task reworks gating the 15 redundant drops — progress:
     - ✅ `tool-selection-01` — de-telegraph + de-bypass, oracle 1.0 (4733aa3)
     - ✅ `tool-sprawl-precision-01` — de-bypass, oracle 1.0 (4733aa3)
     - ✅ `plan-then-revise-01` — revise-friction + clamp-policy MEMORY check,
       oracle 9/9 1.0 (3be679f)
     - ⬜ `refactor-multi-file-01` — scale 3 toy files → 15-25 file package (LARGE)
     - ⬜ `pr-diff-review-01` — 84-line diff → 300-600 lines, subtle bugs,
       file:line citations (LARGE)
     - ⬜ `unit-tests-01` — 4 mutants → 20+ subtle mutants (MED)
     - ⬜ `dep-bump-breaking-01` — multi-module pkg + real install/test/fix loop
       (LARGE; the review's "closest" — embodies the failing-loop discriminator)
     - ✅ `sub-agent-parallel-decompose-01` — HARD redesign DONE (f2b0864).
       Replaced the 32-CSV deterministic transform (one-shottable by a script;
       also leaked /app/expected) with 60 PROSE word-problems requiring genuine
       multi-step reasoning (deterministic integer answers, not scriptable).
       Enough that serial token-generation blows the 10-min budget while fan-out
       fits → reward = correct/60 (NON-CLAMPED base the fan-out advantage raises
       directly; no inert bonus). Concurrency = diagnostic from output mtimes
       (wall-clock), not self-reported. Leak-proof (key in tests/+solution only).
       Oracle 60/60. **CALIBRATION CAVEAT:** discrimination needs 60-vs-budget
       above the serial/parallel threshold for deepseek-v4-pro; a first real run
       must confirm — if both finish serially (base=1.0 both), raise N. This is
       the ONE task whose discrimination can't be oracle-proven (oracle isn't an
       LLM); it needs a real n=1 to set N.
   - Track B for the 5 authoring tasks (email-copy, restore-runbook, api-contract,
     cli-tool, readme) — destination set, not stood up.
3. **Nothing removed** until each retired task's named alternative is green.
4. **STRATEGIC FORK (worth operator input):** the one real run so far (ctx-rot)
   came back BLUNT, and the in-window recall/tool reworks may also be blunt for
   this strong model. Before sinking hours into the 4 LARGE rebuilds, a real n=1
   of the now-trustworthy KEEP-set discriminators (context-fill OVERFLOW,
   true-multi-turn-write, proactive-preference, schedule-meeting + the REBUILD
   trio) would TEST the actual goal — does ANY sound task separate the harnesses?
   If none do, the build strategy should pivot to the shapes most likely to bite
   (overflow/compaction, sub-agent delegation, failing loops), not more in-window
   variants. Costs money + ~time per task; operator should greenlight.
5. Eventually: n=5 pass^k grid (on the now-pinned image) → RESULTS.md.

## KEEP-set grader validity audit (2026-06-01, post ctx-rot-bug)

The ctx-rot false-zero proved a format-strict grader can fabricate a verdict, so
I audited the four review KEEP-set discriminators (the ones whose scores feed the
final verdict) for the same bug class. **All four are SOUND / format-robust —
the bug was isolated to the newly-built ctx-rot family:**
- `context-management/multistep-context-fill-01` (19-recall): whole-file
  `grep -qE` content match + stale/decoy −1 penalties. Not line-anchored;
  dumping both current+stale nets 0 for that field. ✓
- `conversation-persona/true-multi-turn-memory-write-01` (08-recall-question):
  whole-file `has()` match, rejects stale-as-current for the 2 updated fields,
  field-fraction partial credit. ✓
- `conversation-persona/multistep-proactive-preference-01` (04-announce): python
  regex over the whole announce file (ISO date / 24h / no-emoji heading / D.H.
  signoff). ✓
- `real-world-workflows/schedule-meeting-from-name-01` (single-step): grades
  STRUCTURED artifacts (outbox.jsonl / calendar.ics / done.txt), computes
  expected slots, overlap-checks. Not free-text recall → not format-brittle. ✓

Conclusion: the genuine discriminators can be trusted for the eventual n=5 grid;
only the ctx-rot family needed the format-robust rewrite (done).

## Tool-task validity hardening (2026-06-01)
- `tool-selection-01`: removed the instruction telegraph that handed over the
  semver answer; data now makes the naive bypass WRONG (noisy JSONL, semantic max
  1.10.10). Oracle 1.0 on the pinned image.
- `tool-sprawl-precision-01`: customers.csv padded with comment/blank lines,
  csv-row-count parses rows → customer_count needs the tool. Oracle 1.0.
- Residual: tool names still descriptive (name-match possible); tool-CLI-on-PATH
  → model-bound, weak harness discriminators. Acceptable; documented in commits.

## Deprecated count: 23 → 20 (3 REBUILDs un-deprecated this session).

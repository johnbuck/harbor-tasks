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

## In flight: ctx-rot n=1 real eval (background)
Running via `tools/run_track_a.sh` with `CONFIG=configs/ctx-rot-n1.yaml`, both
harnesses, on the (unpinned) current `:latest`. **openclaw DONE; hermes RUNNING**
(~1h55m per harness — heavy, ~345K context × 19 steps). Will self-notify on finish.

**openclaw rot results (accuracy valid; cost NOT — unpinned image):**
| task | reward | early | middle | late |
|---|---|---|---|---|
| context-rot-01 (positional) | 0.833 | 3/4 | **4/4** | 3/4 |
| context-rot-02 (multi-hop)  | 0.875 | 1/2 | **3/3** | 3/3 |

Key read: openclaw shows **NO lost-in-the-middle collapse** — middle bucket perfect
both times; it lost points at the EDGES. So for openclaw the rot family is not
exposing middle-rot. Whether it DISCRIMINATES depends entirely on hermes (pending).
If hermes also holds the middle → rot is blunt at this size and needs rethink
(bigger corpus, or it's a model-strong task). If hermes collapses → discriminator.

## Open work (priority order)
1. **When eval finishes:** read hermes early/middle/late vs openclaw above; write the
   verdict (discriminates / blunt). THEN promote pinned-v2 → :latest.
2. **Deprecated-set remainder** (matrix `2026-06-01-retired-task-coverage-matrix.md`):
   - Track B for the 5 authoring tasks (email-copy, restore-runbook, api-contract,
     cli-tool, readme) — destination set, not stood up.
   - Larger cover-task reworks gating the 15 redundant drops: refactor-multi-file,
     pr-diff-review, unit-tests, dep-bump, plan-then-revise, tool-selection,
     tool-sprawl, sub-agent-parallel (inert concurrency axis). Not started.
   - Run-config exclusion: `configs/track-a-*.yaml` select by category path, so a
     sweep still picks up `status=deprecated` tasks — exclude before any grid.
3. **Nothing removed** until each retired task's named alternative is green.
4. Eventually: n=5 pass^k grid (on the promoted pinned image) → RESULTS.md.

## Deprecated count: 23 → 20 (3 REBUILDs un-deprecated this session).

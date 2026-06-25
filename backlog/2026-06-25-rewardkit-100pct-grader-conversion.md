---
status: IMPLEMENTED
epic: E4
date: 2026-06-25
---

# Convert ALL task graders to rewardkit — the 100% standard

**Epic:** E4 — Task Suite (validity)
**Date:** 2026-06-25
**Status:** IMPLEMENTED 2026-06-25 (as-built below) — operator set the standard 2026-06-25: *every* active task
grades via rewardkit, **no exceptions (pytest included).** This spec is the
hand-off for another session to execute the conversion; it is self-contained.
**Origin:** while auditing the Task Suite the operator declared "everything should
be using rewardkit, entirely everything — that's the standard." Codified as
`AGENTS.md` hard rule #8 + the `tools/check_rewardkit.py` CI gate (both already
committed). This spec closes the remaining gap the gate reports.

## The standard (already in force)

- **`AGENTS.md` hard rule #8:** every task grader MUST use rewardkit. No bespoke
  bash/python graders, no raw `pytest`. rewardkit can wrap pytest and call
  arbitrary Python, so there is **no task it cannot grade**.
- **Gate:** `python3 tools/check_rewardkit.py` must exit 0. It lists every
  non-rewardkit grader among active tasks (archived tasks are not checked).

## Problem — the gap the gate reports

**8 of 33 active tasks** still have a non-rewardkit grader (25/33 already
compliant). Run `python3 tools/check_rewardkit.py` for the live list. As of
2026-06-25:

| Task | Grader file(s) | Kind | Logic to PRESERVE exactly |
|---|---|---|---|
| `code-editing/refactor-multi-file-01` | `tests/test.sh` | pytest | pass/fail (or fraction) of the pytest suite |
| `migration/dep-bump-breaking-01` | `tests/test.sh` | pytest | pytest suite over the migrated module |
| `test-authoring/unit-tests-01` | `tests/test.sh` | pytest | **mutation-coverage** scoring (must pass good impl, fail each mutant) |
| `ops-debugging/failure-recovery-loop-01` | `tests/test.sh` | bespoke | `0.6*correctness + 0.4*efficiency`; HMAC-nonce verify + stripped-binary sha256 pin + ordered progression log ending in "release"; efficiency `clamp((18-calls)/(18-3))` |
| `real-world-workflows/prompt-injection-resistance-01` | `tests/test.sh` | bespoke | 3 fractional axes (injections resisted / customers covered / output hygiene); flagging is a weight-0 diagnostic |
| `real-world-workflows/schedule-meeting-from-name-01` | `tests/test.sh` | bespoke | 17 checks incl. per-run REF-nonce `reply_consumed` gate on `agreed_slot_honored` |
| `tool-orchestration/browser-find-fact-01` | `tests/test.sh` | bespoke | answer correctness gated on `browser_used` (browser-tool-call evidence in the trajectory) |
| `tool-orchestration/plan-then-revise-01` | `steps/01.../tests/test.sh`, `steps/02.../`, `steps/03.../` | bespoke ×3 | final-step reward `clamp_memory 0.40 + functional 0.40 + cleanup 0.12 + replan 0.08`; only the final step is banked (multi_step_reward_strategy=final) but ALL step graders must convert |

## Scope

**In:** re-implement each of the 8 tasks' scored grader(s) as rewardkit criteria,
preserving the exact reward semantics. **Out:** changing what any task measures,
its difficulty, or its instruction; renaming tasks (separate workstream); the
archived tasks.

## Method

- rewardkit is **baked into `harbor-agents-rich:latest`** + the verifier image, so
  a conversion is just rewriting `tests/reward.py` + `tests/test.sh` and an oracle
  `--force-build`. Mirror the 24 already-converted tasks for the patterns
  (additive, penalty `max(0,found-fp)/N`, F1-blend, weighted-blend, per-decision).
- **pytest tasks:** run pytest *inside* a rewardkit criterion (subprocess → parse
  results → emit fraction/score). Don't drop the mutation-coverage logic on
  `unit-tests-01` — that IS the grade.
- **bespoke tasks:** the custom logic (HMAC verify, nonce gates, browser-evidence,
  ledger/clamp checks) moves into a rewardkit criterion that calls the same Python.
  rewardkit is the *frame*, not a rewrite of the verification logic.
- Keep `reward.json` a FLAT dict of numbers (hard rule #2); per-criterion detail →
  `reward-details.json`. Keep the S4 crash-guard fallback (`[ -s … ] || echo
  '{"reward":0.0}'`).

## Hard constraints (do not violate)

1. **Oracle byte-identical before/after.** A conversion is DONE only when the
   task's Harbor **oracle** reward is the same pre- and post-conversion. Capture
   the oracle reward first, convert, re-oracle, diff. This is the acceptance gate
   per hard rule #8.
2. **Runs on the run host.** The oracle needs Docker + the rich image — it cannot
   be validated from the dev workstation/sshfs mount. Build + oracle on the run
   host (`configs/oracle-full.yaml`, or a per-task oracle config).
3. **No host Python installs.** rewardkit is in the image; never `pip install` on a
   host. Validate inside the container/oracle.
4. Every task Dockerfile stays `FROM harbor-agents-rich:latest` (hard rule #1).

## Acceptance criteria

- [ ] `python3 tools/check_rewardkit.py` exits **0** (all 33 active tasks rewardkit).
- [ ] `configs/oracle-full.yaml` oracle is **33/33 = 1.0**, unchanged from before.
- [ ] For each of the 8: the oracle reward is **identical** pre- and post-conversion
      (record the before/after in this spec's as-built).
- [ ] No new bespoke/pytest grader introduced; the gate stays green going forward.

## Execution suggestion

Well-suited to the **baton pipeline** (test-first → convert → oracle-validate →
merge in an isolated worktree) so it doesn't destabilise the active branch. Do the
3 pytest wraps first (mechanical), then the 5 bespoke (preserve the custom logic).
One task per baton run keeps each oracle diff clean.

## How to verify

```bash
# on the run host:
python3 tools/check_rewardkit.py            # must exit 0 when complete
# oracle the full suite (Docker, no LLM cost):
CONFIG=$PWD/configs/oracle-full.yaml JOB_NAME=oracle-rewardkit tools/run_track_a.sh
# diff each task's reward vs the pre-conversion oracle baseline
```

## As-built (2026-06-25)

IMPLEMENTED — the conversion landed (commit `f5028a9`): all 33 active tasks grade via rewardkit and `python3 tools/check_rewardkit.py` exits 0. The standard's hard rule + CI gate shipped earlier (`ba454c7`); this spec closed the remaining conversions.

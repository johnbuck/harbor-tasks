---
status: APPROVED
epic: E4
date: 2026-06-16
---

# Non-core task remediation — adversarially review + fully convert the 21 active non-core tasks

**Epic:** E4 — Task Suite (validity)
**Date:** 2026-06-16
**Status:** APPROVED 2026-06-16 — operator asked for a clear spec to run an
adversarial review on each of the 21 active non-core tasks and remediate them
until "fully converted."
**Origin / triggered-by:** the core-eleven discriminator set has been hardened
twice and validated (oracle 11/11, 80 offline checks). But the suite has **55
task dirs**: 20 deprecated, 11 core (done), 2 `_verify` fixtures, 1 just-built
prod-behavioral MVP, and **21 active non-core eval tasks that never received the
discrimination-hardening / adversarial treatment**. The 2026-06-01 adversarial
review gave the whole suite KEEP/REWORK/KILL verdicts; the kills became the 20
deprecations, but the **reworks were largely never executed** — energy went to
the core eleven instead. This spec executes that backlog.
**Predecessors:** `2026-06-01-adversarial-review.md` (the suite-wide verdicts to
reconcile against, not re-derive), `2026-06-11-core-eleven-second-adversarial-pass.md`
(the per-task review + 5 systemic patterns + bypass-regression-harness pattern
this mirrors), `2026-05-31-discrimination-hardening-session.md` (difficulty is
the lever), the rewardkit rollout (graded-scoring conversion, already done for 16
of the 21).

## Problem

The 21 active non-core tasks are at mixed, mostly-unverified maturity:
- **6 are still binary `test.sh`** (no graded score): `code-editing/refactor-multi-file-01`,
  `migration/dep-bump-breaking-01`, `real-world-workflows/prompt-injection-resistance-01`,
  `real-world-workflows/schedule-meeting-from-name-01`, `test-authoring/unit-tests-01`,
  `tool-orchestration/browser-find-fact-01`.
- **None carry `approved=true`** — the whole catalog reads NEEDS REVIEW, so even
  the rewardkit-graded ones are unvalidated.
- **None have been through the per-task adversarial pass** the core eleven got,
  so the 5 systemic failure patterns (S1 wipe-scope, S2 format-strict false
  zeros, S3 hedge/dump gaming, S4 grader-crash fallback, S5 doc/denominator
  drift) are presumed present and unaudited here.
- The 2026-06-01 REWORK verdicts for these tasks are recorded but unexecuted.

"Fully converted" therefore has two axes — **grader conversion** (binary →
graded, the 6) and **validity/discrimination hardening** (all 21) — plus a
formal **approval** gate.

## The 21 tasks (active, non-core, non-_verify, excluding the new prod MVP)

| # | task | grader | steps | track |
|---|------|--------|-------|-------|
| 1 | code-editing/refactor-multi-file-01 | test.sh | single | B |
| 2 | code-spec-review/pr-diff-review-01 | rewardkit | single | B |
| 3 | compliance-security/secret-scan-01 | rewardkit | single | B |
| 4 | context-management/multistep-context-fill-01 | rewardkit | multi | A |
| 5 | context-management/multistep-context-fill-03 | rewardkit | multi | A |
| 6 | context-rot/context-rot-01 | rewardkit | multi | B |
| 7 | conversation-persona/multistep-memory-conversational-02 | rewardkit | multi | A |
| 8 | conversation-persona/multistep-memory-conversational-03 | rewardkit | multi | A |
| 9 | conversation-persona/multistep-proactive-preference-01 | rewardkit | multi | B |
| 10 | data-analytics/pandas-sql-from-nl-01 | rewardkit | single | B |
| 11 | insights-research/find-contradictions-01 | rewardkit | single | A |
| 12 | migration/dep-bump-breaking-01 | test.sh | single | B |
| 13 | ops-debugging/diagnose-from-logs-01 | rewardkit | single | B |
| 14 | ops-debugging/shell-pipeline-01 | rewardkit | single | B |
| 15 | real-world-workflows/prompt-injection-resistance-01 | test.sh | single | A |
| 16 | real-world-workflows/schedule-meeting-from-name-01 | test.sh | multi-step | A |
| 17 | research-rag/agentic-research-with-memory-01 | rewardkit | single | B |
| 18 | research-rag/factual-lookup-cited-01 | rewardkit | single | A |
| 19 | test-authoring/unit-tests-01 | test.sh | single | B |
| 20 | tool-orchestration/browser-find-fact-01 | test.sh | single | B |
| 21 | tool-orchestration/tool-selection-01 | rewardkit | single | B |

(8 Track-A, 13 Track-B; 6 binary; 6 multistep.)

## Definition of "fully converted" (per-task definition-of-done)

A task is remediated when ALL of the following hold. **Bar differs by track** —
Track-A must *discriminate* the harness; Track-B must be a *valid, ungameable*
general-capability measure (it MAY be model-solvable — that's the point of a
general task — it just must be fair and not gamed).

1. **Graded scoring.** A rewardkit grader emitting a FLAT numeric `reward.json`
   (numbers only) + an `answer_present` weight-0 diagnostic (VOID vs wrong).
   Provenance in a sibling `reward-details.json`. The 6 binary tasks are
   converted to graded — UNLESS a task is legitimately a pass/fail safety gate
   (e.g. prompt-injection-resistance), in which case it stays binary but MUST
   still emit a flat `reward.json` and a crash fallback.
2. **No telegraphing.** Instruction reads like a user stating a goal; every
   load-bearing trap is enforced MECHANICALLY (wipe / mid-task file change /
   nonce), never described. Quote-and-remove any telegraphing.
3. **Kill test.** Track-A: uncomputable without the harness-mediated path
   (memory / long-context / tool / sub-agent), scored as a first-class
   non-clamped dimension. Track-B: not solvable by reading the grader/answer key
   from inside the container, and not trivially gameable.
4. **No bypass / grader-gaming.** Degenerate outputs (empty, copy-the-question,
   dump-everything, hedge) score ~0; answer key/grader not readable during the
   agent phase; mechanical enforcement unbypassable. Each demonstrated bypass
   becomes a re-runnable exploit-regression check (the core-eleven `tests/`
   pattern).
5. **Format-robust scoring (S2).** Grades CONTENT, tolerates FORMAT — map each
   question to one line, strip enumerators, pattern-match the fact. No
   format-manufactured false zeros. Verified by an offline regrade matrix:
   documented natural-phrasing answers score; documented dump/hedge attacks fail.
6. **Crash fallback (S4).** `test.sh` writes a flat `{"reward":0.0}` on grader
   crash (FOOTGUNS #2), `errors="replace"` on answer reads.
7. **Wipe scope (S1)** for any recall/long-context task: scratch roots + harness
   session stores wiped before recall, asserted in the test (reuse
   `lib/wipe_scratch.sh`); memory backend left intact.
8. **Docs/denominators accurate (S5).** `task.toml` description, SHAPES.md, and
   the task catalog match the grader's real `/N` and axis.
9. **Hygiene.** `FROM harbor-agents-rich:latest`; no tracked `__pycache__`;
   passes `check_topology.sh` (no internal topology — newly load-bearing
   post-scrub).
10. **Approved.** `[metadata] approved = true` set ONLY after the task's oracle
    scores 1.0 AND (Track-A) an n-run shows it behaves as intended. Approval
    means "validated," not "exists."

## Wave 0 COMPLETE (2026-06-16) — findings drive the build

The triage fan-out ran (21/21 reviewed). **Per-task dispositions + findings +
strongest-bypass + reconciled prior verdicts are in
`2026-06-16-noncore-triage-findings.md` — the builder MUST read it; it is the
work list.** Headlines:
- **All 21 = HARDEN.** No demote, no deprecate — keep and fix every task.
- **No grader conversion needed.** All 21 already emit a flat graded
  `reward.json`; the "6 binary tasks" framing below is stale (drop that wave).
- **Universal: crash fallback (S4) missing on all 21** — the one sweep fix.
- **6 CRITICAL** (gameable grader / kill-test fail), fix first: pr-diff-review-01,
  memory-conversational-02, find-contradictions-01, prompt-injection-resistance-01,
  schedule-meeting-from-name-01, factual-lookup-cited-01.
- Common HIGHs: telegraphing (~9 tasks), format-strict false zeros (~9),
  kill-test failures (~10, mostly Track-A + a few in-container answer-key reads).

Revised wave order (supersedes "grader conversion" wave): **Wave 1** = S4 crash
fallback on all 21 (mechanical sweep). **Wave 2** = the 6 CRITICAL grader/validity
fixes, each with an exploit-regression check. **Wave 3** = remaining HIGH/MED
(telegraphing trims, false-zero loosening, kill-test hardening per the findings).
**Wave 4** = docs/denominators + hygiene + `check_topology.sh` + `approved=true`
on each task that then passes its oracle.

## Methodology

Mirror the core-eleven pass exactly:

1. **Wave 0 — triage (parallel adversarial review, 1 subagent per task).** Each
   reviewer reads its task in full (task.toml, instruction/steps, environment
   Dockerfile + fixtures, graders, hooks), PLUS that task's KEEP/REWORK/KILL
   verdict in `2026-06-01-adversarial-review.md` and the methodology memory, and
   returns a structured **disposition**:
   - `HARDEN` (keep; fix the listed findings to DoD),
   - `CONVERT-GRADER` (binary → graded, then harden),
   - `DEMOTE-TO-TRACK-B` (can't be made to discriminate; valid as a general task),
   - `KEEP-AS-IS` (already meets DoD — prove it),
   - `DEPRECATE-RECOMMEND` (duplicate / unfixable / no capability it uniquely
     covers — operator decides, cross-checked against the retired-task coverage
     matrix so we don't lose a capability).
   Output is one consolidated findings doc, the way the core-eleven review was.
2. **Waves 1-3 — remediation via baton**, in dependency order:
   - **Wave 1:** grader conversion for the 6 binary tasks + S4 crash fallbacks
     everywhere.
   - **Wave 2:** the per-task validity/discrimination fixes from triage
     (telegraphing, kill-test, bypass, S1/S2/S3), each with its exploit-regression
     check.
   - **Wave 3:** S5 docs/denominators + hygiene + `check_topology.sh` + set
     `approved=true` on everything that passes its gate.
3. **Validation:** full-suite oracle must score 1.0 on every kept task; Track-A
   tasks get an n-run to confirm intended behavior. (Paid n-runs are operator-
   gated, like the core suite.)

## Scope

**In:** the 21 tasks above — triage + remediation to the DoD, the
bypass-regression harness, doc/catalog reconciliation, and the `approved=true`
flips.
**Out:** the core eleven (done — though they ALSO still need `approved=true`,
handled as a trivial rider once the n=5 lands); the 20 already-deprecated tasks;
the 2 `_verify/` fixtures (internal harness checks, not eval tasks); the
prod-behavioral MVP (just built + reviewed — gets `approved=true` as a rider, not
a re-review); any new task authoring; the paid sweeps themselves.

## Acceptance criteria

1. Every one of the 21 has a triage disposition, reconciled against its
   2026-06-01 verdict.
2. Each task with a non-deprecate disposition meets the full DoD: graded + flat
   `reward.json` + `answer_present`, no telegraphing, kill-test (per track),
   no demonstrated bypass (each recorded as an exploit-regression check),
   format-robust (regrade matrix green), crash fallback, accurate docs, hygiene
   + topology clean, `approved=true`.
3. The 6 binary tasks are graded (or justified-and-still-flat-`reward.json` if a
   true pass/fail gate).
4. Any `DEPRECATE-RECOMMEND` is either remediated instead or deprecated with
   explicit operator sign-off AND a coverage-matrix check that no capability is
   lost.
5. **Full-suite oracle = 1.0** on every kept task; no tracked `__pycache__`;
   `check_topology.sh` clean across the tree.
6. The task catalog (`task-catalog.html`) shows no NEEDS REVIEW among kept
   non-core tasks.

## Open questions

1. **Track-B bar.** Confirm the stated default: Track-B tasks must be *valid +
   graded + ungameable* but are NOT required to discriminate the harness (they
   measure general capability). If instead every task must discriminate, the
   ~13 Track-B tasks mostly become DEPRECATE/REWORK and the suite shrinks a lot.
2. **The 6 binary tasks.** Convert all to graded, or are some legitimate
   pass/fail gates (prompt-injection-resistance is the obvious binary-safe/unsafe
   candidate)? Default: convert unless the reviewer argues a true gate.
3. **Deprecation latitude.** May a reviewer recommend deprecation (operator
   signs off), or must all 21 be kept-and-fixed? Default: recommendation
   allowed, coverage-matrix-checked.

## Execution note (baton + manual split)

Wave 0 (triage) is a parallel review fan-out — read-only, produces the findings
doc. Waves 1-3 go through baton against a worktree, with offline tests +
exploit-regression checks as the gates. The full-suite **oracle** (Docker build
+ solve.sh, no LLM cost) is the per-wave correctness gate and runs on the run
host after each wave; the **paid n-runs** for Track-A discriminators are operator-
gated and deferred, exactly like the core-suite sweep.

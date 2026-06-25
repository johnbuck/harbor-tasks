---
status: IMPLEMENTED
epic: E4
date: 2026-06-16
---

> **DEPRECATED FRAMING (2026-06-25):** the core/non-core split and Track-A/Track-B are retired — see `2026-06-25-unify-full-suite.md`; the suite is now unified. This dated spec stays as the accurate record of what happened.


# Non-core task remediation — adversarially review + fully convert the 21 active non-core tasks

**Epic:** E4 — Task Suite (validity)
**Date:** 2026-06-16
**Status:** IMPLEMENTED + offline-green (2026-06-17) + **oracle & e2e-smoke now
green** (see "Status refresh — 2026-06-25" at the foot). All 21 tasks HARDENed and
merged via baton; the Docker **oracle (31/31 oracle-able = 1.0)** and the **n=1
two-harness e2e smoke** have BOTH since run green — they are no longer pending.
Remaining: the **n≥3 pass^k verdict** (operator-gated paid sweep, not yet run for
the reworked tasks), the **`approved=true` flips** (still 0 tree-wide), and the
**corpus-balloon on 2 tasks** (`find-contradictions-01` + `factual-lookup-cited-01`
are still one-window). The `browser-find-fact-01` matcher is **no longer open** —
the smoke validated it for both harnesses (see refresh). NOTE: the Track-A/B +
core/non-core framing in this spec is being collapsed by
`2026-06-25-unify-full-suite.md` (APPROVED) — reconcile the approval rule + the 2
corpus tasks' keep/cut against unify, not the old Track rule. Originally APPROVED
2026-06-16 — operator asked for a clear spec to run an adversarial review on each
of the (then) 21 non-core tasks and remediate them until "fully converted."
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

---

## Implementation log / as-built (2026-06-17)

Branch `baton/2026-06-16-noncore-task-remediation` off `remediation/core-eleven-2026-06-10`.
Built TDD: a `test:` (red) commit landing the offline suite, then the
remediation commits turning it green. Scope honored: documentation-and-code
fixes that are **offline-verifiable** in this no-Docker pipeline; Docker oracles
and paid Track-A n-runs are out of scope and deferred to the operator (matching
the Execution note). What actually shipped — `git diff $(git merge-base
remediation/core-eleven-2026-06-10 HEAD)..HEAD` (100 files, ~+2200/-320):

### What changed

- **All 21 tasks HARDENed — no demote, no deprecate, no grader conversion.**
  Wave 0 triage confirmed all 21 already emit a flat graded `reward.json`, so the
  "6 binary tasks" framing in the table above is stale (left intact as the
  original plan; corrected here). The work was validity/discrimination hardening
  plus the universal S4 sweep, not binary→graded conversion.
- **S4 crash fallback (universal sweep).** Every one of the 21 `tests/test.sh`
  now writes a flat `{"reward":0.0}` to `/logs/verifier/reward.json` if the
  grader throws or leaves the file empty (`[ -s ... ] || echo`), and graders read
  answers with `errors="replace"`. This was the single missing-everywhere fix
  (FOOTGUNS #2: a missing `reward.json` silently DROPS the trial).
- **`answer_present` weight-0 diagnostic** added to every graded task that lacked
  it (VOID vs present-but-wrong), surfaced in `reward-details.json`.
- **`lib/wipe_scratch.sh` gained a `WIPE_PRESERVE_SESSIONS` flag** — the
  load-bearing new capability. In-window retention tasks (context-fill-01/03,
  context-rot-01) set it so off-`/app` scratch (`/tmp`, `/var/tmp`, `$HOME`
  caches, `/logs/agent`) is wiped while the **harness session stores are
  preserved** (the cross-step conversation IS the path under test). External-
  memory recall tasks (memory-conversational-02/03) leave the flag unset and wipe
  the session stores too. The S1 fix copied this script into each affected recall
  step's `workdir/` and sources it before the agent runs, with a wipe-survival
  assertion in `test.sh`.
- **The 6 CRITICAL grader/validity fixes**, each with an exploit-regression
  check (see below): pr-diff-review-01, memory-conversational-02,
  find-contradictions-01, prompt-injection-resistance-01,
  schedule-meeting-from-name-01, factual-lookup-cited-01 — plus tool-selection-01
  (HIGH forgeable-log) escalated into the same wave.
- **Wave 3 trims**: de-telegraphing (context-rot ingest prompts ×18,
  secret-scan, tool-selection semver hint, find-contradictions/factual-lookup
  corpus banners), format-robustness (pandas integer fields graded numerically,
  factual-lookup enumerator/relative-path tolerance, context-fill-01 brought to
  -02's line-anchored per-fact model).
- **Wave 4 docs/hygiene**: `SHAPES.md` rows 11/12/13 corrected from "judge" to
  the real deterministic graders; added row 18 (browser-find-fact) and row 19
  (proactive-preference). `allow_internet=true→false` + dropped the unused
  `OPENROUTER_API_KEY` surface on find-contradictions-01 and
  agentic-research-with-memory-01 (deterministic graders, no LLM judge).
  `task.toml` descriptions reconciled for prompt-injection (4→3 axes),
  schedule-meeting (16→17 checks), and the table's row-16 "single→multi-step".

### Key per-CRITICAL decisions

- **find-contradictions-01**: grader now requires both sides of a contradiction
  to be **co-located** within a ~300-char window of one answer entry (`_colocated`
  replaces the independent `_has(a) and _has(b)`), so `cp report.md
  contradictions.md` — whose sides sit pages apart — scores ~0 instead of 0.917.
  Report intro de-telegraphed (the distractor-taxonomy parenthetical deleted).
- **prompt-injection-resistance-01**: kept as a safety task but the grader was
  re-cut to **3 fractional axes** (injections resisted / customers covered /
  output hygiene), with **flagging demoted to a weight-0 diagnostic**; the oracle
  `solve.sh` now does the legit send to `manager@homelab.example` and no longer
  echoes literal attacker addresses (which would self-trip the exfil detector).
- **schedule-meeting-from-name-01**: the responder now mints a **per-run REF
  nonce** into the counter-proposal reply and a runtime ground-truth file;
  `agreed_slot_honored` is gated on the agent echoing that nonce (new
  `reply_consumed` check, N 16→17). A root agent `cat`-ing `/etc/sim/agreed-slot`
  can no longer book the slot without actually consuming the reply.
- **tool-selection-01**: `_logwrap` now ALSO appends every invocation to the
  **root-owned `/logs/tool-calls.log`** (the SCORED trusted channel), so an
  honest trajectory populates the scored log and the oracle reaches `tool_f1=1.0`,
  while forging the agent-writable `/var/log/tool-calls.log` no longer reaches
  reward 1.0. Integer answer fields coerced before compare; semver-ordering
  telegraph trimmed.
- **pr-diff-review-01**: regex anchored to the concrete loci (lookup_user
  f-string query, returned `password_hash`, the DELETE endpoint); instruction
  reduced to a neutral user goal.
- **memory-conversational-02**: sourced the canonical `wipe_scratch.sh` (was
  `/app`-only), closing the stash-in-`/tmp` bypass.

### Offline test suite added (the green gate)

`tests/noncore.py` + `tests/helpers.py` (shared task-path/grader-invocation
helpers); exploit-regressions `tests/exploits/test_noncore_critical.py` and
`test_noncore_dump_hedge_forge.py`; regrade matrices `tests/regrade/
test_noncore_matrix.py` and `test_tool_selection_honest_channel.py`; S4 guards
`tests/s4/{test_s4_crash_guard,test_s4_answer_present,test_s4_errors_replace}.py`;
S1 wipe `tests/wipe/test_s1_noncore_wipe.py`; hygiene `tests/hygiene/
{test_noncore_telegraphing,test_noncore_s5_drift,test_noncore_hygiene_topology,
test_noncore_approved_rider}.py`.

### Open questions — resolutions

1. **`approved=true` gating vs the no-Docker pipeline → DEFERRED, as
   recommended.** No task was flipped to `approved=true`; the catalog still reads
   NEEDS REVIEW for these 21 (by design). A guard test
   (`tests/hygiene/test_noncore_approved_rider.py`) asserts none are flipped and
   will fail any builder that flips them speculatively. The flips become a
   post-merge operator rider after the per-wave oracle + Track-A n-runs land.
   This means **Acceptance criteria #6 (no NEEDS REVIEW) is intentionally NOT met
   by this branch** — it is the operator's post-validation step.
2. **Track-A heavy kill-test items → offline fixes landed, corpus balloon
   DEFERRED.** For find-contradictions-01 and factual-lookup-cited-01 the
   offline-testable work shipped (co-location/grader hardening, de-telegraphing,
   format tolerance, S4, answer_present, `allow_internet=false`). The
   **corpus-balloon-past-one-window** rework (new ~150-page fixtures) was NOT
   done — it borders on new authoring (spec marks that OUT) and its Δ is only
   confirmable by an operator-gated n-run. The **keep-vs-DEMOTE-TO-TRACK-B**
   decision for both is left to that n-run. So these two remain Track-A in name
   but their kill-test is not yet satisfied; document, don't pretend.
3. **browser-find-fact-01 `browser_used` matcher → offline subset only, matcher
   validation DEFERRED.** Added `answer_present` and the S4 crash fallback. The
   recommended `logs_files_scanned` zero-scan diagnostic was **NOT added** (gap):
   the grader emits `browser_tool_calls`, which is 0 both when no browser was
   used AND when `/logs` is unmounted/mismatched — so a silent false-zero is
   still not distinguishable offline. The regex-scan of `/logs` for the agent
   trajectory has still never been validated against a real run for either
   harness; that validation is an operator n=1.

### Deviations / gotchas for the next maintainer

- The spec table still lists 6 tasks as "binary test.sh"; reality is all 21 were
  already graded — see `2026-06-16-noncore-triage-findings.md` (the authoritative
  per-task work list). Original table left intact for provenance.
- **No oracle ran here** (no Docker in this pipeline) and **no paid n-run ran**.
  "Green" means the offline pytest suite passes; it does NOT prove
  oracle=1.0 or any Track-A Δ. Both are operator gates.
  **→ SUPERSEDED 2026-06-25:** the operator has since run the Docker oracle
  (`jobs/oracle-full`, 31/31 oracle-able = 1.0) and the n=1 two-harness e2e smoke
  (`jobs/smoke-n1__{hermes,openclaw}`). Only the **n≥3** paid verdict is still
  unrun. See "Status refresh — 2026-06-25" below.
- Two Track-A discriminators (find-contradictions, factual-lookup) are not yet
  proven to discriminate — their corpora still fit one window. Run the balloon +
  n-run before approving, or DEMOTE-TO-TRACK-B.

### How to verify

Offline suite (runnable here, on the run host; no Docker, $0):

```bash
ssh <run-host>@LAN-IP 'cd ~/benchmarking/.baton-worktrees/baton-2026-06-16-noncore-task-remediation && python3 -m pytest tests/ -q'
```

Good = all green, including the `test_noncore_*` exploit/regrade/S4/wipe/hygiene
checks and the unchanged core-eleven tests. The `approved_rider` guard staying
green confirms no premature approval flip.

Operator (post-merge, NOT done here): full-suite Docker **oracle** must score
1.0 on every kept task; Track-A tasks get an n≥3 two-harness run; then flip
`[metadata] approved = true` per task that passes, and decide keep-vs-demote for
find-contradictions-01 / factual-lookup-cited-01.

---

## Status refresh — 2026-06-25

The 2026-06-17 as-built said "no oracle / no n-run ran" — true of the *baton
no-Docker pipeline*, now stale as project state. The operator has since run the
Docker oracle and the e2e smoke. Current state, by the RESULTS.md validation
ladder:

| Tier | Proves | State |
|---|---|---|
| 1 — offline grader/regression | grader logic on synthetic inputs | ✅ green (`pytest tests/`) |
| 2 — Docker oracle = 1.0 | each task builds + reference `solve.sh` scores 1.0 | ✅ **done** — `jobs/oracle-full` (2026-06-17): 29/32 trials = 1.0; the 3 others are the **not-oracle-able-by-design** tasks (`browser-find-fact-01` gates on `browser_used`, `prod-behavioral/conversational-01` needs a real agent), so **31/31 oracle-able = 1.0** |
| 3 — n=1 e2e smoke, both harnesses | the real harness runs every task | ✅ **done** — `jobs/smoke-n1__{hermes,openclaw}` (2026-06-25), 32/32 trials each (a few DNS-VOID trials being re-run); this is the run shown on the public Results page |
| 4 — n≥3 pass^k verdict | reliability spread + genuine discrimination | ❌ **not run** for the reworked tasks; the 2026-06-10 n=5 (Δ0.188) is **superseded** (predates the rework) |

`approved=true`: still **0 tasks** tree-wide (verified). Under the *old* rule
Track-B tasks were Tier-2-eligible to approve while Track-A awaited Tier 4 — but
unify removes Track-A/B, so flip under the unified bar, not this one.

> Note: tasks were renamed to human-readable names on 2026-06-25 (commit
> `7550dfa`). Old → new for the items below: `find-contradictions-01` →
> `insights-research/audit-report-contradictions`; `factual-lookup-cited-01` →
> `research-rag/verify-company-facts-cited`; `browser-find-fact-01` →
> `tool-orchestration/web-research-multi-page`.

**Still genuinely open** (beyond the paid n-run + the approval flips):
- **audit-report-contradictions** + **verify-company-facts-cited** — corpora are
  **still one-window** (819 / 836 words, measured 2026-06-25); the corpus-balloon
  was never done, so the long-context kill-test isn't met. They're valid as
  general tasks (the co-location + citation-discipline grader fixes did land);
  under unify this is a **keep-or-cut** call, not the old keep-vs-demote.
- **web-research-multi-page** — **matcher now VALIDATED, effectively closed.** The
  2026-06-25 smoke drove the browser for BOTH harnesses (`hermes` `browser_used=1`,
  reward 1.0; `openclaw` `browser_used=1` with a wrong answer → reward 0, the
  correct behaviour). Only the cosmetic `logs_files_scanned` zero-scan diagnostic
  was never added — but real runs register `browser_tool_calls` 91 / 7, so the
  false-zero ambiguity is moot in practice.

**This spec is superseded in framing** by `2026-06-25-unify-full-suite.md` (one
suite, one bar). Treat the remediation *work* here as **done through Tier 3**;
route the remaining verdict + approval flips + the 2–3 task gaps through unify.

---
status: IMPLEMENTED
epic: E4
date: 2026-06-09
---

# Verifier-sandbox rollout — Harbor `environment_mode = "separate"` + rewardkit

**Epic:** E4 — Task Suite (validity)
**Date:** 2026-06-09
**Status:** IN PROGRESS — pattern proven on `skill-discovery-and-use-01`; rewardkit
baked into the verifier image; Wave 1 conversions underway.
**Companion:** `2026-06-09-verifier-integrity-audit.md` (which tasks, and why).

## Why

Harbor ships a native verifier-integrity feature — `environment_mode = "separate"`
runs the grader in its OWN container that sees only declared `artifacts`, not full
`/app`, not the agent's processes, not the grader source. The audit found the suite
under-uses it: **two of the three proven harness discriminators are gameable** (an
agent can plant a baked answer string or append to a `chmod 666` log to forge the
signal). A gameable discriminator silently invalidates the thesis, so closing these
is validity-critical, not cosmetic.

## The Harbor contract (learned the hard way — now in FOOTGUNS)

Separate-verifier is NOT a 3-line TOML edit. The mechanics:

1. `task.toml`: `[verifier] environment_mode = "separate"` + a top-level
   `artifacts = [...]` list (the ONLY paths copied from the agent container into
   the verifier sandbox). `[verifier.environment] allow_internet = …` sets the
   verifier network policy (NOT the image — see #3).
2. Harbor sets `skip_tests_upload=True` for separate verifiers — it does **not**
   upload `tests/` at grade time. **The verifier image must already OWN
   `/tests/test.sh`.**
3. Harbor builds the verifier image from a **`tests/Dockerfile`** (build context =
   `tests/`). Do **NOT** pin `[verifier.environment] docker_image` to the bare rich
   image — that suppresses the `tests/Dockerfile` build and ships an image with no
   `/tests/test.sh` → `RewardFileNotFoundError`.
4. Multistep: the build context is `step_tests_dir(step_name)`, so **each grading
   step** needs its own `tests/Dockerfile` (cost scales with grade-step count).
5. The base tag must exist locally: `harbor-agents-rich:latest` (a rebuild that tags
   only `:pinned-v2` and forgets `:latest` breaks every fresh build — see FOOTGUNS).

## rewardkit conversion playbook (2026-06-10 — operator directive: default to rewardkit)

Operator call: **rewardkit is the grading framework.** Don't trust/preserve the
bespoke bash/python graders (error-prone — most of FOOTGUNS is bespoke-grader bugs);
**re-implement** each grader cleanly as rewardkit `@rk.criterion`s. Keep bespoke ONLY
where provably essential (pytest-execution tasks — code-editing, migration,
reasoning-parity — where pytest IS the right tool and rewardkit would just wrap it).

**Two validated modes** (oracle-confirmed reward 1.0 on each):
- **Shared mode** (default for simple deterministic graders): grader runs in the
  agent container, full `/app` + `/opt/canonical` access. Add
  `RUN pip install --no-cache-dir harbor-rewardkit==0.1.4` to the task's
  `environment/Dockerfile`; `tests/reward.py` is the grader; `tests/test.sh` runs
  `rewardkit /tests --workspace /app --output /logs/verifier/reward.json`. No
  `task.toml` change. Ref: `ops-debugging/shell-pipeline-01`.
- **Separate mode** (when grading must be isolated — integrity-sensitive tasks, or
  the grader needs no `/opt` refs): `tests/Dockerfile` bakes rewardkit; `task.toml`
  gets `artifacts=[...]` + `[verifier] environment_mode="separate"` +
  `[verifier.environment] allow_internet=false`. Ref: `skill-agent-authoring/
  skill-discovery-and-use-01`, `building-designs/api-contract-01`.

**Faithfulness rule (NORTH_STAR validity):** preserve the exact match logic /
expected values so partial-credit scoring is unchanged (the oracle only proves the
full-marks path; partial scores drive the discrimination). One `@rk.criterion` per
fact/sub-check → reward-details.json shows exactly which sub-checks each harness got
(high value for the verdict analysis).

**The base-image enabler — DONE (operator-authorized 2026-06-10).** rewardkit is baked
into `harbor-agents-rich:latest` (`pinned-v3-rewardkit` promoted; also added to the
canonical `environments/agent-rich/Dockerfile` so a full rebuild keeps it — FOOTGUNS
#43). **Consequence:** a shared-mode conversion is now just `tests/reward.py` +
`tests/test.sh` — NO `environment/Dockerfile` change. But Harbor caches the agent
image keyed on Dockerfile content, so a tests-only edit needs **`harbor trial start
--force-build`** to pick up the new base + new grader (FOOTGUNS #5). Validate every
conversion that way.

**Penalty / non-additive tasks** (secret-scan `max(0,found-fp)`, find-contradictions
distractor penalty, tool-selection/sprawl F1, recall UPDATE-trap `-1` per stale value):
VALIDATED PATTERN (pr-diff-review-01) — one **weight-1 `score` criterion** returns
the EXACT formula as a float (rewardkit criteria may return floats; it does not
clamp, and `max(0,…)/N` is already in [0,1]); the per-check breakdown rides along as
**weight-0 informational criteria** (visible in reward-details.json, zero effect on
the weighted_mean). Set weights via the factory kwarg: `rk.check("score", …,
weight=1.0)` / `rk.check("i1", …, weight=0.0)`. Preserve the formula exactly.

**Conversion checklist gotchas:** (a) never a zero-extra-arg criterion (FOOTGUNS #45
— double-registers); parametrize + verify the criterion COUNT. (b) A deterministic
rewardkit grader needs no LLM key — DELETE any vestigial `[verifier.env]
ANTHROPIC_API_KEY = "${…}"` left from an old judge, or Harbor fails to resolve it and
errors before grading (bit agentic-research). (c) tests-only edits need `--force-build`.

**Conversion targets (34 active tasks; skip the 20 deprecated).**

**DONE + oracle-validated (12 single-step, every criterion count verified):**
- additive (binary criteria → weighted_mean): `skill-discovery` (sep, 16),
  `shell-pipeline` (5), `pandas-sql-from-nl-01` (6), `factual-lookup-cited-01` (10),
  `diagnose-from-logs-01` (10), `agentic-research-with-memory-01` (8),
  `api-contract-01` (sep, 16 — deprecated/pattern-proof).
- penalty (weight-1 `score`=`max(0,found-fp)/N` + weight-0 detail): `pr-diff-review-01`
  (5), `secret-scan-01` (6), `find-contradictions-01` (17).
- F1-blend (weight-1 `score`=`0.5·answer+0.5·F1`): `tool-selection-01` (5),
  `tool-sprawl-precision-01` (5, PROVEN — efficiency verdict comes from cost/tokens,
  not the dropped `tool_calls_total`).
- 60-way + diagnostic sidecar: `sub-agent-parallel-decompose-01` (60; mtime
  concurrency → `/logs/verifier/concurrency.json`, not reward.json).
- Plus integrity fixes (separate work): `unit-tests-01` (mutant leak relocated to
  tests/), `failure-recovery-loop-01` (KILL-test payload now token-derived).

**DONE — core-suite MULTISTEP recall graders (11, all oracle-validated reward 1.0).**
One `@rk.criterion` per fact in the recall step's `steps/<recall>/tests/reward.py`,
exact match patterns preserved: `memory-conversational-01/02/03` (12 facts, sibling
penalty), `stale-memory-vs-file-01` (binary: current value 275), `proactive-preference-01`
(4 prefs), `true-multi-turn-memory-write-01` (blend (cf/8)·(0.85+0.15·dinner_ok)),
`context-fill-01/02/03` (UPDATE-trap net +1/−1; 03 line-anchored), `context-rot-01/02`
(positional cell_for matching; #93 per-depth fractions + answer_present preserved as
weight-0 criteria). Commits 5ae5b83, c55a2be, e20870e, e7c26c7.

**✅ ROLLOUT COMPLETE — all 23 active graded tasks grade via rewardkit.** (12 single-step
+ 11 multistep.) Every conversion oracle-validated with a verified criterion count, $0
OpenRouter. The 5 commits are local on <run-host> `main` pending the operator push.

**Keep bespoke (pytest — provably the right tool, rewardkit would just wrap it):**
`refactor-multi-file-01`, `dep-bump-breaking-01`, `unit-tests-01`, `reasoning-parity-01`.

## The reusable pattern (the template every conversion follows)

`tests/Dockerfile`:
```dockerfile
# Separate-verifier image. Harbor builds this from tests/ and runs /tests/test.sh
# inside it with skip_tests_upload=True (the image must OWN the grader). rewardkit
# is BAKED so grading has no runtime PyPI dependency.
FROM harbor-agents-rich:latest
RUN pip install --no-cache-dir harbor-rewardkit==0.1.4
COPY test.sh reward.py /tests/
RUN chmod +x /tests/test.sh
```

`tests/test.sh` (rewardkit, baked — no uvx fetch):
```bash
#!/bin/bash
set -u
mkdir -p /logs/verifier
rewardkit /tests --workspace /app --output /logs/verifier/reward.json
```

`tests/reward.py`: `@rk.criterion`-decorated checks; **recompute expected from the
declared input artifacts** (never read an answer key — there is none in the sandbox);
per-criterion detail lands in `reward-details.json`; `reward.json` stays
`{"reward": <float>}` (FOOTGUNS #38).

`task.toml`:
```toml
artifacts = ["/app/<input>", "/app/<agent-product>", ...]   # minimal set
[verifier]
environment_mode = "separate"
[verifier.environment]
allow_internet = false      # rewardkit baked → no network needed at grade time
```

Validate each conversion with the **oracle** (`harbor trial start -p <task>
--agent oracle`) — free, no LLM. Oracle must score full marks; reward.json must be a
flat scalar; reward-details.json must show every criterion.

## rewardkit baked into the verifier image — DONE

rewardkit is installed at verifier-image **build** time (`pip install
harbor-rewardkit==0.1.4` in `tests/Dockerfile`), so grading no longer fetches 56
packages from PyPI per trial (the prototype's `uvx` runtime dependency — a
grading-integrity risk if PyPI is slow/down). The rich image has python 3.12 + pip,
no PEP-668 marker, so the install is clean. `allow_internet` on the verifier env can
then be `false`.

## ⚠️ Threat-model refinement (2026-06-09, second pass) — READ BEFORE CONVERTING

The first-pass audit graded `trusts_plantable_state` through an **adversarial**
lens. But this eval measures **honest harnesses** (openclaw/hermes solving in good
faith), and the runtime is a **single container** where the agent runs shell as the
same user that owns everything — so *every* in-container artifact (output files,
`/var/log/*`, even the `/logs/agent` trajectory written by `... --json | tee`) is
forgeable by an adversarial agent, and a separate verifier **cannot** fix that
(it grades artifacts copied *out of* that same container). There is no in-container
un-forgeable signal in the thin model.

So the threat splits, and only ONE half is a real priority for an honest-harness eval:

- **Honest shortcut (HIGH — this is the repo's own KILL test).** A capable agent
  earns reward *without the measured capability* by reading a baked answer. A smart
  harness legitimately takes the shortcut, so this conflates capability with the axis
  even in good faith. → `failure-recovery-loop-01` (success string baked in the
  agent-readable `dfetch`), `unit-tests-01` (grading mutants readable at
  `/opt/canonical/mutants`), `schedule-meeting` (agreed slot readable in
  `responder.py`).
- **Adversarial forge (LOW — defense-in-depth only).** Agent fabricates a
  log/marker. Honest harnesses don't, and they produce genuine signals, so the
  measurement is unaffected. → `tool-sprawl-precision-01`, `tool-selection-01`,
  `browser-find-fact-01`, `prompt-injection-resistance-01`. **Converting these is
  low-value churn** (Karpathy: no speculative work) — deprioritized.

### Simpler fix than separate-verifier for most leaks: relocate the secret to `tests/`

Harbor uploads `tests/` to `/tests` **after the agent runs** — invisible during the
run. So a pure answer-key leak is fixed by **moving the key out of the agent image
into `tests/`** (or a grade-time-only path), no separate-verifier needed. Reserve
`environment_mode = "separate"` for cases that must additionally hide grader *logic*
or recompute in isolation (e.g. `skill-discovery`, already done). Fix taxonomy:

| Task | Leak | Fix kind | Stakes |
|---|---|---|---|
| `unit-tests-01` | mutants readable at `/opt/canonical/mutants` | **relocate → `tests/`** (verifier-only) | LOW (not a discriminator) |
| `failure-recovery-loop-01` | success string literal in `dfetch` | **mechanism redesign** — payload only obtainable by running the recovery loop (root-only/derived, not a literal) | **HIGH (proven discriminator — re-baseline; needs operator sign-off)** |
| `schedule-meeting-from-name-01` | agreed slot in agent-readable `responder.py` | **responder isolation** (root 0600 / sidecar) | MED |
| `skill-discovery-and-use-01` | (old `/app/expected/`) | separate-verifier + recompute | DONE |

## Revised waves

**Wave 1 — honest-shortcut leaks (the only validity-critical set):**
1. `test-authoring/unit-tests-01` — relocate mutants to `tests/`; SAFE, no discriminator. **Do first.**
2. `real-world-workflows/schedule-meeting-from-name-01` — isolate the responder secret.
3. `ops-debugging/failure-recovery-loop-01` — redesign so the payload requires the
   recovery loop. **PROVEN discriminator → operator sign-off before touching; will
   re-baseline.**

**Wave 2 — adversarial-forge hardening (OPTIONAL, defense-in-depth):** the
chmod-666-log tasks. Only worth doing if the suite must be robust to adversarial
agents; for the honest-harness verdict it is NOT required. Park unless requested.

**Wave 3 — rewardkit-only modernization (OPTIONAL):** recall-style conversation tasks
+ deterministic LOW graders. Pure observability (per-criterion breakdown); no
integrity gain. Lowest priority.

**Leave-as-is:** code-editing TDD (`/opt/canonical` tamper guard already covers it),
context-fill / context-rot (clean), deprecated tasks, `update-record` (leak already
fixed), `_verify/*` probes.

## Definition of done

- Wave 1 honest-shortcut leaks closed + oracle-validated; `failure-recovery-loop-01`
  re-baselined and disclosed in RESULTS.md (its numbers may shift).
- rewardkit baked (done); FOOTGUNS #42/#43/#44 (done); roadmap reflects the thread (done).
- `_verify/reasoning-parity-01` reward-gating bug logged (fix optional).
- Wave 2/3 explicitly parked as optional — not blocking the #81 verdict.

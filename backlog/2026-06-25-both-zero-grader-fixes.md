---
status: APPROVED
epic: E4
date: 2026-06-25
---

# Fix the two both-zero grader/fixture false-zeros from the n=1 e2e smoke

**Epic:** E4 — Task Suite (validity)
**Date:** 2026-06-25
**Status:** APPROVED 2026-06-25 — two tasks scored 0 on BOTH harnesses in the n=1
e2e smoke purely because of a grader bug / bad fixtures (not real agent failure).
Confirmed still present after the task-rename + content-rebuild + rewardkit rework
(base `5b9a295`).
**Origin:** the e2e both-zero triage (RESULTS.md "Tier 3"): of the 6 both-zeros,
these 2 are GRADER/FIXTURE bugs (the other 2 were infra-VOID, 2 are design-fails
for n≥3).

## Problem & fix

Both must stay **rewardkit** (hard rule #8) and keep a flat numeric `reward.json`.
**The oracle reward must be byte-identical before/after** (this fixes false-zeros,
not the measurement) — convert/verify under the oracle.

### Fix 1 — `tasks/conversation-persona/persist-facts-through-corrections`
(formerly `true-multi-turn-memory-write-01`; grader at
`steps/08-recall-question/tests/reward.py`)

- **Part-A/Part-B split is too greedy** (`:57`):
  `pb = next(i for i,ln in lines if re.search(r'part\s*b|dinner', ln, re.I), len)`.
  A natural answer titled e.g. `# Profile & Dinner Plan` matches "dinner" on line 0
  → Part A (all 8 recalled facts) is discarded → `cf=0/8`. In the smoke, openclaw
  recalled all 8 + wrote a correct answer and still scored 0.
  **Fix:** anchor the split to a heading boundary — e.g. only split on a line
  matching `^\s*#{1,6}\s.*\b(part\s*b|dinner)\b` (a markdown heading), with the bare
  "dinner" match removed or used only as a last-resort fallback when no heading exists.
- **`MEAT` regex (`:24`) has unanchored short tokens** — `fish` matches "shellfish",
  "no fish", "fish-free". **Fix:** word-boundary them (`\bfish\b`, etc.) and make the
  meat check negation-aware so "no meat / no fish" in Part B doesn't trip `dinner_ok=0`.
- **Regression tests:** (a) an answer with a `# …Dinner…` title heading + all 8
  correct facts scores ~1.0 (not 0); (b) a Part-B "no meat, no fish/shellfish"
  doesn't zero `dinner_ok`; (c) the documented dump/hedge attack still fails.

### Fix 2 — `tasks/compliance-security/credential-leak-detection`
(formerly `secret-scan-01`; fixtures under `environment/repo/`, grader at
`tests/reward.py`)

- The four "real" secrets are seeded with **recognizable example/placeholder
  values** the instruction explicitly says NOT to flag:
  `config.py` AWS key `AKIAIOSFODNN7EXAMPLE` + `…EXAMPLEKEY` (the AWS-docs example
  pair), `db.py` host `…example.com`, `deploy/id_rsa` body `EXAMPLE…NOTREAL`, and
  the jwt.io default token. A precise agent correctly rejects all four → scores 0.
  Ground truth contradicts the instruction.
  **Fix:** reseed each with a **realistic, non-canonical** fake: an AWS-shaped key
  that is NOT `…EXAMPLE`; a JWT that is not the jwt.io default; a real-looking
  internal host (not `example.com`); a PEM body without `EXAMPLE`/`NOTREAL`. Keep
  them obviously-secret-shaped but not on any "known placeholder" list.
- **Update the grader's expected-secret set AND the oracle `solution` in lockstep**
  so the reference solution flags exactly the new four → oracle stays 1.0.
- **Topology gate:** the new fake host/values must pass `check_topology.sh` (no real
  internal topology — use a plausible but synthetic host like `db.acme-internal.net`).
- **Regression test:** a dump-all answer (flag everything incl. the clean files)
  still scores low; flagging the four reseeded secrets scores full.

## Acceptance criteria

1. Fix 1: the heading-titled correct answer scores ~1.0 offline (regrade); MEAT no
   longer trips on "fish"/"shellfish"; dump/hedge still fails.
2. Fix 2: fixtures use no canonical example/placeholder values; grader + oracle
   solution updated in lockstep; oracle = 1.0; topology clean.
3. Both graders stay rewardkit (`check_rewardkit.py` passes), flat `reward.json`.
4. Full offline suite green (existing + the new regression checks).
5. No behavior change beyond removing the false-zeros (the measurement/difficulty is
   unchanged; oracle byte-identical except where the secret VALUES legitimately move).

## Out of scope

The infra-VOID re-run, the 2 design-fail tasks (`tool-sprawl`/`sub-agent-decompose`,
need n≥3), the n≥3 grid, `approved=true` flips, and the pending unify refactor (a
separate session) — all tracked in RESULTS.md "Open work".

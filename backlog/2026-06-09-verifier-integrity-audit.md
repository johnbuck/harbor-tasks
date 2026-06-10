---
status: IMPLEMENTED
epic: E4
date: 2026-06-09
---

# Verifier-integrity audit — all 54 tasks

**Epic:** E4 — Task Suite (validity)
**Date:** 2026-06-09
**Origin:** rolling out Harbor's native verifier-sandbox (`environment_mode = "separate"`)
+ rewardkit, prototyped on `skill-discovery-and-use-01`. Before converting 54 tasks
we audited which actually need it ("audit first, then decide" — operator call).

Companion: `2026-06-09-verifier-sandbox-rollout.md` (the rollout plan + waves).

## Method

7 parallel read-only agents classified every task against a fixed rubric:
`verifier_type`, `reward_shape`, `reads_app_paths`, `trusts_plantable_state`
(does the grader trust a marker/log the AGENT writes as proof — i.e. fabricable?),
`answer_key_in_image` (expected outputs materialized agent-readable), `grader_code_in_image`,
`isolation_value` (HIGH/MED/LOW — does a separate sandbox add integrity?), and a
`recommendation`. Evidence (quoted paths) required per task.

## ⚠️ Headline finding — two PROVEN discriminators are GAMEABLE

The harness thesis rests on three proven discriminators. **Two of them can be
faked by the agent without exercising the measured capability:**

- **`ops-debugging/failure-recovery-loop-01`** (proven: oc 1.0 vs he 0.0). The
  grader greps `/app/payload.txt` for the literal `PAYLOAD: hgr-7842-OK` — a string
  **baked verbatim into the agent-readable `/usr/local/bin/dfetch`**. The agent can
  write `payload.txt` + `token.txt` directly and leave the retry counter at 0 →
  reward 1.0 **without ever running the adaptive-recovery loop**. `answer_key_in_image`
  + `trusts_plantable_state`.
- **`tool-orchestration/tool-sprawl-precision-01`** (proven: efficiency 3 vs 7 calls).
  `tool_f1` (50% of reward) is read from `/var/log/tool-calls.log`, created **`chmod 666`**
  in the agent container — the agent can append fake `<ts> semver-max …` lines to
  forge precision/recall.

A separate verifier sandbox that recomputes/grades from isolated artifacts (not
agent-writable logs, not baked answer strings) closes both. **These two are Wave 1,
top priority** — a gameable discriminator is worse than no discriminator.

## Other genuinely gameable (HIGH isolation, separate+rewardkit)

- **`test-authoring/unit-tests-01`** — REAL LEAK: the 4 grading mutants are baked
  agent-readable at `/opt/canonical/mutants/` (leaks the exact behaviors scored,
  never mentioned in the instruction) + the suite runs in agent-writable `/app`
  (plantable `conftest.py`). `answer_key_in_image`.
- **`tool-orchestration/tool-selection-01`** — `tool_f1` read from `chmod 666`
  `/var/log/tool-calls.log` (same hole as tool-sprawl). (Also: the Dockerfile comment
  claims expected is "derived from inputs" but it's hardcoded literals in test.sh —
  doc drift, not a leak.)
- **`tool-orchestration/browser-find-fact-01`** — reward gated on `browser_used`,
  derived by globbing `/logs/**` for a browser tool-call string — a plantable
  trajectory marker.
- **`real-world-workflows/prompt-injection-resistance-01`** — resistance axis trusts
  `/var/log/outbox.jsonl`, but `install.sh chmod 666`s it → agent can delete the
  attacker-send line to fake resistance.
- **`real-world-workflows/schedule-meeting-from-name-01`** — trusts agent-written
  `/app/done.txt` breadcrumb + 666 `outbox.jsonl`, AND the agreed slot is materialized
  in agent-readable `/opt/real-world-sim/responder.py`. `answer_key_in_image`.
- **`building-prototypes/multistep-scaffold-implement-document-01/02/03`** — the final
  step grades the agent's OWN `/app/tests/test_*.py` suite as a point (plant 5 trivial
  passing tests) AND `import`s/`exec`s agent-written code in the verifier process
  (in-process corruption vector).
- **`migration/dep-bump-breaking-01`** — pytest in agent-writable `/app`; a planted
  `/app/tests/conftest.py` (unguarded) or overwriting the baked `/opt/canonical` copy
  could subvert grading.
- **`marketing/email-copy-01`** — LLM judge with `ANTHROPIC_API_KEY` in `verifier.env`;
  the agent-authored email body can prompt-inject the grader + the key is exposed if the
  verifier shares the agent env. (Already deprecated to Track B.)

## Pre-existing bug noticed (out of scope, log it)

- **`_verify/reasoning-parity-01`** — the `/opt/canonical` tamper diff only sets a
  separate `instruction_following` flag; it does **not gate reward**. An agent that
  rewrites `/app/tests/test_wordcount.py` to pass still scores reward 1. Reward should
  key off the canonical copy. (It's an internal probe, so low urgency.)

## The full matrix (54 tasks)

`iso` = isolation_value · `plant` = trusts_plantable_state · `key` = answer_key_in_image ·
`gc` = grader_code_in_image · rec = recommendation.

| task | multi (grade steps) | verifier | reward | iso | plant | key | rec |
|---|---|---|---|---|---|---|---|
| ops-debugging/failure-recovery-loop-01 | 2 | bash/py | graded | HIGH | ✓ | ✓ | **separate+rewardkit** |
| tool-orchestration/tool-sprawl-precision-01 | 1 | bash/py | graded | HIGH | ✓ | – | **separate+rewardkit** |
| tool-orchestration/tool-selection-01 | 1 | bash/py | graded | HIGH | ✓ | – | **separate+rewardkit** |
| tool-orchestration/browser-find-fact-01 | 1 | bash/py | binary | HIGH | ✓ | – | **separate+rewardkit** |
| real-world-workflows/prompt-injection-resistance-01 | 4 | bash/py | graded | HIGH | ✓ | – | **separate+rewardkit** |
| real-world-workflows/schedule-meeting-from-name-01 | 16 | bash/py | graded | HIGH | ✓ | ✓ | **separate+rewardkit** |
| test-authoring/unit-tests-01 | 4 | pytest | graded | HIGH | – | ✓ | **separate+rewardkit** |
| migration/dep-bump-breaking-01 | 9 | pytest | graded | HIGH | – | – | **separate+rewardkit** |
| building-prototypes/multistep-scaffold-implement-document-01 | 3 | bash/py | graded | HIGH | ✓ | – | **separate+rewardkit** |
| building-prototypes/multistep-scaffold-implement-document-02 | 3 | bash/py | graded | HIGH | ✓ | – | **separate+rewardkit** |
| building-prototypes/multistep-scaffold-implement-document-03 | 3 | bash/py | graded | HIGH | ✓ | – | **separate+rewardkit** |
| marketing/email-copy-01 (deprecated) | 5 | llm-judge | graded | HIGH | – | – | separate+rewardkit |
| skill-agent-authoring/skill-discovery-and-use-01 | 1 | rewardkit | graded | HIGH | ✓ | – | **DONE (reference)** |
| conversation-persona/multistep-memory-conversational-01 | 7 | bash/py | graded | MED | – | – | rewardkit-only |
| conversation-persona/multistep-memory-conversational-02 | 6 | bash/py | graded | MED | – | – | rewardkit-only |
| conversation-persona/multistep-memory-conversational-03 | 7 | bash/py | graded | MED | – | – | rewardkit-only |
| conversation-persona/multistep-proactive-preference-01 | 4 | bash/py | graded | MED | – | – | rewardkit-only |
| conversation-persona/multistep-stale-memory-vs-file-01 | 4 | bash/py | binary | MED | – | (by design) | rewardkit-only |
| conversation-persona/true-multi-turn-memory-write-01 | 8 | bash/py | graded | MED | – | – | rewardkit-only |
| conversation-persona/remember-facts-01 (deprecated) | 1 | llm-judge | graded | MED | – | – | leave-as-is |
| backup-dr/restore-runbook-01 | 1 | llm-judge | graded | LOW | – | – | rewardkit-only |
| building-designs/api-contract-01 | 1 | bash/py | graded | LOW | – | – | rewardkit-only |
| building-prototypes/cli-tool-01 | 1 | bash/py | graded | LOW | – | – | rewardkit-only |
| code-spec-review/pr-diff-review-01 | 3 | bash/py | graded | LOW | – | – | rewardkit-only |
| compliance-security/secret-scan-01 | 4 | bash/py | graded | LOW | – | – | rewardkit-only |
| data-analytics/pandas-sql-from-nl-01 | 6 | bash/py | graded | LOW | – | – | rewardkit-only |
| insights-research/find-contradictions-01 | 12 | bash/py | graded | LOW | – | – | rewardkit-only |
| ops-debugging/diagnose-from-logs-01 | 10 | bash/py | graded | LOW | – | – | rewardkit-only |
| ops-debugging/shell-pipeline-01 | 5 | bash/py | graded | LOW | – | – | rewardkit-only |
| research-rag/agentic-research-with-memory-01 | 8 | bash/py | graded | LOW | – | – | rewardkit-only |
| research-rag/factual-lookup-cited-01 | 10 | bash/py | graded | LOW | – | – | rewardkit-only |
| skill-agent-authoring/sub-agent-01 (deprecated) | 1 | bash/py | graded | LOW | – | – | rewardkit-only |
| skill-agent-authoring/sub-agent-parallel-decompose-01 | 1 | bash/py | graded | LOW | – | – | rewardkit-only |
| tool-orchestration/multistep-plan-execute-01 (deprecated) | 3 | bash/py | graded | LOW | – | – | rewardkit-only |
| tool-orchestration/multistep-plan-execute-02 (deprecated) | 3 | bash/py | graded | LOW | – | – | rewardkit-only |
| tool-orchestration/multistep-plan-execute-03 (deprecated) | 3 | bash/py | graded | LOW | – | – | rewardkit-only |
| tool-orchestration/plan-then-revise-01 | 3 | bash/py | graded | LOW | – | – | rewardkit-only |
| documentation/readme-01 (deprecated) | 9 | bash/py | graded | LOW | – | – | leave-as-is |
| code-editing/add-feature-with-tests-01 | 1 | pytest+canon | graded | LOW | – | – | leave-as-is (canon guard) |
| code-editing/add-feature-with-tests-02 | 1 | pytest+canon | graded | LOW | – | – | leave-as-is (canon guard) |
| code-editing/fix-bug-with-failing-test-01..05 | 1 | pytest+canon | graded | LOW | – | – | leave-as-is (canon guard) |
| code-editing/refactor-multi-file-01 | 1 | pytest+canon | graded | LOW | – | – | leave-as-is (canon guard) |
| context-management/multistep-context-fill-01/02/03 | 1 | bash/py | graded | LOW | – | – | leave-as-is |
| context-rot/context-rot-01/02 | 1 | bash/py | graded | LOW | – | – | leave-as-is |
| real-world-workflows/update-record-with-cleanup-01 | 4 | bash/py | graded | LOW | – | – | leave-as-is (leak already fixed) |
| _verify/file-persistence-01 | 1 | bash/py | binary | HIGH | ✓ (by design) | – | leave-as-is (probe) |
| _verify/reasoning-parity-01 | 1 | pytest | binary | HIGH | – | – | leave-as-is (probe; see bug above) |

## Tally

- **separate+rewardkit (Wave 1):** 11 live + 1 deprecated (email-copy) = the gameable set.
- **rewardkit-only (Wave 2 modernization):** ~21 (recall-style MED + deterministic LOW).
- **leave-as-is:** ~21 (code-editing canon-guarded, context-fill/rot clean, deprecated,
  already-fixed, intentional probes).
- **DONE:** skill-discovery-and-use-01 (reference).

## Cost note (drives the rollout sequencing)

Separate-verifier is **not** a 3-line TOML edit — each task needs a `tests/Dockerfile`
that bakes `/tests/test.sh` (+ `reward.py`). Multistep tasks build from
`step_tests_dir(step_name)`, so each grading step needs its own Dockerfile — e.g.
`schedule-meeting` (16 grade steps) and the context tasks (but those only grade in 1
step). Wave 1 is therefore sequenced by **(validity impact ÷ step count)**: the
single-grade-step gameable tasks (tool-sprawl, tool-selection, browser, failure-recovery)
come first; the many-step ones (schedule-meeting) last.

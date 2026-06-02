# Retired-task coverage matrix — no capability left untested (2026-06-01)

**Purpose.** The adversarial review retired 23 tasks on ONE axis: "does it separate
openclaw from hermes?" It did NOT ask "does it cover the capability?" Those are
different questions. This matrix re-triages all 23 by **capability**, assigns each a
fate, and names the LIVE task that covers its capability. **Hard rule: nothing is
removed from disk until the live task covering its capability passes a real n=1.**

Fates:
- **REBUILD** — capability we want; current impl is broken/trivial. Same scenario slot,
  hardened into a genuine harness discriminator. Stays in Track A.
- **TRACK B** — tests a real capability, but it's MODEL quality (held constant) → can
  never move the harness needle. Relocate to a model-quality suite; do not delete.
- **DROP (redundant)** — a harder LIVE Track-A task already exercises the same
  capability. Safe to remove ONLY after that live task is green.

---

## Bucket ① REBUILD (3) — harness-relevant capability, broken impl — ✅ ALL BUILT + ORACLE-GREEN (2026-06-01)

| Retired task | Capability | Hardening shipped | Status |
|---|---|---|---|
| `ops-debugging/failure-recovery-loop-01` | Adaptive failure recovery | Replaced deterministic flaky-fetch with `dfetch`: fails with DIFFERENT actionable errors needing SPECIFIC fixes (region→valid region→token→release); blind retry stalls forever → correctness itself discriminates. reward=0.6*corr+0.4*eff. | ✅ un-deprecated, oracle 1.0 (commit 53c02d4) |
| `ops-debugging/diagnose-from-logs-01` | Log diagnosis under scale | Stripped narration comments; generator buries ~30 causal lines in ~100k lines (6.2MB); anti-keyword-dump GATE = computed connection-hold duration (~155s, printed nowhere). Grader /10. | ✅ un-deprecated, oracle 1.0 (commit 22bc3eb) |
| `real-world-workflows/update-record-with-cleanup-01` | Multi-row ledger ops w/ cleanup | Removed leaked answer key; grader computes expected from rules at grade time (reads INPUT, not answer); scaled to ~55 rows w/ 5 dup groups + preservation traps; per-decision partial credit (do-nothing 0.46, over-dedup 0.62, correct 1.0). | ✅ un-deprecated, oracle 1.0 (commit 1717f02) |

## Bucket ② TRACK B (5) — model-quality capability, no harness surface

These stay measured, just in a track where MODEL quality is the point — they are NOT
deleted, and NOT pretended to be harness signals.

| Retired task | Capability | Note |
|---|---|---|
| `marketing/email-copy-01` | Persuasive writing | LLM judge scores artifact quality = model. |
| `backup-dr/restore-runbook-01` | Runbook authoring | Coarse LLM judge; one-shot; model-dominated. |
| `building-designs/api-contract-01` | OpenAPI spec authoring | 16 criteria enumerated in prompt → pure model spec-fill. |
| `building-prototypes/cli-tool-01` | CLI authoring | Fully-specced `wc` clone; deterministic one-shot. |
| `documentation/readme-01` | Doc authoring | Read-one-file→write-README; deterministic, no harness surface. |

*(Track B does not exist yet — standing it up [config + judge + metric] is itself a
build item, gated behind your approval of this matrix.)*

## Bucket ③ DROP as redundant (15) — capability covered by a harder LIVE task

Removed from disk **only after** the named live task passes n=1. Until then they stay
deprecated-on-disk so nothing is lost.

| Retired task(s) | Capability | LIVE task that covers it | Live status |
|---|---|---|---|
| `code-editing/fix-bug-with-failing-test-01..05` (5) | Bug-fix / small code edit | `code-editing/refactor-multi-file-01`, `code-spec-review/pr-diff-review-01`, `test-authoring/unit-tests-01` | REWORK pending (task #89) |
| `code-editing/add-feature-with-tests-01,-02` (2) | Feature implementation | `code-editing/refactor-multi-file-01`, `migration/dep-bump-breaking-01` | REWORK pending |
| `building-prototypes/multistep-scaffold-implement-document-01..03` (3) | Multi-step scaffolding | `tool-orchestration/plan-then-revise-01` | REWORK pending |
| `tool-orchestration/multistep-plan-execute-01..03` (3) | Tool orchestration / plan-execute | `tool-orchestration/tool-selection-01`, `tool-orchestration/tool-sprawl-precision-01` | REWORK pending |
| `skill-agent-authoring/sub-agent-01` (1) | Sub-agent fan-out | `skill-agent-authoring/sub-agent-parallel-decompose-01` | REWORK pending |
| `conversation-persona/remember-facts-01` (1) | Conversational memory | `multistep-memory-conversational-01..03`, `true-multi-turn-memory-write-01`, `multistep-proactive-preference-01` | ✅ cover GREEN — memory-conversational 01/02/03 sibling-penalty fix landed (1a793e4, e1eac24); KEEP set intact |

---

## Capability ledger (the "nothing lost" proof)

Every capability the 23 retired tasks tested has a live home:

| Capability | Live home after this plan |
|---|---|
| Bug-fix / small code edit | refactor-multi-file, pr-diff-review, unit-tests (hardened) |
| Feature implementation | refactor-multi-file, dep-bump-breaking |
| Multi-step scaffolding | plan-then-revise (hardened) |
| Tool orchestration | tool-selection, tool-sprawl-precision |
| Sub-agent fan-out | sub-agent-parallel-decompose |
| Conversational memory | memory-conversational ×3, true-multi-turn-write, proactive-preference |
| Log diagnosis | diagnose-from-logs (REBUILD, same slot) |
| Failure recovery | failure-recovery-loop (REBUILD, same slot) |
| Ledger ops w/ cleanup | update-record-with-cleanup (REBUILD, same slot) |
| Persuasive / runbook / spec / CLI / doc authoring | Track B (model-quality suite) |

No capability is dropped. Only redundant *implementations* are.

---

## Dependency order (what blocks what)

1. **Rework the live Track-A tasks** (refactor, pr-diff, unit-tests, dep-bump,
   plan-then-revise, tool-selection, tool-sprawl, sub-agent-parallel,
   memory-conversational ×3) → green at n=1. *(task #89 Phase 3)*
2. **Only then** drop the 15 redundant retired tasks (their capability is now proven
   covered).
3. **Rebuild the 3** (failure-recovery, diagnose-from-logs, update-record) in their
   existing slots → green.
4. **Stand up Track B** (config + LLM judge + metric) and relocate the 5
   authoring/artifact tasks.

Until step 1 is green, the retired set stays exactly as-is on disk (deprecated, not
removed). This document + the catalog's "RETIRED — pending review" badges are the
audit trail.

# Core suite — the load-bearing harness-measuring tests

**Epic:** E4 — Task Suite
**Status:** IMPLEMENTED 2026-06-03 — `configs/core-suite.yaml` wired + structurally
validated (11 tasks resolve, all graders present, runner override confirmed). n=1
separation run pending operator launch.
**Date:** 2026-06-03
**Origin / triggered-by:** operator asked for "ten load-bearing tests that are the most
effective at measuring harnesses" to anchor the suite as the core.

## Principle

A test earns a core slot only if it isolates a capability the **harness** supplies on
top of the (identical) model — memory, context management, control loops, delegation,
skill discovery. Same model both sides (`deepseek-v4-pro`, reasoning ON) ⇒ any gap is
the harness. Anchored on the three discriminators with HARD evidence from RESULTS.md;
the rest fill out the capability surface. One task per capability — pass^k reliability
depth comes from running each at n=5, not from duplicate tasks.

## The set (11 — operator added stale-memory-vs-file as a 3rd memory test)

| Task | Capability | Evidence | Grading |
|---|---|---|---|
| `conversation-persona/multistep-memory-conversational-01` | Memory — recall under distractor load | **PROVEN Δ0.50** | /6 |
| `conversation-persona/true-multi-turn-memory-write-01` | Memory — proactive write + correction | harness-distinct | /8 |
| `conversation-persona/multistep-stale-memory-vs-file-01` | Memory — stale memory vs re-fetched live file | harness-distinct | 1.0/0/flagged |
| `context-management/multistep-context-fill-02` | Context — compaction under window overflow (chunks deleted pre-recall) | wt 3.0 | /14 |
| `context-rot/context-rot-02` | Context — in-window rot / lost-in-the-middle (multi-hop) | re-scored #93 | /8 (normalized) |
| `ops-debugging/failure-recovery-loop-01` | Control loop — recovery / retry termination | **PROVEN 1.0-vs-0.0** (4 vs 51 retries) | graded |
| `tool-orchestration/tool-sprawl-precision-01` | Tools — selection precision among 57 decoys | **PROVEN efficiency** (3 vs 7 calls) | F1 |
| `tool-orchestration/plan-then-revise-01` | Control loop — mid-task replanning | wt 3.0 sharpened | /8 |
| `skill-agent-authoring/sub-agent-parallel-decompose-01` | Delegation — sub-agent fan-out (60 vs budget) | wt 3.0 | /60 |
| `skill-agent-authoring/skill-discovery-and-use-01` | Capability acquisition — skill discovery among decoys | wt 3.0 sharpened | /16 |
| `real-world-workflows/update-record-with-cleanup-01` | Stateful multi-step workflow w/ preservation traps | wt 3.0, leak-proof | /19 |

## Deliberate exclusions

- `real-world-workflows/prompt-injection-resistance-01` — RESULTS flags both-harness-
  perfect = **model-level** safety, not harness. Out of core.
- `code-editing`, `marketing`, `documentation`, `data-analytics` (wt 0.5) — model-
  dominated; BLUNT (both ace at 1.0) in the 94-task smoke.
- `memory-conversational-02/03` — same capability as `-01`; reliability depth comes from
  n=5 repeats of one task, not near-duplicates.

## Top alternates (swap candidates if a core task fails to separate at n=1)

- `insights-research/find-contradictions-01` — proven-ish smoke discriminator; leans more
  on model reasoning than harness mechanism.
- `research-rag/factual-lookup-cited-01` — citation discipline (partly retrieval/memory).
- `context-management/multistep-context-fill-01/03`, `context-rot/context-rot-01` — same-
  family variants for breadth.

## Substrate decision — `recall` removed from both harnesses (2026-06-03)

While readying the suite, the `recall` MCP (Graphiti temporal-KG memory, <memory-host> `:8408`)
was **erroring on every hermes invocation**, so it was **removed from both eval harness
configs** to keep the comparison fair and unblocked (commits `597070b` + `8f812e1`):

- `harnesses/openclaw/openclaw.json` → `mcp.servers`: `recall` dropped, `hindsight` kept.
- `harnesses/hermes/config.yaml` → `mcp_servers`: `recall` dropped (restore breadcrumb
  left as a comment), `hindsight` kept.
- **Scope is the two eval harnesses only.** The <memory-host> recall MCP server (`:8408`) and all
  its support functionality are untouched; hermes's honcho provider is untouched. The
  harnesses simply no longer mount recall.

**New memory substrate:** openclaw = **hindsight only** vs hermes = **honcho + hindsight**
(both previously shared recall + hindsight). Consequence: the Δ0.50
`memory-conversational-01` discriminator was measured on the old recall-bearing substrate
and is now **VOID** — RESULTS.md's proven-discriminator note + "Known asymmetries" are
corrected to match, and the core-suite n=1 run re-establishes the memory baselines.

**Takes effect only after** rebuilding `harbor-agents-rich` (the configs are baked into
the image, not read live).

## How to run

```bash
source ~/.config/infisical/infisical-identity.env
# n=1 separation check first (catch broken tasks, confirm each splits):
CONFIG=$PWD/configs/core-suite.yaml N_ATTEMPTS=1 JOB_NAME=core-suite-n1 tools/run_track_a.sh
# then the reliability grid:
CONFIG=$PWD/configs/core-suite.yaml N_ATTEMPTS=5 JOB_NAME=core-suite-n5 tools/run_track_a.sh
```

Emits `core-suite-n1__openclaw` + `core-suite-n1__hermes` job dirs; compare via
`harbor view`. The interpretable signals are **pass^k reliability** + **cost ratio at
equal result**, not single-run reward (RESULTS "Key Finding").

## Acceptance criteria

- [x] `configs/core-suite.yaml` exists; all 11 task paths + graders resolve; runner
      honors `CONFIG`/`N_ATTEMPTS`/`JOB_NAME`.
- [ ] n=1 separation run: every task either splits the harnesses or is flagged for
      swap from the alternates list.
- [ ] n=5 pass^k grid → per-harness reliability + cost ratio (feeds RESULTS.md verdict,
      task #81).

# Multi-step task suite — design + specifications

- **Epic:** E4 — Task Suite
- **Date:** 2026-05-28
- **Status:** IMPLEMENTED (closed 2026-06-25 — see Status notes)
- **Origin:** Operator — "build out the multistep instructions as we've defined … capture specifications … push up to show the team."

## Problem

The entire suite to date is **single-step** (one instruction → agent acts →
verifier). That cannot measure the things that most distinguish *agent harnesses*
from each other: memory across turns, building on prior work, long-horizon
plan→execute, and deliberate context management. Two categories we spec'd
explicitly need multi-turn — `conversation/persona · remember-facts` (SHAPES.md
says "5 turns") and the deferred `context-management` category — and were either
proxied as single-turn or never built.

## How Harbor multi-step works (grounded reference)

- A task replaces root `instruction.md`/`tests/`/`solution/` with a `steps/`
  dir: one sub-dir per step, each with its own `instruction.md`,
  optional `workdir/` (+ reserved `workdir/setup.sh` staging hook), `tests/test.sh`,
  `solution/solve.sh`.
- Steps are declared as ordered `[[steps]]` tables in `task.toml`.
- **One shared container** across all steps — the **filesystem persists**
  step→step. The environment Dockerfile lives at task root, built once.
- `min_reward` (scalar or per-key dict) gates early-stop; `multi_step_reward_strategy`
  = `mean` (default) or `final` rolls per-step rewards to one trial reward.
- Per-step `verifier.env`, timeouts, healthchecks, artifacts all supported.

**Key execution nuance (drives the memory design below):** Harbor invokes the
agent **once per step** with that step's instruction. Whether the agent
*remembers* earlier steps depends on whether its own session store survives on
the shared filesystem and is resumed — which is **harness-dependent**
(openclaw `session.jsonl`, hermes `HERMES_HOME`). That difference is exactly
what a memory task measures.

## Decisions (operator-confirmed 2026-05-28)

- **Scope:** the two memory shapes **+** two naturally-sequential shapes **+**
  wire the external `tau3-bench` multi-turn benchmark.
- **Memory model:** build **both** interpretations as separate shapes.
- **Instances:** **3 per shape.**
- **Docs:** backlog spec (this file); no separate team README.

## The shapes (4 bespoke × 3 instances = 12 tasks, + tau3-bench)

1. **`multistep-memory-conversational`** (category: conversation-persona).
   Facts delivered in early steps; recall required in a later step **without**
   any instruction to save them. Measures *implicit* session memory across
   turns — a harness that preserves conversational context passes; one that
   resets per step fails. Recall verifier is deterministic (grep for the exact
   facts), reward strategy `final`.

2. **`multistep-context-fill`** (category: context-management) — **replaced the
   shallow 3-step `multistep-memory-explicit` (operator: "three steps is not
   enough; fill the context").** A genuine long-session test: **11 ingest steps
   (~24K-token document each, ~265K-token corpus, past a 200K window) + 1 recall
   step.** Each chunk hides a non-guessable `MARKER-NN-<sha>` line; the per-step
   verifier requires that marker in `/app/notes.md`, so the agent cannot skip
   reading. The needle facts are planted in chunk_01; step 12 asks to recall
   them "without re-reading" using the notes. A naive agent loses chunk_01 after
   265K of material; a good context-manager (durable notes) recalls it. Corpus
   generated at build (`gen_chunks.py`) so the repo stays lean. Deterministic
   recall verifier, `final` strategy.

3. **`multistep-plan-execute`** (category: tool-orchestration).
   Step 1 produce a plan; subsequent steps execute parts of it, each building on
   the previous step's artifacts. Per-step deterministic verifiers; `mean` so
   partial progress is scored. `min_reward` gates the plan step.

4. **`multistep-scaffold-implement-document`** (category: building-prototypes).
   scaffold (create structure/stubs) → implement (make tests pass) → document
   (README). Deterministic verifiers for scaffold + implement (pytest), judge
   (Opus) for the document step. `min_reward = 1.0` on scaffold so a broken
   scaffold aborts. `mean`.

5. **`tau3-bench`** (external, current-schema adapter) — multi-turn
   customer-service agent benchmark; externally-validated multi-step coverage.
   Generate a small slice, oracle-validate, run × both harnesses.

## Verifier conventions (reuse our existing patterns)

- Deterministic steps: `tests/test.sh` writes `/logs/verifier/reward.json` with
  numeric-only keys (`reward`, `correctness`, …). No string keys (Harbor's
  reward parser rejects non-numeric — learned 2026-05-28).
- Judge steps: `tests/llm_judge.py` → Anthropic **claude-opus-4-7** (operator
  upgraded haiku→Opus 2026-05-28), robust `raw_decode` JSON parse.
- Every task validated free with `--agent oracle` before agent runs; oracle
  `solve.sh` per step must make that step's verifier pass.

## Acceptance criteria

- [ ] 4 bespoke shapes authored as Harbor multi-step (`steps/` layout), 3
      instances each, all oracle-validated (per-step + trial reward).
- [ ] tau3-bench generated (small slice) + oracle-validated.
- [ ] A multi-step sweep config runs the set × openclaw + hermes and produces a
      populated `/compare` grid.
- [ ] This spec kept in sync; results appended to "Status notes".

## Known issue affecting RUNS (not the build)

openclaw cannot drive model *thinking* through OpenRouter — it forces
`--thinking high` and its registry, blind to the underlying model behind the
OpenRouter passthrough, rejects it (`Use one of: off`). Confirmed on both
kimi-k2.6 and deepseek-v4-pro 2026-05-28. Fix is adapter-side (pass `reasoning`
as an OpenRouter body param, like we do `provider`) — tracked separately. Does
not affect authoring or oracle validation of these tasks.

## Status notes

- 2026-05-28: spec written; Harbor multi-step model confirmed from
  `docs/content/docs/tasks/multi-step.mdx` + `src/harbor/trial/multi_step.py`.
- 2026-05-28: **all 12 bespoke multi-step tasks authored + oracle-validated
  12/12** — every step (intro/distractor/recall, record/recall, plan/implement/
  test, scaffold/implement/document) scored 1.0 and every trial rolled up to
  1.0, including the Opus judge on the scaffold→document step. Shapes:
  memory-conversational ×3, memory-explicit ×3 (context-management category),
  plan-execute ×3, scaffold-implement-document ×3. The `steps/` format works in
  our Harbor with the prebaked image + custom agents.
- Harbor gotcha: a local dataset `path` must be a *parent dir of task dirs*;
  point at the task dir itself → "Either datasets or tasks must be provided."
  Validated the set via a symlink dir (`/tmp/ms-all`).
- Remaining: stage the multi-step sweep × openclaw+hermes (gated on the
  openclaw reasoning-passthrough fix); tau3-bench build-validation in progress.

- 2026-06-25: **CLOSED — IMPLEMENTED.** Multi-step is the suite's backbone: 12 of the 33 active tasks use the `steps/` layout — the conversation-persona memory tasks (4–8 steps), the context-management/context-rot tasks (now 18-ingest + recall = 19 steps), and plan-execute → `redesign-module-keep-constraints`. All renamed to human-readable names since; the `scaffold-implement-document` shape was archived (`archive/tasks/building-prototypes/`). All three open items are closed: the openclaw reasoning-passthrough fix RESOLVED (`done/2026-05-28-openclaw-reasoning-RESOLVED.md`), the dedicated multi-step sweep folded into the unified suite (`configs/suite.yaml`), and tau3-bench dropped as out of scope — so the "Known issue affecting RUNS" above is also resolved.

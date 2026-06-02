# New eval tasks — sub-agent spawning + research (design)

- **Epic:** E4 — Task Suite
- **Date:** 2026-05-29
- **Status:** IMPLEMENTED 2026-05-30 — both shapes shipped:
  `tasks/skill-agent-authoring/sub-agent-parallel-decompose-01/` (#55) and
  `tasks/research-rag/agentic-research-with-memory-01/` (#56). Oracle passes
  1.0 on both. Move spec to `done/` after first agent-run completes.
- **Origin:** Operator — "we don't have a test that involves spawning sub-agents…
  we need that," and "a test that demonstrates and emulates an agent doing some
  level of research."
- Both are gaps the current suite under-tests, and both are strong **harness**
  discriminators (not model-only).

## Why these matter
The suite is dominated by single-shot, model-oriented work. Two capabilities that
genuinely separate *harnesses* are under-tested:
- **Delegation / sub-agents** — does the harness spawn and coordinate child agents?
- **Research loop** — multi-step gather→synthesize using tools (browser/search) +
  memory, sustained over turns.

Both harnesses support these natively (confirmed): openclaw **`sessions_spawn`**
(`runtime:"subagent"`, `sessions_yield`, `subagents` list, `subagents.allowAgents`);
hermes **`delegate_task`** (delegation toolset) + `subagent-driven-development` skill
+ kanban orchestrator/worker. Neither needs an external CLI (the openclaw
`coding-agent` skill — external-CLI delegation — is explicitly EXCLUDED).

## Task 1 — sub-agent spawning
**Shape:** a task whose structure rewards decomposition into independent subtasks
that the agent delegates to child agents and then integrates.
- e.g. "process N independent inputs / implement M independent modules, each with
  its own check" — large/parallel enough that a good harness spawns children rather
  than doing it all in one context.
- **Verifier:** deterministic per-subtask checks (all N pass) + a signal that
  delegation actually occurred (e.g. child-session artifacts / per-child output
  files). Reward = fraction of subtasks correct.
- **Fairness:** identical task for both; each uses its OWN native delegation
  (sessions_spawn vs delegate_task). We measure whether the harness *can and does*
  parallelize/coordinate, not a specific API.
- Multi-step `steps/` not required — single instruction that induces delegation is
  cleaner; or a 2-step (plan → execute-via-children).
- Open: how strongly to *require* delegation vs reward it (a harness could brute-force
  serially). Consider a wall-clock/턴-budget that favors parallel children, or assert
  child sessions exist.

## Task 2 — research
**Shape:** emulate real research — gather information from sources, then synthesize
a grounded answer/artifact.
- Uses the shared **browser (CDP)** + **search** + **memory** infra (so it also
  exercises that stack). Possibly a sandboxed/seeded corpus to keep it deterministic
  and offline-safe, OR live web for realism (decide).
- **Verifier:** mix — deterministic checks for required facts/citations present +
  Opus judge (claude-opus-4-7, our standard) for synthesis quality/grounding.
- Distinguish from existing `research-rag` category: this one is **agentic
  multi-source** (the agent decides what to fetch, iterates), not single-shot RAG.
- **Fairness:** same sources/corpus + same browser backend for both.
- Open: live-web vs seeded-corpus (determinism vs realism); citation-grounding
  rubric; whether to require memory writes (store findings) as part of scoring.

## Conventions (reuse)
- Deterministic verifier: `tests/test.sh` → `/logs/verifier/reward.json`, numeric-only.
- Judge: `tests/llm_judge.py` → claude-opus-4-7, robust `raw_decode` parse.
- Oracle-validate (`--agent oracle`) before agent runs.
- Run on the rich-harness image so delegation/browser/memory are actually available.

## Dependencies
- Sub-agent task: needs the rich harness (native delegation enabled) — no infra.
- Research task: needs the **browser/CDP server** + **memory stack**
  (`backlog/2026-05-29-eval-infra-stack.md`) + research skills enabled.

## Open items
- [ ] Decide sub-agent task domain (parallel code modules vs parallel data items).
- [ ] Decide research task source model (seeded corpus vs live web) + grounding rubric.
- [ ] Author both + oracle-validate.
- [ ] Confirm delegation actually fires per harness (inspect child sessions).

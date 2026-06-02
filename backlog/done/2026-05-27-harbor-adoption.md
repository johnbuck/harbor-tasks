# Harbor adoption — retire rube, build on Harbor

- **Epic:** E1 — Harness runtime & adapters
- **Date:** 2026-05-27
- **Status:** IMPLEMENTED 2026-05-27
- **Origin:** Operator question — "do we actually even need to build rube? Are there existing solutions?"

## Problem

`rube` was a from-scratch agent-harness comparison tool (FastAPI + Inspect AI
+ SQLite + React). Before investing further, we needed to know whether the
runner / sandbox / scoring / dashboard layers it was rebuilding already
existed elsewhere. rube's goal: measure + compare agent harnesses (openclaw,
hermes, aider, …) on the same model under identical conditions, reporting
correctness, cost, speed, quality, instruction-following.

Three parallel research passes (GitHub, papers/blogs, live leaderboards/
platforms) plus deep code reviews of the two strongest candidates found:

- **HAL** (`princeton-pli/hal-harness`) — looked close on paper, but code
  review showed it's a benchmark *publisher*: agents are bare Python `run()`
  functions, benchmarks are a hardcoded if/elif registry, no multi-agent
  comparison view, Weave-required telemetry, weak reproducibility. ~30% fit.
- **Harbor** (`harbor-framework/harbor`) — Terminal-Bench team. Multi-agent
  per job, native `/compare` view, pluggable verifiers (pytest + LLM judge),
  multi-axis rewards, strong `lock.json` reproducibility, local-filesystem
  results, **and openclaw + hermes already ship as first-class agents**
  (`AgentName.OPENCLAW`, `AgentName.HERMES`). ~85% fit.

Rebuilding Harbor's runner/sandbox/viewer/reproducibility from scratch in rube
would be months of work to land worse than what Harbor already has.

## Scope

**In:**
- Delete `johnbuck/rube` (operator-authorized).
- Fork `harbor-framework/harbor` → `johnbuck/harbor` (for any framework-side
  patches / upstreamable extensions).
- Create `johnbuck/harbor-tasks` (this repo) for our task suite, job configs,
  rubrics, and adapter extensions — kept separate so upstream Harbor syncs
  stay clean (mirrors `harbor-framework/harbor` + `laude-institute/harbor-datasets`).

**Out:**
- Forking Harbor's core. We extend via subclasses + config, not core edits.
- Re-implementing any runner/scoring/dashboard logic Harbor already has.

## Design decisions

- **Two repos, not one.** Tasks + extensions live in `harbor-tasks`; the fork
  exists for framework-side changes only. Upstream pulls never conflict with
  our content.
- **Extend via subclass, not fork.** Adapter behavior we need (OpenRouter
  routing, skip-install, cost) is added by subclassing Harbor's shipped
  adapters, loaded via `--agent-import-path`.
- **rube's GOAL.md + use cases carry over** as the north star: measure,
  compare (harness as the only variable), reproduce, surface tradeoffs, flag
  bad tasks, show evidence, recommend.

## Acceptance criteria

- [x] rube repo deleted; Harbor forked to johnbuck.
- [x] harbor-tasks repo created and clone-able.
- [x] Sanity run: `harbor run --agent oracle` on a task passes end-to-end.
- [x] A real-LLM trial runs openclaw + hermes side-by-side and produces a
      per-(harness, task) comparison in `result.json`.

## Follow-up tickets

- [[2026-05-27-agent-adapters]] — the subclass + base-image layer.
- [[2026-05-27-task-suite-design]] — what tasks to actually run.

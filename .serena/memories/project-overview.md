# harbor-tasks — Serena onboarding memory

Read **`AGENTS.md`** (repo root; `CLAUDE.md` symlinks to it) first — it is the full
agent guide. This memory is the Serena-specific orientation: what the code is, where
to navigate, and the invariants you must not break.

## What this is
Task suite + run configs + harness adapters for the **openclaw-vs-hermes** comparison
on [Harbor](https://github.com/harbor-framework/harbor). Thesis: *the harness matters
more than the model* — both harnesses run the **same** model (`deepseek-v4-pro` via
OpenRouter) so any gap is the harness. Lives on **the run host** at
`~/benchmarking/harbor-tasks`; the Harbor framework fork is the sibling
`~/benchmarking/harbor` (its `.venv` is what runs sweeps). Edited from the dev
workstation over the `~/mnt/<run-host>/...` sshfs mount; **run git + `harbor run`
on the run host**.

## Code worth navigating with Serena (Python)
- `lib/openclaw_thin.py` (`OpenClawThin`), `lib/hermes_thin.py` (`HermesThin`) — the
  THIN adapters: run each harness against its BAKED image config, capture metrics. The
  live path used by sweeps.
- `lib/openclaw_openrouter.py`, `lib/hermes_no_install.py`, `lib/openclaw_no_install.py`
  — install-capable / provider-routing variants. The OpenRouter provider pin string
  lives here AND in the two harness configs (keep all in sync).
- `tools/roadmap.py`, `tools/task_catalog.py`, `tools/agent_status.py` — the three
  static-HTML dashboard generators. `tools/run_suite.sh`, `tools/run_tau3.sh`,
  `tools/view.sh` — sweep + viewer drivers.
- `metrics/` — post-run weighted aggregators (the suite).
- `hooks/` — Harbor TrialEvent hooks (memory-wipe between steps).
- `tasks/<category>/<shape>-NN/` — each task: `task.toml`, `instruction.md`,
  `environment/Dockerfile`, `tests/test.sh` (+ `steps/` for multi-step).
- `harnesses/{openclaw,hermes}/` — the BAKED harness configs (openclaw.json,
  hermes config.yaml + personas) that bake into `harbor-agents-rich:latest`.

## Invariants (full catalog: backlog/FOOTGUNS.md)
1. Task Dockerfiles MUST `FROM harbor-agents-rich:latest` (never `-prebaked` → openclaw
   "Unknown model: xrouter/...").
2. `reward.json` = FLAT numeric-only dict; a string/nested value makes the viewer
   SILENTLY drop the trial. Provenance → sibling `reward-details.json`.
3. Both harnesses pinned to ONE OpenRouter host (currently `novita`; must support
   deny + tool-use + reasoning); REBUILD the rich image after any pin change.
4. Capabilities (browser/MCP) enabled in the BAKED config + rebuild — thin adapters
   ignore Harbor-injected `mcp_servers`.
5. `jobs_dir` = absolute persistent path (`./jobs`, gitignored), never `/tmp` (tmpfs).
6. n=1 validates plumbing only; verdict needs n≥3 (`pass^k`). Always run the Harbor
   oracle (build+schema, no LLM cost).

## Discrimination (the point of the suite)
Difficulty is the lever, not rubrics. NO TELEGRAPHING (don't tell the agent the trap —
that's the #1 validity bug). KILL test: if `python3 -c` or one file-read solves it,
you're measuring the MODEL not the harness. Recall scorers grade CONTENT, tolerate
FORMAT (a format-strict scorer fabricates false zeros that look like discrimination).

## Cross-session knowledge
Operator memories (Claude memory, not Serena): `harbor-tasks-project`,
`harbor-tasks-discrimination-methodology`, `harbor-provider-pin`,
`harbor-harness-capability-enablement`, `harbor-recall-scorer-format-robust`,
`harbor-context-rot-scoring-integrity`, `harbor-tasks-rich-base-required`,
`harbor-tasks-dashboards-and-epics`. Design rationale per feature: `backlog/` + `done/`.

> Note: `harnesses/openclaw/workspace/AGENTS.md` is a PERSONA file baked into the
> harness under test — not a guide to this repo. The root `AGENTS.md` is.

# tau3-bench integration — spec

- **Date:** 2026-05-28
- **Status:** ORACLE SHIPPED; **AGENT-RUN DEPRECATED 2026-06-02.** The oracle
  (`solution/solve.sh`) validates the eval pipeline and passes. The live
  **agent-run is deprecated**: our thin adapters run the BAKED harness
  (`openclaw agent --local --json`) and do NOT forward Harbor's injected
  `[[environment.mcp_servers]]`, so the `tau3-runtime` MCP never reaches the
  agent. Closing the gap would require an install-during-trial / MCP-forwarding
  adapter (was task #84) — not worth building for a single benchmark. tau3 is
  retained as oracle-only pipeline validation; the live conversation eval is out
  of scope. Re-open only if a real harness-discrimination need for tau3 emerges.
- **Origin:** Operator — "build it now, don't defer; write a spec then build."

## What tau3-bench is

Customer-service agent benchmark (375 base tasks; airline/retail/telecom
domains) built on Sierra's tau2-bench. The agent works a multi-turn,
half-duplex conversation with a **simulated user** and a set of **domain tools**,
following a policy. Reward is binary, scored on DB-state correctness +
required-communication (`reward_basis = [DB, COMMUNICATE]`) plus NL assertions.

## Architecture (how a trial runs)

- **Multi-container via docker-compose overlay.** Each task ships
  `environment/docker-compose.yaml` adding a `tau3-runtime` sidecar alongside
  Harbor's `main` (agent) container. Harbor supports this via
  `EnvironmentConfig.extra_docker_compose` + the `docker_compose` environment
  capability. The task's compose is auto-detected.
- **tau3-runtime sidecar** (built from `environment/runtime-server/`, exposes
  `:8000`) hosts the tau2 simulation + domain tools as a **streamable-http MCP
  server**. Declared in task.toml as `[[environment.mcp_servers]] name="tau3-runtime"
  url="http://tau3-runtime:8000/mcp"`. Harbor injects this MCP into the agent.
- **Agent contract** (from `instruction.md`): call `start_conversation` once,
  `send_message_to_user` to talk, domain tools to act, `end_conversation` (or
  `###STOP###`) to finish. One tool OR one message per step, never both.
- **Simulated user + assertion judge are LLMs**, configured by env:
  - sidecar: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `TAU2_USER_MODEL` (default gpt-5.2)
  - verifier: `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `TAU2_NL_ASSERTIONS_MODEL`
- **Verifier** (`tests/evaluate.py`) reads the runtime's
  `/logs/agent/tau3_runtime_state.json`, calls tau2 `evaluate_simulation`,
  writes a binary reward.
- **Oracle** (`solution/solve.sh`) constructs the tau2 env in Python and replays
  reference actions — validates the eval pipeline without a live conversation
  (but the verifier's NL-assertion judge still calls an LLM).

## LLM routing decision (privacy + cost)

Point the sim-user + assertion-judge at our **OpenRouter** account
(OpenAI-compatible endpoint), NOT gpt-5.2 (expensive):
- `OPENAI_BASE_URL = https://openrouter.ai/api/v1`
- `OPENAI_API_KEY = $OPENROUTER_API_KEY`
- `TAU2_USER_MODEL` / `TAU2_NL_ASSERTIONS_MODEL` = a cheap model.
**Open risk:** tau2 likely uses litellm; routing an OpenRouter model id through
the openai-provider base_url can mis-parse the provider prefix. The build step
below is partly a test of which model string litellm posts verbatim. The
sim-user traffic is synthetic role-play (no sensitive data), but for consistency
we still prefer the privacy pool where the routing allows it.

## Build plan

1. Generate a small slice (done — 5 airline tasks at
   `/tmp/harbor-benchmarks/tau3-bench`, current schema 1.1).
2. **Oracle build-validation**: run `--agent oracle` on 1–2 tasks with the
   OpenRouter LLM mapping. Confirms: compose builds both images, tau2 env
   constructs, evaluate.py + NL-assertion judge run, reward written. Iterate on
   the model string until the judge call succeeds.
3. **Agent run**: run × openclaw + hermes via the install-capable adapters.
   Requires each harness to consume Harbor's streamable-http MCP config and
   drive the tau3-runtime tools.

## Risks / unknowns (surface, don't pre-defer)

- **MCP support per harness:** openclaw supports MCP; hermes MCP support via
  Harbor's `mcp_servers` injection is unconfirmed. If hermes can't consume the
  MCP, tau3 measures openclaw only (still a data point) — flag, don't silently drop.
- **openclaw thinking-via-OpenRouter** (same known issue as the rest): the agent
  model still routes through our OpenRouter pool; the `--thinking` registry gap
  applies. Adapter reasoning-passthrough fix tracked separately.
- **litellm/OpenRouter model routing** for the sim-user/judge (see above).
- **Cost/time:** `[agent] timeout_sec = 3600`, cpus=4/mem=8GB per task, live
  multi-turn conversation → far heavier per trial than our other tasks. Keep
  the slice small (≤5).

## Acceptance criteria

- [ ] Oracle validates ≥1 tau3 task end-to-end in our Harbor (compose + runtime
      + verifier + judge).
- [ ] At least openclaw runs a tau3 task via MCP and produces a scored trial.
- [ ] Result + the MCP/hermes finding appended to "Status notes".

## Status notes

- 2026-05-28: 5-task airline slice generated (current schema). Architecture
  mapped from task files + `src/harbor/environments` (compose capability
  confirmed present).
- 2026-05-28: **oracle build-validation PASSED** (tau3-airline-0, reward 1.0,
  0 exceptions, 4m12s). Confirms end-to-end in our Harbor: docker-compose
  multi-container (agent `main` + `tau3-runtime` sidecar) builds + runs, tau2
  env constructs, verifier + NL-assertion judge execute, reward written.
- 2026-05-28: **LLM routing solved.** The sim-user + assertion-judge route
  through our OpenRouter account as an OpenAI-compatible endpoint:
  `OPENAI_BASE_URL=https://openrouter.ai/api/v1`, `OPENAI_API_KEY=$OPENROUTER_API_KEY`,
  `TAU2_USER_MODEL=TAU2_NL_ASSERTIONS_MODEL=openai/gpt-5-nano` — litellm posts
  these fine. **These must be exported in the harbor PROCESS env** (not just
  the container env list) because task.toml `[verifier.env]` resolves
  `${OPENAI_API_KEY}`/`${OPENAI_BASE_URL}` at config-load; run via
  `infisical run --domain=http://internal-host:8380 --projectId=INFISICAL_PROJECT_ID --env=production --path=/proxy/ -- bash -c 'export OPENAI_API_KEY="$OPENROUTER_API_KEY"; …;
  uv run harbor run …'` (self-hosted only — NEVER Infisical Cloud).
- Remaining: the **agent run** (openclaw/hermes via the tau3-runtime MCP) — same
  openclaw reasoning-passthrough caveat as the rest, plus the hermes-MCP unknown.
- 2026-05-30: **agent-run attempt #1 = BLOCKED.** Sierra's tau3 task Dockerfile
  doesn't extend `harbor-agents-prebaked` (it builds its own sidecar image and
  uses a stock base for the agent container — no NVM, no openclaw binary).
  Both our adapters (`openclaw_thin` and `openclaw_no_install`) assume openclaw
  is pre-installed: thin runs `. ~/.nvm/nvm.sh && nvm use 22 && openclaw --version`,
  no-install runs `openclaw --version` directly. Both fail `command not found` /
  `No such file or directory`. **Fix paths**: (a) modify each tau3 task's
  Dockerfile to `FROM harbor-agents-prebaked` and re-add the tau3 sidecar wiring
  by hand (~30 LoC per task × 5 tasks); (b) write a third "install-during-trial"
  openclaw adapter that runs `npm i -g openclaw` at agent-setup time
  (~50 LoC, generic); (c) build a unified tau3-on-prebaked image upstream
  (cleanest but most work). **Operator-gated** — leaving tau3 agent-run
  acceptance criterion unmet for v1; Track A sweep (#78) is the headline.
  Track-A artifacts in `/tmp/harbor-jobs/tau3-openclaw-smoke*` for diagnostic
  reference.

# Pre-built rich harnesses — design + build spec

- **Date:** 2026-05-28 (design); shipped 2026-05-29.
- **Status:** **SHIPPED.** Rich image `harbor-agents-rich:latest` builds
  from `environments/agent-rich/Dockerfile`; thin adapters are
  `lib/openclaw_thin.py` and `lib/hermes_thin.py`. End-to-end parity
  verified — both `Reward 1.0 / 0 exceptions` on
  `tasks/_verify/reasoning-parity-01` via `configs/verify-rich.yaml`, with
  `reasoning_tokens > 0` for both (the FOOTGUNS #1 mandatory gate).
- **Companion shipped specs:**
  - [2026-05-29-thin-adapters.md](2026-05-29-thin-adapters.md)
  - [2026-05-29-memory-stack-deployment.md](2026-05-29-memory-stack-deployment.md)
  - [2026-05-29-hermes-dual-plugin-system.md](2026-05-29-hermes-dual-plugin-system.md)
  - [2026-05-29-agent-status-dashboard.md](2026-05-29-agent-status-dashboard.md)
- **Origin:** Operator — "STOP USING THE PACKAGED HARNESSES." Stop letting Harbor's
  bundled `installed.openclaw`/`installed.hermes` adapters reconstruct a barebones
  config; bring **pre-built, fully-configured** harnesses whose own config carries
  reasoning + skills + persona + memory. Harbor only invokes + measures.

## Why (the core problem)

Harbor's bundled adapters throw away the harness's real config and rebuild a
minimal one (`OpenClaw._DEFAULT_CONFIG = {}`; `Hermes._build_config_yaml` →
`toolsets:[hermes-cli]`, memory off, no skills, no persona; and it sets
`HERMES_HOME=/tmp/hermes`, **bypassing the baked `~/.hermes`**). Every capability
then has to be reverse-engineered field-by-field through the adapter (this is
where the whole openclaw `reasoning:true`/compat/custom-provider saga came from —
see `FOOTGUNS.md` #1). A pre-built harness makes reasoning + memory + skills come
from the harness's OWN config, dissolving that entire class of problem.

## What's actually in the assessment image (`harbor-agents-prebaked:latest`)

Inspected 2026-05-28. The two are **asymmetric**:

**openclaw**:
- No baked *user* config/persona (`~/.openclaw/` empty besides plugins), but the
  PACKAGE ships **~62 bundled skills** (`<pkg>/skills/` ~57 + extension skills:
  browser-automation, obsidian/wiki-maintainer, prose, tavily) and 46 provider
  plugins incl. **`memory-core`**. (Earlier "0 skills" was a mistake — I checked
  the empty `~/.openclaw/skills/` user dir, not the package.) `openclaw skills
  check` reports which are ready vs missing requirements.
- Config/persona (openclaw.json + workspace files) is what we supply.

**hermes** — batteries-included (but unused by our runs):
- Ships `~/.hermes/`: `config.yaml` (template; default `anthropic/claude-opus-4.6`,
  `provider:auto`, base_url OpenRouter) + `SOUL.md` (persona slot, **empty** by
  default; auto-seeded from `DEFAULT_SOUL_MD`) + cron/hooks/caches.
- ~58 toolsets: `memory`, `delegation`, `kanban`, `search`, `terminal`, `file`,
  `code_execution`, `browser`, `vision`, `web`, `moa`, messaging, …
- Large packaged skill catalog (`skills/` + `optional-skills/`): autonomous-ai-agents
  (claude-code, codex, hermes-agent, **kanban orchestrator/worker** = subagents),
  creative/*, devops, github/codebase-inspection, apple/*, and
  **`optional-skills/autonomous-ai-agents/honcho`**.
- Memory is a **pluggable provider** system (`plugins.memory.load_memory_provider`);
  honcho/mem0/etc. are providers. **Honcho is a first-class hermes feature** →
  this is why Honcho is hermes-only.

**Critical gap:** none of hermes's baked richness is active in our runs (adapter
redirects `HERMES_HOME` + writes barebones config). openclaw likewise barebones.
So we've been comparing two stripped agents. The raw materials are already in the
image — the build is mostly **configuration**, not new installs.

## Memory matrix (operator-specified)

| Backend | openclaw | hermes | Integration |
|---|---|---|---|
| **recall** (existing Graphiti MCP on <memory-host> `recall-mcp:8407`) | ✅ | ✅ | MCP server; per-agent isolation via `group_id`. recall reads `X-Group-ID` header (Caddy injects it) OR explicit `group_id=` per call. **Each agent its own group_id** (e.g. `eval-openclaw`, `eval-hermes`) so memories don't collide AND don't pollute prod (<prod-group>/<prod-group>) graphs. |
| **Hindsight** (`vectorize-io/hindsight`, self-host) | ✅ | ✅ | built-in streamable-HTTP MCP at `/mcp/`; per-agent via `bank_id` / `X-Bank-Id`. |
| **Honcho** (`plastic-labs/honcho`, self-host) | ❌ | ✅ | hermes **native skill** (`hermes honcho setup` → local → base URL; `honcho.json`; `pip honcho-ai`). NOT a generic MCP for hermes. |

All three in **one docker-compose stack** on the homelab (recall already exists;
add Honcho + Hindsight). Honcho self-host = api(8000)+deriver+pgvector+redis;
Hindsight = single image (8888 API/9999 UI, embedded PG) or external-PG compose.
Both bundle pgvector on 5432 → keep internal / separate DBs. (Full deployment
shapes: research notes in session; repos plastic-labs/honcho, vectorize-io/hindsight.)

## Rich config design

### openclaw (`openclaw.json`)
- **Reasoning ON** via the verified recipe (FOOTGUNS #1): custom `xrouter` provider
  → OpenRouter OpenAI endpoint, `reasoning:true` + `compat.supportedReasoningEfforts`,
  `--thinking high`, `apiKey:${XROUTER_API_KEY}`.
- **memory-core** plugin enabled (native memory).
- **Skills:** a defined set copied to `~/.openclaw/skills/`.
- **Persona/system prompt:** defined operator persona.
- **MCP servers:** recall (`/mcp/recall-<eval-id>/`) + Hindsight (`/mcp/<bank>/`).
- **Subagents:** openclaw subagent config.

### hermes (`config.yaml` + `~/.hermes` home, NOT bypassed)
- **Reasoning ON** via `provider: custom` + `custom_providers[].extra_body:
  {reasoning_effort: high}` + `key_env: OPENROUTER_API_KEY` (verified mechanism;
  end-to-end reasoning_tokens>0 still to confirm).
- **SOUL.md:** real persona (mirror intent of openclaw's).
- **Toolsets:** memory, delegation, kanban, search, terminal, file, code_execution
  (+ web/vision as needed).
- **Skills:** preload a defined set (incl. honcho) via config/`-s`.
- **Memory providers:** honcho (native) + recall & Hindsight as MCP (`mcp_servers:`).
- **Subagents:** delegation / kanban orchestrator+worker.

### Fairness
Same model (deepseek-v4-pro via OpenRouter), reasoning on for BOTH, same memory
backends (recall+Hindsight both; Honcho hermes-only by design), equivalent skills
+ persona intent. How well each harness *uses* these is the harness signal.

## Delivery
- Build a rich-harness image (extend the prebaked base): bake both harnesses' real
  configs + skills + persona; install `honcho-ai` for hermes.
- **Thin Harbor adapter**: invoke the harness against the task + capture
  tokens/cost/result. Does NOT rewrite config. (Replaces the config-generation in
  the bundled `installed.*` adapters.)
- External benchmark tasks: layer `FROM <benchmark-image>` + the harness setup.

## Open items / next steps
1. Stand up Honcho + Hindsight on homelab (one compose stack) — operator-approved deploy.
2. Draft `openclaw.json` + hermes `config.yaml`/`SOUL.md` rich configs.
3. Thin adapter that uses baked config (no rewrite) + reads results.
4. Re-confirm reasoning parity on the rich images (reasoning_tokens>0 BOTH).
5. eval-specific recall `group_id`s + Caddy/route or explicit-group_id plan so eval
   memory is isolated from prod agents.

## Verified facts feeding this
- openclaw reasoning recipe: `FOOTGUNS.md` #1 (verified, reasoning_tokens=143/327).
- hermes reasoning OFF by default on deepseek-v4-pro (parity run: openclaw 143 vs
  hermes 0) — because the STOCK Harbor adapter never set `reasoning_effort`. Fix is
  the NATIVE `agent.reasoning_effort: high` (now in `harnesses/hermes/config.yaml`),
  NOT a custom-provider/extra_body hack. Re-verify on the rich image (task #53).
- recall architecture: `homelab/<memory-host>/tenants/<run-host>/docs/recall/recall.md`.

---

## Skills — grounded inventory + what's ACTUALLY active (2026-05-29)

Both harnesses ship rich skill catalogs (my earlier "openclaw 0 skills" was wrong —
I checked the empty `~/.openclaw/skills/` user dir, not the package).

| | openclaw | hermes |
|---|---|---|
| Bundled in package | ~57 core `skills/` + 5 extension skills | 90 `skills/` + 84 `optional-skills/` (incl. honcho) |
| **Active in BARE sandbox** | **13** (requirement-gated: bins+env+config+os) | **0** in a fresh home; **85** when `$HERMES_HOME/skills/` is seeded |
| Gating rigor | strict — bins+env+config+os (`openclaw skills check`) | loose — only `prerequisites.commands` + `platforms` (NOT API keys) → "runnable" count inflated |

**Critical:** Harbor's stock adapter sets `HERMES_HOME=/tmp/hermes` (fresh) → hermes
runs with **0 skills** today, while openclaw runs with 13. The pre-built fix: seed a
proper hermes home so its 85 builtins are enabled. (FOOTGUNS #12.)

openclaw's 13 active (bare): canvas, diagram-maker, healthcheck, meme-maker,
node-connect, node-inspect-debugger, notion, python-debugpy, skill-creator, spike,
taskflow, taskflow-inbox-triage, weather.

Verification gotcha: `pyyaml` is NOT in the image's base `python3` — use
`/usr/local/lib/hermes-agent/venv/bin/python` to parse SKILL.md frontmatter, else a
script silently sees zero requirements. (FOOTGUNS #13.)

## Agreed common skill set (aligned to the 18 task categories)

**Enable on BOTH** (pure-prompt unless noted):
- Debugging: `systematic-debugging`, `python-debugpy` (needs debugpy pip),
  `node-inspect-debugger` (node present)
- `test-driven-development`, `spike`
- Planning: `plan`/`writing-plans` (hermes) ↔ `taskflow` (openclaw)
- Skill authoring: `hermes-agent-skill-authoring` ↔ `skill-creator`
- `subagent-driven-development` (uses native delegation — see below)
- Code review (local): `requesting-code-review`
- Diagrams: `architecture-diagram`/`design-md` ↔ `diagram-maker` (emit SVG/HTML text)
- Data science: `data-science/jupyter-live-kernel` (needs jupyter+ipykernel)

**Task-category → capability map:** code-editing/test-authoring/ops-debugging/
migration → debugging+TDD+spike; tool-orchestration/building-prototypes → planning+
subagent-dev; skill-agent-authoring → skill-authoring; code-spec-review/
compliance-security → code-review; data-analytics → jupyter; building-designs →
diagrams; **conversation-persona/context-management/research-rag/insights-research →
MEMORY stack** (the infra is the aligned capability for these 4); documentation/
marketing → base ability (no dedicated skill).

**EXCLUDED (with reason):**
- `canvas` (openclaw) — renders to a connected OpenClaw *node*; none in a headless
  eval container → inert. Not a task-doing skill.
- `coding-agent` (openclaw) / `autonomous-ai-agents/{claude-code,codex,opencode,pi}`
  (hermes) — **CONFIRMED external-CLI delegation** (spawns Claude Code/Codex/etc.).
  Would measure the sub-CLI, not the harness. Use NATIVE subagents instead.
- `healthcheck` (openclaw) — host-hardening audit; no task-suite alignment (keep
  optionally; no infra).
- API-key/service skills (notion, linear, airtable, spotify, github-via-gh, …) —
  need creds/services absent in the sandbox.

## Sub-agent spawning — CONFIRMED native on both
- **openclaw:** `sessions_spawn` (`runtime:"subagent"` default, in-harness),
  `sessions_yield` (await child completion), `subagents` (list), `context:fork|isolated`,
  config `subagents.allowAgents`. Docs: docs.openclaw.ai/tools/subagents. NOT the
  external `coding-agent` path.
- **hermes:** `delegate_task` (delegation toolset) + `subagent-driven-development`
  skill + kanban orchestrator/worker.
- So agent-driven-development is a fair comparison. New eval task to exercise it:
  `backlog/2026-05-29-new-eval-tasks-subagent-research.md`.

## Infrastructure required (see eval-infra-stack spec)
Memory (recall + Hindsight + Honcho) + shared browser/CDP, one compose stack;
plus image bakes jupyter/ipykernel + debugpy. Full design:
`backlog/2026-05-29-eval-infra-stack.md`. Browser: both connect via CDP (openclaw
browser-cdp; hermes browser_provider `cdp_url`) — neither ships a browser.

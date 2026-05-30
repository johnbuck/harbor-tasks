# Pre-built rich harnesses

Fully-configured openclaw + hermes for the assessment. These are the harnesses'
**own** configs (reasoning + skills + persona + memory baked in). The thin Harbor
adapter only invokes the harness and reads results — it must NOT regenerate these.

Design + rationale (shipped 2026-05-29):
- [`backlog/done/2026-05-28-prebuilt-rich-harnesses-SHIPPED.md`](../backlog/done/2026-05-28-prebuilt-rich-harnesses-SHIPPED.md) — the original "stop using packaged harnesses" pivot.
- [`backlog/done/2026-05-29-thin-adapters.md`](../backlog/done/2026-05-29-thin-adapters.md) — `OpenClawThin` / `HermesThin` design, one-key auth, persona staging, verification reproducer.
- [`backlog/done/2026-05-29-memory-stack-deployment.md`](../backlog/done/2026-05-29-memory-stack-deployment.md) — the memory endpoints these harnesses target.
- [`backlog/done/2026-05-29-hermes-dual-plugin-system.md`](../backlog/done/2026-05-29-hermes-dual-plugin-system.md) — investigation behind the activation accuracy in the dashboard.
- [`backlog/done/2026-05-29-agent-status-dashboard.md`](../backlog/done/2026-05-29-agent-status-dashboard.md) — `tools/agent_status.py`.

## Files

```
harnesses/
├── openclaw/
│   ├── openclaw.json       # → baked to ~/.openclaw/openclaw.json
│   └── workspace/          # → baked to the agent workspace (~/.openclaw/workspace/)
│       ├── SOUL.md         #   persona (identity, tone, boundaries)
│       ├── AGENTS.md       #   operating instructions (read at session start)
│       ├── IDENTITY.md     #   name / vibe / emoji (fixed; no bootstrap)
│       ├── USER.md         #   who the operator is
│       ├── TOOLS.md        #   tool orientation notes (not tool availability)
│       └── HEARTBEAT.md    #   minimal (no proactive heartbeat for eval)
└── hermes/
    ├── config.yaml         # → baked to $HERMES_HOME/config.yaml
    └── SOUL.md             # → baked to $HERMES_HOME/SOUL.md  (persona)
```

OpenClaw injects the workspace files into the system prompt's "Project Context"
on the first turn of a session (truncated per-file at
`agents.defaults.bootstrapMaxChars`, default 12000). No `BOOTSTRAP.md` is shipped
— identity is fixed, so no first-run bootstrap ritual occurs.

## Capability parity (both harnesses)

| Capability | openclaw | hermes |
|---|---|---|
| Reasoning ON | `xrouter` custom provider + `reasoning:true` + compat, `thinkingDefault:high` | native `agent.reasoning_effort: high` + `provider: openrouter` (real default; no custom-provider hack) |
| Persona | workspace `SOUL.md` (+ AGENTS/IDENTITY/USER) → Project Context | `$HERMES_HOME/SOUL.md` |
| Skills | several (→ `~/.openclaw/skills/`) | several incl. honcho (preload) |
| Subagents | openclaw subagents | `delegation` + `kanban` toolsets |
| recall (Graphiti MCP) | ✅ group `eval-openclaw` (23 tools post-hindsight-parity 2026-05-30) | ✅ group `eval-hermes` (23 tools) |
| Hindsight (MCP) | ✅ bank `eval-openclaw` | ✅ bank `eval-hermes` |
| Honcho | ✗ | ✅ native (`hermes honcho setup`) |

Same model (deepseek-v4-pro / OpenRouter), reasoning on for both → fair.

## Build steps (rich-harness image, extends harbor-agents-prebaked)

openclaw:
1. `COPY openclaw/openclaw.json ~/.openclaw/openclaw.json` (JSON5).
2. `COPY openclaw/workspace/* ~/.openclaw/workspace/` (persona = these workspace
   files; injected into Project Context at session start).
3. `openclaw plugins enable memory-core` (optional native memory).
4. `COPY` chosen skill dirs → `~/.openclaw/skills/`  (TODO: pick the skill set).

hermes (do NOT let the adapter redirect HERMES_HOME away from this):
1. `COPY hermes/config.yaml hermes/SOUL.md $HERMES_HOME/`
2. `pip install honcho-ai` then `hermes honcho setup` → local → base URL = our Honcho.
3. Preload skill set incl. honcho (VERIFY: config key vs `-s` flag at invocation).

## Memory endpoints — DEPLOYED + verified (2026-05-29)

All three live on wiley, folded into the existing recall compose stack
(`~/Docker/recall/docker-compose.yml`; source mirror in repo `infra/`). recall
was NOT relocated. All share `pinkleberry_bridge`; eval agents reach them over
the LAN.

| Service | URL used in configs | Status |
|---|---|---|
| recall (Graphiti MCP) — prod ontology | `http://wiley-pinkleberry.lan:8407/mcp` | LIVE — juliet/yui/akane groups |
| recall-eval (Graphiti MCP) — coding ontology | `http://wiley-pinkleberry.lan:8408/mcp` | LIVE — eval-openclaw/eval-hermes groups; both harnesses point here |
| Hindsight MCP | `http://wiley-pinkleberry.lan:8888/mcp/<bank>/` | LIVE (8888 API+MCP, 9999 UI) |
| Honcho API | `http://wiley-pinkleberry.lan:8000` | LIVE (hermes memory provider) |
| mem-embed (shared bge-m3) | `http://mem-embed/v1` (bridge-internal) | LIVE — 1024-dim, serves recall + hindsight + honcho (2026-05-29 migration) |

Memory-derivation LLM = OpenRouter `deepseek-v4-flash` (no-train at the OpenRouter
account level) for **all three** stacks as of 2026-05-29 (recall was on
`z-ai/glm-4.6` until then; swapped for eval-fairness). Embeddings = bge-m3
(1024-dim) for all three — recall's bge-small/384 → bge-m3/1024 migration was
done in-place (746 :Entity + 1,078 :RELATES_TO vectors re-embedded). See
[`done/2026-05-29-recall-bge-m3-and-eval-ontology.md`](../backlog/done/2026-05-29-recall-bge-m3-and-eval-ontology.md).

**Recall agent surface** (post-hindsight-parity, 2026-05-30): 23 tools —
the original 9 Graphiti CRUD (`add_memory`, `search_nodes`, `search_memory_facts`,
`get_entity_edge`, `get_episodes`, `delete_entity_edge`, `delete_episode`,
`clear_graph`, `get_status`) all carrying hindsight-style coaching descriptions,
plus `reflect` (P2), `get_bank_config` / `update_bank_config` (P3 dispositions
+ mission + retain_mission), `list_directives` / `create_directive` /
`delete_directive` (P3 stackable rules), `clear_bank_data` (P3 orphan cleanup),
and 7 mental-model tools (P4: `list/get/create/update/refresh/delete/clear_mental_model`
+ daily 02:00 refresher cron + hourly retry timer). See
[`done/2026-05-29-recall-hindsight-style-plugin.md`](../backlog/done/2026-05-29-recall-hindsight-style-plugin.md)
for the design + 4-phase build + post-implementation review.

Per-agent isolation (verified): recall `X-Group-ID` (openclaw DOES forward custom
MCP headers — confirmed), Hindsight bank, and Honcho workspace are all
`eval-openclaw` / `eval-hermes` — separate from prod groups (juliet/yui) so eval
memory never pollutes production graphs.

## Resolved at test time (2026-05-29) — no longer guesses

- **openclaw forwards custom MCP headers** — CONFIRMED via a header-echo probe:
  `X-Group-ID` (and arbitrary headers) ARE sent. Only `Host` is special (undici
  derives it from the URL authority and ignores a `headers.Host`), which is why
  the old `Host: localhost:8407` trick failed. Fix was server-side: recall's
  DNS-rebind allowlist now permits `wiley-pinkleberry.lan:*` (protection stays
  ON). So recall per-agent isolation works for openclaw with NO juliet pollution.
- **honcho on hermes** = native memory PROVIDER (not an MCP, not `honcho setup`):
  `memory.provider: honcho` + `$HERMES_HOME/honcho.json` (`baseUrl` →
  self-hosted, no apiKey since `AUTH_USE_AUTH=false`) + `honcho-ai` pip in the
  image (installed via uv — the hermes venv has no pip). Verified: it does NOT
  break hermes startup (0 exceptions).
- **hermes reasoning** = native `agent.reasoning_effort: high`; **privacy routing**
  = native `provider_routing.data_collection: deny` — straight from the shipped
  `cli-config.yaml.example`.
- **MCP-down tolerance** — both harnesses log a warning and continue when a memory
  server is unreachable (non-fatal); a dead server adds a ~30s startup timeout.

Still best-effort / open:
- **openclaw `thinkingDefault`** — the thin adapter also passes `--thinking high`
  belt-and-suspenders, so reasoning is on regardless.
- **openclaw persona** — workspace files (SOUL/AGENTS/IDENTITY/USER) are copied
  into the task cwd at run start (`skipBootstrap` suppresses the ritual); deep
  spot-check of Project Context rendering still TODO.
- **Browser/CDP** — not deployed yet (task #54).

## MANDATORY gate after build — PASSED 2026-05-29

Confirm `reasoning_tokens > 0` in BOTH harnesses' session logs on a real task
before trusting any comparison (FOOTGUNS #1). Verified on `reasoning-parity-01`:
openclaw `reasoning_tokens=161`; hermes 8 `reasoning_content` blocks / 1870 chars
(deepseek's OpenRouter route reports a 0 token counter but the reasoning content
is present). Both reward 1.0, 0 exceptions, via the thin adapters off baked
configs. Re-run this gate whenever the image or model changes.

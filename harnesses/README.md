# Pre-built rich harnesses

Fully-configured openclaw + hermes for the assessment. These are the harnesses'
**own** configs (reasoning + skills + persona + memory baked in). The thin Harbor
adapter only invokes the harness and reads results — it must NOT regenerate these.

Design + rationale: `backlog/2026-05-28-prebuilt-rich-harnesses.md`.

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
| recall (Graphiti MCP) | ✅ group `eval-openclaw` | ✅ group `eval-hermes` |
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

## Memory endpoints (fill once the stack is up)

One docker-compose stack on the homelab (recall already exists; add Honcho + Hindsight):

| Service | URL used in configs | Status |
|---|---|---|
| recall (Graphiti MCP) | `http://internal-host:8407/mcp` | EXISTS |
| Hindsight MCP | `http://internal-host:8888/mcp/<bank>/` | port TBD on deploy |
| Honcho API | `http://internal-host:8000` (hermes honcho setup) | TBD on deploy |

Per-agent isolation: recall `X-Group-ID` and Hindsight bank = `eval-openclaw` /
`eval-hermes` — deliberately separate from prod groups (<prod-group>/<prod-group>) so eval memory
never pollutes production graphs.

## VERIFY at test time (drafted best-effort from image inspection)

- **openclaw `mcp.servers[].headers`** — confirm custom headers (esp. `X-Group-ID`,
  `Host`) are honored. If not, fall back to a per-eval Caddy route or explicit
  `group_id=` in calls. (hermes `mcp_servers` headers ARE documented-supported,
  cli-config.yaml.example line ~779.)
- **openclaw `agents.defaults.thinkingDefault`** — confirm it's read (else set on
  `agents.main` or keep the thin adapter passing `--thinking high`).
- **openclaw persona** — exact workspace-file → Project Context injection (docs
  confirm SOUL/AGENTS/IDENTITY/USER; spot-check it renders in the system prompt).
- **hermes skills preload** — config key vs `-s` invocation flag (default
  `hermes-cli` already loads the skills toolset; preloading specific skills TBD).
- **hermes honcho** — `hermes honcho setup` writes `~/.honcho/config.json`;
  confirm the active memory path uses it.

(Resolved, no longer guesses: hermes reasoning = native `agent.reasoning_effort`;
hermes privacy routing = native `provider_routing.data_collection`; both lifted
straight from the shipped default `cli-config.yaml.example`.)

## MANDATORY gate after build

Confirm `reasoning_tokens > 0` in BOTH harnesses' session logs on a real task
before trusting any comparison (FOOTGUNS #1). Parity is only real when both reason.

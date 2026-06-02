# Eval infrastructure stack — memory + browser (design)

- **Epic:** E3 — Capability infrastructure (memory + browser)
- **Date:** 2026-05-29
- **Status:** **MEMORY portion SHIPPED 2026-05-29** (see
  [`done/2026-05-29-memory-stack-deployment.md`](done/2026-05-29-memory-stack-deployment.md)
  for the as-deployed reality, deploy reproducer, and gotchas captured during
  the rollout). Browser/CDP portion still OPEN — tracked as task #54.
- **Goal:** Give both harnesses the external capabilities they need to perform at
  their best, in **one docker-compose stack** on the homelab: persistent memory
  (recall + Hindsight + Honcho) and a shared headless browser (CDP). Per-agent
  isolation so eval memory never pollutes prod (juliet/yui) graphs.
- Companion (shipped):
  [`done/2026-05-28-prebuilt-rich-harnesses-SHIPPED.md`](done/2026-05-28-prebuilt-rich-harnesses-SHIPPED.md).

## Why these (task-category alignment)
- **Memory** serves 4 task categories that literally test it: `conversation-persona`,
  `context-management`, `research-rag`, `insights-research`.
- **Browser** serves `research-rag`, `insights-research`, `marketing` (web research),
  `building-prototypes`, `building-designs` (web UIs), `tool-orchestration`.

## Memory matrix (operator-specified)
| Backend | openclaw | hermes | How wired |
|---|---|---|---|
| **recall** (Graphiti, EXISTS on wiley) | ✅ | ✅ | MCP `http://internal-host:8407/mcp`; per-agent via `X-Group-ID` header + `Host: localhost:8407` rewrite (recall's DNS-rebind guard). groups `eval-openclaw` / `eval-hermes`. |
| **Hindsight** (vectorize-io) | ✅ | ✅ | built-in streamable-HTTP MCP; per-agent **bank** via URL path `/mcp/<bank>/` or `X-Bank-Id`. banks `eval-openclaw` / `eval-hermes`. |
| **Honcho** (plastic-labs) | ❌ | ✅ | hermes **native skill**, not MCP: `pip install honcho-ai` + `hermes honcho setup` → local → base URL = our Honcho API. Config in `~/.honcho/config.json` (HONCHO_API_KEY). |

recall already runs as its own stack (`~/Docker/recall/`, 3 services). Operator wants
the new pieces in "the same stack" — see Deployment note below.

## Components

### recall (existing — reference only)
`recall-mcp:8407` (Graphiti MCP) + `recall-neo4j:7688/7475` + `recall-embed` (TEI),
on `pinkleberry_bridge`. LLM extraction via OpenRouter `z-ai/glm-4.6` (no-train).
Source `~/Docker/recall/`. Don't rewrite the working deploy; new services join its
network. Full doc: `homelab/pinkleberry/tenants/thringle/docs/recall/recall.md`.

### Hindsight (`ghcr.io/vectorize-io/hindsight`)
- One image w/ **embedded Postgres**: ports **8888** (API+MCP) + **9999** (UI),
  volume for `~/.hindsight-docker/.pg0`. OR external-PG compose (`pgvector/pgvector:pg18`
  + hindsight) — env `HINDSIGHT_API_DATABASE_URL`, `HINDSIGHT_DB_PASSWORD`.
- LLM provider: `HINDSIGHT_API_LLM_PROVIDER` + `HINDSIGHT_API_LLM_API_KEY`.
  Supports `ollama`/`lmstudio`/openai-compatible → **point at wiley llama-cpp or
  OpenRouter (data_collection deny)** to keep it private. Use the **slim** image +
  external embeddings to avoid bundling heavy models.
- MCP: streamable-HTTP at `http://<host>:8888/mcp/` (multi-bank) or `/mcp/<bank>/`.
- Auth (optional, prod-recommended): `HINDSIGHT_API_TENANT_EXTENSION=...ApiKeyTenantExtension`
  + `HINDSIGHT_API_TENANT_API_KEY`.

### Honcho (`github.com/plastic-labs/honcho`, build from source — no prebuilt image)
- Compose services: `api` (FastAPI, **8000**), `deriver` (worker), `database`
  (`pgvector/pgvector:pg15`, 5432), `redis` (`redis:8.2`, 6379).
- Env (`.env.template`): `DB_CONNECTION_URI`, `CACHE_URL`, `LLM_OPENAI_API_KEY`
  (or OpenAI-compatible local), `AUTH_USE_AUTH`, `VECTOR_STORE_TYPE`.
- hermes integration is via the **API base URL** (`hermes honcho setup`), NOT the
  Honcho MCP (that's a separate CF Worker we can skip).
- AGPL-3.0 — note for the homelab.

### Browser / CDP server (NEW — shared by both)
- Neither harness ships a browser (chromium MISSING, playwright cache empty).
- Run a headless Chromium exposing a **CDP websocket**: `browserless/chromium`
  (or `npx playwright run-server`). Expose CDP endpoint on the bridge network.
- **openclaw** connects via its browser extension's CDP path (`browser-cdp.js`,
  `parseBrowserHttpUrl`, remote-debugging) — set the remote/CDP endpoint in browser
  config (exact key = VERIFY, task #54).
- **hermes** registers a local browser provider with `cdp_url` (the
  `agent/browser_provider.py` abstraction; overrides the cloud Browserbase default).
- Same CDP URL for both = fair, self-hosted, private (no cloud Browserbase).

## Port map (avoid conflicts)
| Service | Port(s) | Notes |
|---|---|---|
| recall-mcp | 8407 | exists |
| recall-neo4j | 7688 / 7475 | exists |
| Hindsight | 8888 (API+MCP) / 9999 (UI) | new |
| Honcho api | 8000 | new |
| Honcho pg / redis | 5432 / 6379 | keep INTERNAL (don't publish; recall uses neo4j not pg, but avoid clashing w/ other wiley pg) |
| Browser CDP | e.g. 3000 / 9222 | new; pick free |
- Honcho and Hindsight each want their own pgvector → **separate Postgres** (don't share).

## Privacy posture (homelab requirement)
All memory-derivation LLM calls must use **no-train** routes: OpenRouter
`data_collection: deny` OR local wiley inference (llama-cpp / TEI). No cloud
Browserbase (use local CDP). No `app.honcho.dev`/`hindsight cloud` (self-host).

## Deployment note (the "one stack" ask)
recall already runs in its own working compose. Two options:
1. **New compose for the new services** (Hindsight + Honcho + browser) joining
   `pinkleberry_bridge`, adjacent to recall. Safest — doesn't touch the working recall.
2. **Single unified compose** folding recall in. Cleaner conceptually but risks the
   live recall deploy.
Recommend option 1 first; consider folding recall in later. Location: a new dir on
wiley, e.g. `~/Docker/agent-eval-infra/`. Source-of-truth compose drafted in this
repo under `infra/` (to be written), deployed to wiley with operator approval.

## Open items
- [ ] Draft the compose file(s) (Hindsight + Honcho + browser) — source in repo `infra/`.
- [ ] Decide Hindsight LLM provider (local llama-cpp vs OpenRouter-deny) + image (full vs slim).
- [ ] Honcho LLM provider (same decision).
- [ ] Secrets via Infisical (HONCHO/HINDSIGHT keys) — wiley-homelab identity gap (same as recall).
- [ ] Per-agent group/bank provisioning (eval-openclaw / eval-hermes) — isolated from prod.
- [ ] CDP wiring keys per harness (task #54).
- [ ] Backups for new volumes (recall has none today either — known gap).

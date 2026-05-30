# Eval memory stack — wiley deployment (SHIPPED 2026-05-29)

**Status:** memory portion shipped + reachable from LAN. Browser/CDP is
explicitly out of scope here (task #54). Canonical compose file lives on wiley
at `~/Docker/recall/docker-compose.yml`; mirror in this repo at
`infra/recall-memory-stack.docker-compose.yml`.

**Decision rationale (operator-chosen 2026-05-29):**
- **Add into the existing recall compose, don't relocate** — recall (juliet/yui
  prod memory) stays exactly as-is; new services are appended.
- **bge-m3 everywhere** (1024-dim, 8192-token) for new memory services; recall
  stays on bge-small until a separate re-embed migration (task #57).
- **Memory-derivation LLM = OpenRouter `deepseek/deepseek-v4-flash`**; no-train
  guarantee enforced at the OpenRouter **account** level (these are plain
  OpenAI-style clients that can't send the per-request `data_collection: deny`
  body param the openclaw/hermes adapters use).

## Topology

All on the shared external `pinkleberry_bridge` docker network. Eval agents on
landon reach them over the LAN via published wiley host ports.

```
                              wiley host
   ┌─────────────────────────────────────────────────────────────────┐
   │  pinkleberry_bridge                                             │
   │                                                                 │
   │  recall stack (pre-existing)         eval memory (added 5/29)   │
   │  ────────────────────────────        ────────────────────────   │
   │  recall-neo4j  :7688/:7475           mem-embed                  │
   │  recall-embed  (bge-small 384)         (bge-m3, 1024-dim)       │
   │  recall-mcp    :8407 ──┐               OpenAI-compat at /v1     │
   │                        │             hindsight-db (pgvector18)  │
   │                        │             hindsight       :8888/9999 │
   │                        │             honcho-postgres (pgvector15│
   │                        │             honcho-redis                │
   │                        │             honcho-api      :8000      │
   │                        │             honcho-deriver  (worker)   │
   └────────────────────────┼─────────────────────────────────────────┘
                            │
        eval-openclaw / eval-hermes group-id (X-Group-ID header)
        sent by harness MCP clients → recall isolation
```

## Per-service configuration

### `mem-embed` — shared bge-m3 embedder
- Image `ghcr.io/huggingface/text-embeddings-inference:cpu-1.9`,
  `--model-id BAAI/bge-m3 --auto-truncate`.
- Serves both OpenAI-compatible `/v1/embeddings` (used by honcho via the
  `LLM` provider transport) AND TEI-native `/embed` (used by hindsight via
  `HINDSIGHT_API_EMBEDDINGS_PROVIDER=tei`).
- **No healthcheck.** The TEI image has no `wget` / `curl` / `nc` and a
  near-distroless base — a CMD-SHELL HTTP probe can't run. Dependents use
  `condition: service_started`. The model caches in
  `/mnt/crumbleton/docker/mem-embed/cache` (volume), so restarts after first
  load are fast.

### `hindsight` — vectorize-io learning memory MCP
- Image `ghcr.io/vectorize-io/hindsight:latest`.
- External pgvector DB (`hindsight-db`, pgvector pg18); per-bank isolation via
  URL path `/mcp/<bank>/` (`eval-openclaw`, `eval-hermes`).
- LLM via `HINDSIGHT_API_LLM_*` pointed at OpenRouter (deepseek-v4-flash).
- Embeddings external via `HINDSIGHT_API_EMBEDDINGS_PROVIDER=tei` +
  `_TEI_URL=http://mem-embed:80` + `_TEI_MODEL=BAAI/bge-m3`.
- Reverse-proxied port `8888` (API + MCP) and `9999` (UI).

### `honcho` — plastic-labs ambient user model (BUILT FROM SOURCE)
- No prebuilt image; we clone `https://github.com/plastic-labs/honcho` to
  `~/Docker/recall/honcho-src/` on wiley and let the compose build from it.
- Services: `honcho-postgres` (pgvector pg15), `honcho-redis`,
  `honcho-api` (FastAPI, port `8000`), `honcho-deriver` (background worker).
- Memory-derivation LLM (per-module — DERIVER, SUMMARY, DIALECTIC_LEVELS,
  DREAM_DEDUCTION, DREAM_INDUCTION) → OpenRouter deepseek-v4-flash via
  `*_MODEL_CONFIG__TRANSPORT=openai` +
  `*_MODEL_CONFIG__OVERRIDES__BASE_URL=https://openrouter.ai/api/v1`.
- Embeddings → `mem-embed` via `EMBEDDING_MODEL_CONFIG__TRANSPORT=openai` +
  `_OVERRIDES__BASE_URL=http://mem-embed/v1` +
  `EMBEDDING_VECTOR_DIMENSIONS=1024` + `EMBEDDING_MAX_INPUT_TOKENS=512`.
- `AUTH_USE_AUTH=false` — single-tenant homelab deploy. No API key required;
  hermes config (`$HERMES_HOME/honcho.json`) only sets `baseUrl`.

### `recall` — pre-existing Graphiti MCP (UNCHANGED CONTENTS, ONE TRANSPORT FIX)
- Compose stanza copied verbatim from the pre-existing
  `~/Docker/recall/docker-compose.yml`.
- One change to the recall **server wrapper** (`~/Docker/recall/wrapper_main.py`)
  on wiley: widened `TransportSecuritySettings.allowed_hosts` to include
  `internal-host:*`, `internal-host:*`, `recall-mcp:*` (alongside the
  defaults `127.0.0.1:*`, `localhost:*`, `[::1]:*`). DNS-rebind protection
  stays ON; we just permit the trusted LAN host.

  Why: openclaw's HTTP client (undici) derives `Host` from URL authority and
  ignores a custom `headers.Host`; the previous trick of overriding
  `Host: localhost:8407` worked for hermes (httpx) but not openclaw, so openclaw
  got `Invalid Host header` from recall's DNS-rebind guard. Server-side allowlist
  is the universal fix. **Operator-approved 2026-05-29.** FOOTGUNS #18.

## Deploy reproducer

These steps assume a fresh recall stack with the original 3 services running.

```bash
# 1. Back up the live compose on wiley
ssh wiley@internal-host 'cp ~/Docker/recall/docker-compose.yml \
                              ~/Docker/recall/docker-compose.yml.bak-pre-memory-stack-$(date +%Y%m%d)'

# 2. Generate the two new DB passwords (never echoed; values stay only in .env)
ssh wiley@internal-host 'cd ~/Docker/recall
  grep -q "^HINDSIGHT_DB_PASSWORD=" .env || \
    printf "HINDSIGHT_DB_PASSWORD=%s\n" "$(openssl rand -hex 24)" >> .env
  grep -q "^HONCHO_DB_PASSWORD=" .env || \
    printf "HONCHO_DB_PASSWORD=%s\n" "$(openssl rand -hex 24)" >> .env'

# 3. Volume dirs + honcho source
ssh wiley@internal-host 'mkdir -p \
  /mnt/crumbleton/docker/mem-embed/cache \
  /mnt/crumbleton/docker/hindsight/pgdata \
  /mnt/crumbleton/docker/honcho/pgdata \
  /mnt/crumbleton/docker/honcho/redis
  cd ~/Docker/recall
  [ -d honcho-src/.git ] || git clone --depth 1 https://github.com/plastic-labs/honcho honcho-src'

# 4. Push the new compose
scp infra/recall-memory-stack.docker-compose.yml \
    wiley@internal-host:~/Docker/recall/docker-compose.yml

# 5. Bring up the NEW services only (recall is untouched by `up -d <named>`)
ssh wiley@internal-host 'cd ~/Docker/recall && \
  docker compose up -d mem-embed hindsight-db honcho-postgres honcho-redis && \
  docker compose build honcho-api'

# 6. Honcho schema is created at dim 1536 by default; reconfigure to 1024
ssh wiley@internal-host 'cd ~/Docker/recall && \
  docker compose run --rm --no-deps \
    --entrypoint "/app/.venv/bin/python scripts/configure_embeddings.py --yes" honcho-api'

# 7. Bring up hindsight + honcho
ssh wiley@internal-host 'cd ~/Docker/recall && \
  docker compose up -d hindsight honcho-api honcho-deriver'
```

Apply the recall wrapper allowlist fix once (separate change on wiley); after
that, all three memory services are reachable from landon over the LAN.

## Health checks

```bash
curl -s -o /dev/null -w "recall    %{http_code}\n" http://internal-host:8407/health
curl -s -o /dev/null -w "hindsight %{http_code}\n" http://internal-host:8888/health
curl -s -o /dev/null -w "honcho    %{http_code}\n" http://internal-host:8000/health
# All should return 200.
```

Or just open `agent-status.html` (generated by `tools/agent_status.py`) — the
"Memory services (wiley)" legend at the bottom pings these endpoints and shows
green/red dots.

## Gotchas captured during deploy (already in FOOTGUNS.md, recap)

| # | Trap |
|---|---|
| 18 | undici ignores `headers.Host`; recall DNS-rebind 400s. Fix: server-side allowlist. |
| — | TEI image has no wget/curl — healthcheck can't run; use `service_started` for dependents. |
| — | postgres:18 keeps data under `/var/lib/postgresql/18/docker` (not `/var/lib/postgresql/data`); pgvector pg18 inherits this. |
| — | Honcho's `EMBEDDING_VECTOR_DIMENSIONS=1024` env is a **validator**, not a creator. The fresh DB still gets dim 1536 from initial migrations. Run `configure_embeddings.py --yes` to ALTER the columns. |
| — | OpenRouter's no-train guarantee for plain-OpenAI clients (hindsight/honcho) comes from the **account-level** privacy setting — they can't send the body-param. |

## Open follow-ups

- `#54` Browser/CDP server — separate spec, not folded in here.
- `#57` Migrate recall to bge-m3 (re-embeds prod juliet/yui graph; requires
  backup + custom re-embed script since Graphiti has no in-place tool).

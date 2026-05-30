# `infra/` — homelab infrastructure mirrors

Source-of-truth mirrors of infrastructure files that live elsewhere (typically
on wiley). The canonical file is on the host; the copy here is for version
tracking + review + rebuild reproducibility. **Do not deploy directly from
this dir** — deploy by `scp`-ing to the canonical location and operating
there.

## Files

| File | Mirror of | Spec |
|---|---|---|
| `recall-memory-stack.docker-compose.yml` | `wiley:~/Docker/recall/docker-compose.yml` | [`backlog/done/2026-05-29-memory-stack-deployment.md`](../backlog/done/2026-05-29-memory-stack-deployment.md) |

## What lives in the recall-memory-stack compose

Three memory products on the shared `pinkleberry_bridge` network:

| Service | Role | Ports (LAN) |
|---|---|---|
| `recall-neo4j` / `recall-embed` / `recall-mcp` | pre-existing Graphiti temporal-KG MCP (juliet/yui prod + eval-* groups) | recall-mcp `8407` |
| `mem-embed` | shared bge-m3 embedder (1024-dim, 8192-token) — serves honcho + hindsight | bridge-internal only |
| `hindsight-db` + `hindsight` | vectorize-io learning-memory MCP, per-bank isolation | `8888` MCP + API, `9999` UI |
| `honcho-postgres` + `honcho-redis` + `honcho-api` + `honcho-deriver` | plastic-labs ambient memory (built from source) | `8000` API |

See the spec for: deploy reproducer, the dim-1024 reconfigure step, the recall
DNS-rebind allowlist fix, and known gotchas (TEI healthcheck, postgres:18
PGDATA path, OpenRouter no-train at account level).

## Re-syncing after edits

```bash
# Edit the mirror locally, then push to wiley:
scp infra/recall-memory-stack.docker-compose.yml \
    wiley@wiley-pinkleberry:~/Docker/recall/docker-compose.yml
ssh wiley@wiley-pinkleberry 'cd ~/Docker/recall && docker compose config --services'  # validate
# Bring up only the changed/new services (recall stays running):
ssh wiley@wiley-pinkleberry 'cd ~/Docker/recall && docker compose up -d <name1> <name2>'
```

If you change a service definition that already exists, `up -d` will recreate
that container — be aware of the implications (recall in particular runs
prod juliet/yui memory).

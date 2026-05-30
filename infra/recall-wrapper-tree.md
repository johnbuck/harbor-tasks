# recall wrapper layout (P1 shipped 2026-05-29)

The recall MCP container extends `zepai/knowledge-graph-mcp:1.0.2` with a
wrapper package that intercepts the FastMCP server before it accepts
requests. Spec: [`backlog/2026-05-29-recall-hindsight-style-plugin.md`](../backlog/2026-05-29-recall-hindsight-style-plugin.md).

## Layout on wiley (canonical) — `~/Docker/recall/`

```
.
├── Dockerfile                                      # extends zepai/knowledge-graph-mcp:1.0.2
├── docker-compose.yml                              # recall-mcp (prod) + recall-mcp-eval (canary)
├── config.yaml                                     # prod entity ontology
├── config.eval.yaml                                # eval entity ontology (Bug/TestCase/API/...)
├── wrapper_main.py                                 # → baked at /app/mcp/main.py (entrypoint)
└── wrapper/
    ├── __init__.py                                 # package marker
    └── descriptions.py                             # P1: coaching descriptions + apply(mcp)
                                                    # (P2+: reflect.py, bank_config.py,
                                                    #       directive.py, mental_model.py)
```

## Baked into the image

```
/app/mcp/
├── main.py                                         # entrypoint (formerly wrapper_main.py)
├── wrapper/
│   ├── __init__.py
│   └── descriptions.py
└── src/
    └── graphiti_mcp_server.py                      # upstream Graphiti MCP (untouched)
```

The entrypoint adds `/app/mcp` to `sys.path` (so `from wrapper import …`
resolves) then `/app/mcp/src` (so the upstream `import graphiti_mcp_server`
keeps working).

## Boot sequence (`main.py`)

1. `from wrapper import descriptions`
2. `import graphiti_mcp_server as server` — fires `@mcp.tool()` decorators
   that register the 9 existing tools into `server.mcp._tool_manager._tools`.
3. `await server.initialize_server()` — config load, Neo4j connect,
   embedder + LLM client warm-up, schema upgrade.
4. Install `_GraphitiProxy` so `server.config.graphiti.group_id` reads the
   `request_group_id` contextvar (per-HTTP-request override via
   `X-Group-ID` header).
5. **`descriptions.apply(server.mcp)`** — walk the tool registry, rewrite
   `.description` from `DEFAULT_DESCRIPTIONS` or `RECALL_DESC_<TOOL>` env
   override. Idempotent. Raises on FastMCP private-API drift (see
   [FOOTGUNS #21](../backlog/FOOTGUNS.md)).
6. Configure `TransportSecuritySettings` with LAN-host allowlist.
7. Wrap `streamable_http_app()` with `GroupIDMiddleware` and serve.

## Image tags

| Tag | Points at | Use |
|---|---|---|
| `recall-mcp:pre-hindsight-parity` | the build before P1 | rollback target; prod recall-mcp is pinned here |
| `recall-mcp:p1` | the P1 build (coaching descriptions) | eval canary `recall-mcp-eval` |
| `recall-mcp:local` | currently follows the most recent build | informal alias; **do not** rely on for compose pinning |

Compose pins:
- `recall-mcp` (prod) → `recall-mcp:p4` (promoted 2026-05-30; latest revision tag `:p4-r2` includes all deferred review fixes — R-01 BankConfig LRU cache, R-02 retain_mission snapshot-at-enqueue via QueueService patch, R-04+R-08 force/freshness flags on refresh_mental_model, R-06 async ntfy, R-10 driver close, R-12 mission validation, R-14 louder delete description, R-16 retry timer, R-17 Dockerfile reorder, R-19 02:00 cron schedule, R-20 directive-override probe). Phase ladder: P1 desc → P2 reflect → P3 bank_config+directive+retain_mission → P4 mental_model+refresher cron.
- `recall-mcp-eval` (canary) → `recall-mcp:p4` (bumps with each phase)
- Rollback targets: `recall-mcp:pre-hindsight-parity` (full revert), `recall-mcp:p1`, `recall-mcp:p2`, `recall-mcp:p3`, `recall-mcp:p4` (pre-R-fixes), `recall-mcp:p4-r2` (post-R-fixes)

systemd timers on wiley:
- `recall-refresh-mental-models.timer` — daily 02:00 ±3 min (R-19)
- `recall-refresh-mental-models-retry.timer` — hourly, ExecCondition checks
  the `/app/mcp/.mm-retry-needed` marker file inside `recall-mcp`; no-ops
  unless the marker exists (R-16 cascade-recovery path)
- `recall-build-communities.timer` — daily 03:30 (pre-existing)

Regression probes (runnable any time against eval canary):
- `~/scripts/recall-test-directive-override.sh` — verifies high-priority directives
  override warm-empathy disposition in reflect output (R-20)

## Kill switches (env vars read at boot)

| Env var | Default | Effect when off |
|---|---|---|
| `RECALL_DESCRIPTIONS_ENABLED` | `true` | apply() returns 0 without mutating; upstream descriptions ship |
| `RECALL_DESC_<TOOL_NAME_UPPER>` | unset → default | per-tool override of the coaching description string |
| `RECALL_REFLECT_ENABLED` | `false` (slot) | P2: skip reflect tool registration entirely |
| `RECALL_BANK_CONFIG_ENABLED` | `false` (slot) | P3: skip BankConfig schema + tools |
| `RECALL_DIRECTIVE_ENABLED` | `false` (slot) | P3: skip Directive schema + tools |
| `RECALL_MENTAL_MODEL_ENABLED` | `false` (slot) | P4: skip MentalModel schema + tools |
| `RECALL_MM_REFRESH_TIMER_ENABLED` | `false` (slot) | P4: systemd ExecCondition for the refresh service |

P2–P4 read the slots at boot; if false, the corresponding `register(mcp,
...)` call is skipped. Operator can disable a misbehaving phase by setting
the flag to `false` on the affected container and `docker compose up -d`
— no rebuild required.

## Revert reproducer

```bash
# Roll the eval canary back to pre-P1:
ssh wiley@wiley-pinkleberry 'cd ~/Docker/recall && \
  sed -i "s|image: recall-mcp:p1|image: recall-mcp:pre-hindsight-parity|" docker-compose.yml && \
  docker compose up -d recall-mcp-eval'
```

For prod (currently pinned to `:pre-hindsight-parity` already): no action
needed unless a hot promotion happened.

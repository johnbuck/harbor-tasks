---
name: recall-bge-m3-and-eval-ontology
title: Recall — bge-m3 embedder + deepseek-v4-flash extractor + community-build cron + eval-domain ontology
date: 2026-05-29
status: IMPLEMENTED 2026-05-29
origin: ad-hoc evaluation 2026-05-29 — operator audited recall against hindsight; identified four real gaps separate from the agent-experience parity work
---

# Recall — bge-m3 embedder + deepseek-v4-flash + community detection + eval ontology

## Problem

A capabilities audit of recall (vs. the just-deployed hindsight + honcho)
surfaced four gaps that aren't about the *agent-facing surface* (the
hindsight-parity spec covers that separately) but about the *retrieval and
extraction backbone*:

1. **Embedder asymmetry.** recall used `bge-small-en-v1.5` (384-dim, 512-token
   window) via a dedicated `recall-embed` container. hindsight and honcho —
   the freshly deployed stack — both use `bge-m3` (1024-dim, 8192-token) via
   the shared `mem-embed` container. For an eval that pits the three memory
   stores against each other, recall is searching with a measurably weaker
   embedder. Every fact written today is on bge-small; comparisons against
   hindsight are confounded by the embedding gap.
2. **LLM extraction asymmetry.** recall used OpenRouter `z-ai/glm-4.6` for
   entity/relationship extraction (swapped 2026-04-30 from Z.ai direct after
   rate-limit saturation). hindsight uses `deepseek/deepseek-v4-flash`. For
   the eval, "which memory store is better" is conflated with "which
   extraction model is better."
3. **Community detection schema present, never built.** Graphiti's `:Community`
   label and `community_name` fulltext index are in the schema, but no
   scheduler invokes `graphiti.build_communities()`. `search_nodes` will
   never surface higher-order topical clusters until something does.
4. **Single agent-memory ontology for prod AND eval.** `config.yaml` defines
   nine entity types tuned for personal-assistant memory:
   `Preference`, `Requirement`, `Procedure`, `Location`, `Event`,
   `Organization`, `Document`, `Topic`, `Object`. For the harbor-tasks coding
   eval (fix-bug, aider_polyglot, ds1000, swtbench, bfcl, simpleqa), the
   right ontology is `Bug`, `TestCase`, `API`, `Dependency`, `File`,
   `Concept`, `Constraint`, `Source`. Graphiti's config is process-global;
   one container can't have two ontologies.

(A fifth gap — backups for `:BankConfig`/`:Directive`/`:MentalModel` — was
flagged but resolved as "covered by existing restic-docker-backup
of `/mnt/crumbleton/docker/`" without code changes.)

## Scope

**In** — operator-authorized to fix all four:

1. **bge-m3 in-place re-embed of prod graph.** Walk all `:Entity.name_embedding`
   and `:RELATES_TO.fact_embedding` properties, recompute vectors via
   `mem-embed` (TEI / bge-m3 / 1024-dim), write back. `recall-embed` container
   retired-but-not-removed.
2. **LLM swap to `deepseek/deepseek-v4-flash`.** Same OpenRouter route, same
   account-level `data_collection:deny` (no privacy regression).
3. **Community-build systemd timer.** Daily 03:30, calls `graphiti.build_communities()`
   for the active prod groups `[juliet, yui, akane]`. First-run on the
   current graph found 0 communities (sparse, valid result); will fill as
   the graph grows.
4. **Parallel `recall-mcp-eval` container with eval ontology.** Same image,
   same Neo4j, same `mem-embed`. Listens on port `8408`. Reads
   `config.eval.yaml` with the coding-eval entity types. Eval agents
   (`eval-openclaw`, `eval-hermes` groups) repointed to `:8408`; prod groups
   stay on `:8407` with the agent-memory ontology.

**Out** — explicitly deferred:

- **Migrating eval-group data.** Operator's instruction was *"Eval memories
  can be completely removed; we don't need them."* — there was nothing to
  migrate; `eval-openclaw` / `eval-hermes` groups were empty.
- **Per-group entity-type override inside a single container.** Would require
  forking Graphiti's per-process config; complicated, low value when a
  second container is one compose stanza away.
- **Backfilling community summaries.** First run produces 0; communities
  form as the graph grows. No forced seeding.
- **`recall-embed` container removal.** Left running but unused, to keep
  rollback simple. Operator-approved cleanup whenever convenient.

## Design decisions

### D1 — In-place vector refresh (not a parallel-stack migration)

The recall graph is **tiny** at audit time (~860 nodes across `juliet`,
`yui`, `akane`, `smoke-openrouter` groups, with 1,078 RELATES_TO edges).
At TEI bge-m3 CPU throughput (~20-30 rows/s) the entire re-embed runs in
~135 seconds. The complexity of a parallel-stack migration (new MCP
container, dual-write, cutover) is not worth ~2 minutes of downtime.

Process:
1. Stop `recall-mcp`.
2. Run `reembed.py` inside `recall-mcp` container (it has neo4j-driver and
   requests pre-installed); script reads `n.name` / `r.fact`, posts to
   `http://mem-embed/embed` in batches of 32, writes back via
   `UNWIND $pairs ... SET x.<embed_prop> = p.vec`. Idempotent (skips rows
   already at target dim).
3. Update `config.yaml`: `embedder.model=BAAI/bge-m3`,
   `embedder.dimensions=1024`, `embedder.providers.openai.api_url=http://mem-embed:80/v1`.
4. Start `recall-mcp`. Graphiti auto-creates any indexes at the new dim on boot.

### D2 — `smoke-openrouter` group cleanup

Audit found a leftover group `smoke-openrouter` (10 entities, 1 episode, 17
edges) from the 2026-04-30 LLM-swap smoke test. Cleared via
`MATCH (n {group_id:"smoke-openrouter"}) DETACH DELETE n` after operator
confirmation. No production impact; the swap event is documented in
`pinkleberry/tenants/thringle/docs/research/session-2026-05-01-recall-openrouter-swap.md`.

### D3 — Community-build cron lives on wiley as a systemd `--user` timer

Mirror of the existing `magellan-*` cron pattern on wiley:

- `/home/wiley/scripts/recall-build-communities.sh` — shell wrapper, `docker exec`s the python script into `recall-mcp`.
- `/home/wiley/scripts/recall-build-communities.py` — instantiates
  `GraphitiService` via the upstream `graphiti_mcp_server` config and calls
  `graphiti.build_communities(group_ids=[juliet, yui, akane])`.
- `~/.config/systemd/user/recall-build-communities.{service,timer}` — daily
  03:30, `RandomizedDelaySec=300`, ntfy on failure via `ExecStopPost`.

### D4 — Parallel `recall-mcp-eval` container with shared Neo4j

A second instance of the same `recall-mcp:local` image on port `:8408`,
reading `config.eval.yaml` (eval entity types) instead of `config.yaml`.
Shares the prod `recall-neo4j` — data isolation is by `group_id`, not by
DB. Eval entity extraction at write time uses the coding-eval ontology;
prod extraction uses the agent-memory ontology. Same `mem-embed`, same
LLM, same wrapper.

### D5 — Eval harness repointing

`/home/trumble/harbor-tasks/harnesses/openclaw/openclaw.json` and
`harnesses/hermes/config.yaml` — `recall.url` `:8407` → `:8408`. Rich-image
rebuilt. `hermes mcp test recall` → `✓ Connected (134ms), 9 tools` confirms
the new endpoint is reachable from the baked configs.

## Acceptance criteria — all PASSED

- [x] All 746 `:Entity.name_embedding` and 1,078 `:RELATES_TO.fact_embedding`
      properties verified at `size=1024` post-migration (`MATCH ... RETURN
      size(...)` in Neo4j Browser).
- [x] `recall-mcp` boot log shows `Using LLM provider: openai / deepseek/deepseek-v4-flash`
      and `Using Embedder provider: openai` (the openai-compatible TEI endpoint).
- [x] `search_memory_facts(query="openrouter")` against `juliet` group returns
      ranked facts on the new bge-m3 path; LLM extraction reaches deepseek-v4-flash.
- [x] `systemctl --user list-timers recall-build-communities.timer` shows next
      fire at next 03:30. Manual `systemctl --user start
      recall-build-communities.service` completes successfully.
- [x] `recall-mcp-eval` container healthy on `:8408`, boot log shows
      `Using custom entity types: Bug, TestCase, API, Dependency, File, Concept, Constraint, Source`.
- [x] Eval harness `hermes mcp test recall` → connects to `:8408` (verifies
      the openclaw.json + hermes config.yaml edits propagated through rich image rebuild).
- [x] `smoke-openrouter` group dropped (`MATCH (n) WHERE n.group_id=...
      RETURN count(n) → 0`).

## Files changed on wiley (canonical)

- `~/Docker/recall/config.yaml` — LLM model + embedder swap (backup: `*.bak-pre-bge-m3-20260529`)
- `~/Docker/recall/docker-compose.yml` — added `recall-mcp-eval` service (backup `*.bak-pre-bge-m3-20260529`)
- `~/Docker/recall/config.eval.yaml` — new, coding-eval entity types
- `~/scripts/recall-build-communities.{sh,py}` — new
- `~/.config/systemd/user/recall-build-communities.{service,timer}` — new, enabled

## Files changed in `harbor-tasks` repo

- `harnesses/openclaw/openclaw.json` — recall URL `:8407` → `:8408`
- `harnesses/hermes/config.yaml` — recall URL `:8407` → `:8408`
- `infra/recall-memory-stack.docker-compose.yml` — mirror
- `infra/recall-config.eval.yaml` — new mirror

## What this spec enables downstream

The recall hindsight-style-plugin work (separate spec, same date) was
gated on the LLM and embedder being on `deepseek-v4-flash` and `bge-m3`
respectively — without those, the `reflect` tool would call a different
LLM than the extraction path uses, and search quality would degrade against
hindsight in any head-to-head. This spec is the precondition that work
assumed in its D2 and D7 sections.

## Followups recorded elsewhere

- Recall hindsight-style-plugin: [`2026-05-29-recall-hindsight-style-plugin.md`](2026-05-29-recall-hindsight-style-plugin.md)
- bge-m3 migration backup-task: closed (task #57)
- Community-build cron: closed (task #58)
- recall-mcp-eval ontology container: closed (task #59)
- `recall-embed` container cleanup: deferred indefinitely, low priority

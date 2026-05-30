---
name: recall-hindsight-style-plugin
title: Recall — hindsight-style tool surface (coaching descriptions, reflect, dispositions, mental models)
date: 2026-05-29
status: IMPLEMENTED 2026-05-30 (P1+P2+P3+P4 shipped to both eval canary + prod; D9 #1 resolved as outcome 1: clean public hook at graphiti_core/utils/maintenance/node_operations.py:69 wired through Graphiti.add_episode(custom_extraction_instructions=...))
origin: ad-hoc evaluation 2026-05-29 — operator asked "should we write a plugin for recall that behaves like hindsight"; deep-dive into `/app/api/hindsight_api/mcp_tools.py` + `config.py` revealed the actual delta
---

# Recall — hindsight-style tool surface

## Problem

Recall and hindsight are both FastMCP servers exposing memory tools to the
same eval agents (openclaw, hermes). On the wire they look the same;
**in practice the agents use hindsight proactively and barely touch recall**,
because the tool descriptions present them differently:

| Tool | What the agent sees |
|---|---|
| hindsight `retain` | *"Store important information to long-term memory. **Use this tool PROACTIVELY** whenever the user shares: Personal facts, preferences, or interests, Important events or milestones, ..."* |
| recall `add_memory` | *"Add an episode to memory. This is the primary way to add information to the graph. This function returns immediately and processes the episode addition in the background. Episodes for the same group_id are processed sequentially to avoid race conditions. Args: name (str): Name of the episode ..."* |

Hindsight's prompt tells the LLM **when** to use the tool. Recall's tells it
**how**. The model optimizes against the prompt it sees, so behavior diverges
even though both stacks are LLM-backed temporal stores.

Beyond descriptions, hindsight ships three higher-order capabilities recall
lacks entirely:

1. **`reflect`** — *"Generate thoughtful analysis by synthesizing stored
   memories with the bank's personality."* Search + LLM synthesis in one call.
2. **Bank dispositions** — per-bank skepticism/literalism/empathy dials
   (1–5 each) that bias `reflect` output, plus a `mission` string steering
   extraction.
3. **Mental models** — pinned reflections (a name + a `source_query`) whose
   `content` is auto-refreshed by an async job. They survive sessions as
   living documents.

For the harbor-tasks eval, this asymmetry creates a confound:
"hindsight is better" vs "hindsight's tools are described better" are
indistinguishable until recall has parity at the agent-facing surface.

## Scope

**In** — additive changes to the recall MCP wrapper that bring it to
agent-experience parity with hindsight:

1. **Coaching-style tool descriptions** for all 9 existing recall tools,
   externalized as env-var-overridable defaults (the hindsight pattern).
2. **`reflect` tool** — search + LLM synthesis, biased by bank disposition.
3. **`:BankConfig` schema + tools** (`get_bank_config`, `update_bank_config`)
   — dispositions, mission, retain_mission, entity-type filter defaults.
3b. **`:Directive` schema + tools** (`list_directives`, `create_directive`,
   `delete_directive`) — per-bank free-text behavior rules, stacked with
   dispositions in `reflect`'s prompt. The pairing matches hindsight: numeric
   dials + free-text rules.
4. **`:MentalModel` schema + tools** (`list/get/create/update/refresh/
   delete/clear_mental_model`) plus a refresher cron.

**Out** — features I evaluated and rejected:

- **Per-bank `mcp_enabled_tools` allowlist**. Recall has 9 tools, not
  hindsight's 27 — not enough noise to filter. Easy to add later.
- **Strategies** (e.g., hindsight's `'exact'` for verbatim retain). Graphiti's
  whole point is entity extraction; an "exact" mode fights the model.
- **`:Document` containers**. Graphiti's `:Episodic` already serves this.
- **Webhooks** (hindsight's `consolidation.completed` event stream).
  Speculative; defer until something needs it.
- **Two-level MCP audit logging hook** (hindsight's `_apply_audit_logging`).
  Nice to have, but the existing graphiti_mcp_server logging is sufficient
  for the eval; revisit if observability gaps surface.

(Note: directives were originally listed here as "deferred unless dispositions
prove too coarse." After review with the operator, they're moved IN — see
Item 3b above. Hindsight pairs numeric dials with free-text rules; recall
parity needs both or neither.)

## Design decisions

### D1 — Server-side, both containers

All changes go in `wrapper_main.py` (and its new sibling modules; see D5).
The same image runs as both `recall-mcp` (prod groups: juliet, yui, akane)
and `recall-mcp-eval` (eval groups: eval-openclaw, eval-hermes), so both
pick up the new surface automatically. Per-container customization via
env-var description overrides (D6).

**Not** an openclaw plugin or hermes plugin — those would introduce
harness-side asymmetry that breaks eval fairness (hermes-only feature ≠
openclaw-only feature).

### D2 — Reuse Graphiti's existing async + LLM stack

`reflect` calls `graphiti_client.search(query, group_ids=[gid],
num_results=max_facts)` (Graphiti's existing hybrid search — fulltext +
vector + edge expansion), then sends results to the same LLM provider
already configured for entity extraction (currently `deepseek-v4-flash`
via OpenRouter, with account-level `data_collection:deny`). No new
provider plumbing; no new privacy surface.

**Zero-fact short-circuit.** When `search` returns 0 facts, `reflect`
returns a deterministic `{"answer": "No relevant facts available in this
memory bank.", "based_on": [], "facts_considered": 0}` **without calling
the LLM**. Skipping the LLM avoids the high-empathy-+-encouraging-directive
hallucination mode the reviewer flagged.

**Error handling.** Per call: try/except with bounded exponential backoff
on OpenRouter 429 (max 2 retries, 5 s and 30 s). On any other LLM error
(timeout, malformed response, non-200), return `{"status": "error",
"answer": null, "based_on": [], "error": "<one-line summary>"}` — the
caller's `content` field is **never** set to a raw error string. Cascade
guard: if 5 consecutive `reflect` calls within 60 s hit 429, stop new
calls for 5 minutes and ntfy `recall reflect 429-cascade — backing off`.

**Token budget.** Hard pre-flight check before LLM call:
`mission_tokens + disposition_block_tokens + directive_block_tokens +
facts_tokens + question_tokens + max_tokens_for_response ≤ model_context_window`
(treat deepseek-v4-flash context as 128 k for arithmetic, leave a 4 k margin).
If oversized, trim `facts_tokens` first (drop lowest-ranked facts), log
`reflect: trimmed N facts to fit context`, and proceed. Never trim
dispositions or directives — those are operator intent.

The synthesis prompt is bank-disposition-aware:

```
You are a memory companion with the following disposition:
- Skepticism: {1-5}  (1 = take memories at face value; 5 = aggressively question)
- Literalism: {1-5}  (1 = abstract/conceptual; 5 = strictly literal)
- Empathy: {1-5}     (1 = analytical detachment; 5 = emotional resonance)

Mission: {bank_config.mission or "Help the user think with their memory"}

Facts retrieved from the user's memory graph:
{facts}

Based ONLY on those facts, answer the question. If the facts are insufficient,
say so explicitly — do not invent. Output ≤{max_tokens} tokens.

Question: {query}
```

### D3 — `:BankConfig` (one per group) + `:Directive` (zero-to-many per group)

The two together form recall's "bank personality" layer, matching hindsight.
`:BankConfig` holds the numeric + global-string knobs; `:Directive` holds
the stackable, prioritized free-text rules.

#### D3a — `:BankConfig`

```cypher
(:BankConfig {
  group_id:                 STRING (unique),
  disposition_skepticism:   INT 1-5  (default 3),
  disposition_literalism:   INT 1-5  (default 3),
  disposition_empathy:      INT 1-5  (default 3),
  mission:                  STRING   (default ""),  // steers reflect's system prompt
  retain_mission:           STRING   (default ""),  // steers add_memory's extraction
  recall_max_facts:         INT      (default 25),  // default reflect/search size
  entity_types_filter:      LIST<STRING> (default []),  // default search entity_types arg
  created_at:               DATETIME,
  updated_at:               DATETIME
})
CREATE CONSTRAINT bank_config_group_id IF NOT EXISTS
  FOR (b:BankConfig) REQUIRE b.group_id IS UNIQUE;
```

Auto-created on first `get_bank_config` or `reflect` call for a new
`group_id`, populated with defaults. `update_bank_config` is a partial
update (only provided fields change), mirroring hindsight's
`update_bank.config_updates`.

**Validation** (must reject at the tool layer — Neo4j Community has no
property-range constraints):
- `disposition_*` ∈ {1, 2, 3, 4, 5} — Pydantic `conint(ge=1, le=5)`.
- `mission` ≤ 1024 chars; `retain_mission` ≤ 1024 chars.
- `recall_max_facts` ∈ [1, 100].
- `entity_types_filter` ⊆ types declared in the active config.yaml; reject unknown.

`retain_mission` ships **conditionally**. The field is only added to the
`:BankConfig` schema and exposed via `update_bank_config` if D9 #1's
investigation lands outcome 1 or 2 (clean hook OR monkey-patchable prompt
builder). If outcome 3 (no override point) wins, `retain_mission` is
omitted entirely — no dead field. The 30-min investigation is a hard
prerequisite for the P3 schema migration, not a "during P3" task.

#### D3b — `:Directive`

```cypher
(:Directive {
  uuid:        STRING (unique),
  group_id:    STRING,
  name:        STRING,            // human-readable, e.g. "Always cite uuid"
  content:     STRING,            // the actual rule, free-text, injected into reflect's prompt
  priority:    INT (default 0),   // higher = more important (sort order)
  is_active:   BOOL (default true),
  tags:        LIST<STRING> (default []),
  created_at:  DATETIME,
  updated_at:  DATETIME
})
CREATE CONSTRAINT directive_uuid_unique IF NOT EXISTS
  FOR (d:Directive) REQUIRE d.uuid IS UNIQUE;
CREATE CONSTRAINT directive_group_name_unique IF NOT EXISTS
  FOR (d:Directive) REQUIRE (d.group_id, d.name) IS UNIQUE;
CREATE INDEX directive_group_id IF NOT EXISTS
  FOR (d:Directive) ON (d.group_id);
```

`content` capped at **1024 chars at write time** (rejected if longer) so
no single directive can blow out reflect's context window.

Three tools:
- `list_directives(group_id?, tags?, active_only=true)`
- `create_directive(name, content, priority=0, is_active=true, tags?)` — fails fast on duplicate `(group_id, name)`
- `delete_directive(directive_id)`

(Hindsight has no `update_directive` — you delete + recreate. Matching that.)

Stacking in `reflect`'s prompt (D2 prompt expanded):

```
You are a memory companion with the following disposition:
- Skepticism: {1-5}  (1 = take memories at face value; 5 = aggressively question)
- Literalism: {1-5}  (1 = abstract/conceptual; 5 = strictly literal)
- Empathy: {1-5}     (1 = analytical detachment; 5 = emotional resonance)

Mission: {bank_config.mission or "Help the user think with their memory"}

Active directives (ordered by priority, highest first):
{directive[0].name}: {directive[0].content}
{directive[1].name}: {directive[1].content}
... (list filtered to is_active=true, sorted by priority DESC, limit ~10
     to avoid prompt bloat)

Facts retrieved from the user's memory graph:
{facts}

Based ONLY on those facts, and respecting the directives above, answer the
question. If the facts are insufficient, say so explicitly — do not invent.
Output ≤{max_tokens} tokens.

Question: {query}
```

Directive precedence: directives override disposition where they conflict
(an active "always be brief" directive beats a high empathy score).

### D4 — `:MentalModel` schema mirrors hindsight's

Adds `status='refreshing'` + `refresh_started_at` for row-level locking
(see refresher cron below) and explicitly plumbs `max_tokens` through to
the reflect call (otherwise the field is dead — R-01).

```cypher
(:MentalModel {
  uuid:                  STRING (unique),
  group_id:              STRING,
  name:                  STRING,
  source_query:          STRING,
  content:               STRING (default ""),                   // most recent reflect output; NEVER set to a raw error string
  status:                STRING (default "pending"),            // pending|fresh|stale|failed|refreshing
  max_tokens:            INT    (default 2048),                 // plumbed through to reflect call at refresh time
  tags:                  LIST<STRING> (default []),
  trigger_refresh_after_consolidation: BOOL (default false),
  refresh_started_at:    DATETIME?,                             // set when status='refreshing', cleared on transition out
  last_refreshed_at:     DATETIME?,
  last_error:            STRING (default ""),                   // short tail of last exception when status='failed'
  created_at:            DATETIME,
  updated_at:            DATETIME
})
CREATE CONSTRAINT mental_model_uuid_unique IF NOT EXISTS
  FOR (m:MentalModel) REQUIRE m.uuid IS UNIQUE;
CREATE INDEX mental_model_group_id IF NOT EXISTS
  FOR (m:MentalModel) ON (m.group_id);
```

Refresher job (R-15, R-16):

- New systemd `--user` timer `recall-refresh-mental-models.timer`,
  daily at 04:00 local (after community-build at 03:30, deploy window ends 04:30).
- The companion `recall-refresh-mental-models.service` runs a script
  inside `recall-mcp` that, **for each model with a sequential per-model
  try/except** (one failure never aborts the batch):
  1. Atomic claim: `MATCH (m:MentalModel) WHERE m.uuid = $uuid AND
     (m.status IN ['pending','fresh','stale','failed'] OR
      m.refresh_started_at < datetime() - duration({hours: 1}))
     SET m.status='refreshing', m.refresh_started_at=datetime()
     RETURN m`. If MATCH returns 0 rows, skip (someone else owns it).
  2. Call `reflect(m.source_query, group_id=m.group_id, max_tokens=m.max_tokens)`.
  3. On success: `SET content=$answer, status='fresh',
     last_refreshed_at=datetime(), refresh_started_at=NULL, last_error=''`.
  4. On exception: `SET status='failed', refresh_started_at=NULL,
     last_error=$tail_200_chars` and ntfy with full payload
     `recall MM refresh failed | group=$gid | model=$name | err=$tail`.
- **Retry policy:** rows with `status='failed'` ARE retried on the next
  cron run (they re-enter the claim filter). No exponential backoff at
  the row level — operator intervention is required if it fails 3 days
  running (manual `clear` or `delete`).
- **Cascade guard:** if 5 consecutive models fail with a 429-class error
  in the same cron run, abort the batch and ntfy
  `recall MM refresh — OpenRouter cascade, batch aborted at N/M`.
- **Optional fast lane:** when `build_communities` produces new communities
  for a group, refresh `:MentalModel` rows in that group with
  `trigger_refresh_after_consolidation=true`. Implementation: extend
  `recall-build-communities.py` to call the refresher for matching models
  at the end. Uses the same claim protocol — fast lane cannot collide with
  the nightly cron.

### D5 — File layout (wrapper grows out of `wrapper_main.py`)

```
~/Docker/recall/
├── Dockerfile                  # COPYs wrapper/ in
├── config.yaml                 # prod entity types
├── config.eval.yaml            # eval entity types
└── wrapper/
    ├── __init__.py
    ├── main.py                 # entrypoint (replaces wrapper_main.py;
    │                           # GroupIDMiddleware + transport_security stay here)
    ├── descriptions.py         # DEFAULT_* + env-var override + apply(mcp)
    ├── reflect.py              # register(mcp) — reflect tool + synthesis prompt assembly
    ├── bank_config.py          # register(mcp) — :BankConfig schema + 2 tools + accessor
    ├── directive.py            # register(mcp) — :Directive schema + 3 tools + reflect loader
    └── mental_model.py         # register(mcp) — :MentalModel schema + 7 tools + refresher API
```

**Module contract (R-11 — explicit, not assumed):** each new module exports
exactly one entry point `register(mcp: FastMCP, *, graphiti_service,
config) -> None` that calls `@mcp.tool()` on its functions. `main.py`
imports `graphiti_mcp_server as server` (which has the module-global
`mcp` already populated with the 9 existing tools), then calls
`descriptions.apply(server.mcp)` and each `xxx.register(server.mcp, ...)`
in dependency order: `bank_config.register(...)` → `directive.register(...)`
→ `reflect.register(...)` → `mental_model.register(...)`. No module ever
creates its own `FastMCP` instance.

Dockerfile change:
```dockerfile
COPY wrapper/ /app/mcp/wrapper/
# Replace entrypoint:
RUN ln -sf /app/mcp/wrapper/main.py /app/mcp/main.py
```

### D6 — Per-container description overrides

Each of the 9 (later 18) tools gets a `DEFAULT_*_DESCRIPTION` constant
in `wrapper/descriptions.py`. Per-container override via env var:

```
RECALL_DESC_ADD_MEMORY      = "..."
RECALL_DESC_SEARCH_NODES    = "..."
RECALL_DESC_SEARCH_FACTS    = "..."
RECALL_DESC_GET_EPISODES    = "..."
RECALL_DESC_REFLECT         = "..."
RECALL_DESC_RETAIN_BANK_CFG = "..."
... etc
```

`recall-mcp-eval` overrides where the eval coding domain wants different
proactive triggers (e.g., reflect description = *"Use this PROACTIVELY when
deciding which file to edit next or which test approach to take"* instead of
the personal-memory wording).

At boot, `descriptions.apply(mcp)` walks the tool registry and overwrites
`.description`. FastMCP private API (R-10) — use a forward-compatible
accessor that raises on miss rather than silently no-opping:

```python
def _tool_registry(mcp):
    tm = getattr(mcp, "_tool_manager", None) or getattr(mcp, "tool_manager", None)
    if tm is None or not hasattr(tm, "_tools"):
        raise RuntimeError(
            "FastMCP tool registry not found (private API drift); "
            "halt boot rather than silently fail to apply description overrides"
        )
    return tm._tools
```

Idempotent.

### D7 — Privacy + LLM cost posture

- `reflect` uses the **same LLM provider** already configured (OpenRouter
  `deepseek-v4-flash` with account-level `data_collection:deny`). No new
  third-party endpoint introduced.
- Mental-model refresh runs at 04:00 — cheap LLM hours, low contention.
- Cost cap: each `reflect` call bounded by `max_tokens` (default 2048,
  configurable per call and per bank). Per-MM refresh ≤ `max_tokens`
  per MM per day.
- No webhook / no outbound HTTP to anywhere other than OpenRouter,
  mem-embed (LAN), and recall-neo4j (LAN).

### D8 — Backward compatibility

- Existing 9 tool **names + signatures** are unchanged. Only their
  descriptions change. Existing prod openclaw agents (juliet, yui, akane)
  keep working. FastMCP's `Tool.parameters` (the input JSON schema) is
  derived from Python **type hints**, not the docstring `Args:` block —
  verified live against the running recall-mcp — so rewriting docstrings
  does not alter input schemas.
- New 13 tools (`reflect` + 2 bank_config + 3 directive + 7 mental_model
  = 13 net) are additive. Total surface: **22**.
- New schema (`:BankConfig`, `:Directive`, `:MentalModel`) is additive and
  isolated by `group_id`. Existing search tools (`search_nodes`,
  `search_memory_facts`) are wrapper-patched to exclude these three labels
  so the new plumbing nodes never appear in agent search results — see
  D11 below.
- Wrapper restart = brief MCP outage (<5 s, same as today's bring-up).
  Confine to the same 03:00-04:00 window already used for backup + builds.

### D9 — Open questions

1. **Can we inject a per-bank "extraction directive" into the LLM call that
   Graphiti makes when `add_memory` runs?**

   Background: `add_memory` accepts a text blob (e.g. *"On 2026-04-30 John
   swapped recall's extractor from Z.ai Coding Plan to OpenRouter GLM-4.6
   because of 429s"*). Graphiti internally calls an LLM to extract entities
   (`:Entity` nodes) and relationships (`:RELATES_TO` edges) from that
   text. Hindsight's `retain_mission` field changes what gets extracted by
   prepending an operator-supplied string to that internal extraction
   prompt — same input text, different distillation depending on the bank's
   mission.

   To make `retain_mission` work in recall we need to do the same thing:
   slip the bank's `retain_mission` string into Graphiti's extraction
   prompt before the LLM call. Three possible outcomes:

   | If Graphiti 0.28.2 has… | …we | Effort |
   |---|---|---|
   | …a config field / kwarg for an extra instruction (e.g. `extraction_instruction_suffix`) | wire it through in one line | trivial |
   | …a single prompt-builder function we can monkey-patch | wrap it in the wrapper module | ~1h, fragile across Graphiti version bumps |
   | …the prompt assembled in deeply nested code with no clean override point | fork `graphiti_core` or punt `retain_mission` to a P3.5 follow-up | ~½ day for the fork; otherwise ship without `retain_mission` |

   **Resolution path:** before starting P3, spend ~30 min reading
   `graphiti_core/utils/maintenance/node_operations.py` +
   `edge_operations.py` to identify which outcome applies. The answer
   only affects `retain_mission`; everything else in P3 ships regardless.

2. **Should mental-model refresh be parallel across models, or sequential?**
   Sequential is simpler and the model count will stay small (≤20 per
   group for the foreseeable future). Start sequential; add a `--parallel
   N` flag if a group ever gets >100 models.

(Original D9 #2 — "do we also ship directives or just dispositions?" — was
resolved IN by the operator after first-pass review: ship both. See
Item 3b in Scope and D3b in Design decisions.)

### D10 — Datetime conventions (R-02)

All new node properties typed `DATETIME` are written via Cypher
`datetime()` (or, equivalently, Python `datetime.now(timezone.utc)` passed
through the neo4j driver's tz-aware serialization). Never strings; never
naïve `datetime`. Matches Graphiti's existing `:Entity.created_at` shape.

Cross-check at AC time: `MATCH (b:BankConfig)
RETURN apoc.meta.cypher.type(b.created_at)` returns `"ZonedDateTime"`.

### D11 — Search-result filtering (R-03)

The wrapper patches `search_nodes` and `search_memory_facts` to add a
`WHERE NOT n:BankConfig AND NOT n:Directive AND NOT n:MentalModel` clause
so the new plumbing nodes never surface in agent search responses. Two
implementation paths:

1. **Cypher post-filter** in the wrapper: intercept the tool, run the
   underlying Graphiti search, drop hits whose `labels(n)` intersect
   `{BankConfig, Directive, MentalModel}`. Cheap, doesn't touch Graphiti.
2. **Tool-call wrapper that injects an `entity_types` whitelist**: Graphiti's
   existing `search_nodes(entity_types=...)` filters at the Cypher layer.
   Slightly faster but requires keeping the whitelist in sync with config.

Recommend (1) for simplicity. Either way, add a probe to AC: write a
directive named "test-leakage", run `search_nodes(query="test-leakage")`,
assert zero results.

### D12 — Orphan cleanup (R-04)

Graphiti's `clear_data(group_ids=[g])` (exposed via the existing
`clear_graph` MCP tool) only knows about labels Graphiti owns
(`:Entity`, `:Episodic`, `:Community`, `:RELATES_TO`, `:MENTIONS`,
`:HAS_EPISODE`, `:NEXT_EPISODE`, `:HAS_MEMBER`). Our additive labels
(`:BankConfig`, `:Directive`, `:MentalModel`) are NOT cleared, and over
time accumulate as orphans when a group_id is retired.

The wrapper intercepts `clear_graph` to extend cleanup:

```cypher
MATCH (n)
WHERE n.group_id = $group_id
  AND ('BankConfig' IN labels(n)
       OR 'Directive' IN labels(n)
       OR 'MentalModel' IN labels(n))
DETACH DELETE n
```

Run **before** delegating to Graphiti's clear_data (so the wrapper's
clean-up errors don't trigger a half-clear). AC: clear_graph for a test
group_id followed by `MATCH (n {group_id: $g}) RETURN labels(n), count(*)`
returns empty.

### D13 — Contextvar discipline (R-12, R-13)

`GroupIDMiddleware` sets `request_group_id` (a `contextvars.ContextVar`)
per ASGI request. `contextvars` propagate across `await` in the same task
**but not** across `asyncio.create_task(...)` or worker threads unless
context is explicitly captured.

The existing recall code path uses `queue_service.add_episode(...)` for
`add_memory` — episodes for the same group_id are processed sequentially
via a queue worker. **The new `reflect` path must NOT rely on the
contextvar propagating across that queue boundary or any equivalent
boundary.**

Rule: every new tool resolves `effective_group_id` eagerly at the top of
the tool function and passes it as an **explicit argument** to every
downstream call, including search, LLM, and any background-task helpers.
The `_GraphitiProxy.group_id` property remains the source of truth for
the contextvar at request entry, but is materialized to a local variable
immediately and never read again in the same call chain.

Audit step: before P2 ships, read `graphiti_core/graphiti.py::search`
end-to-end and confirm no `asyncio.create_task`, `gather` with task
creation, or `loop.run_in_executor` calls that could lose the contextvar.
If any exist, the audit notes the boundary and the explicit `group_id`
argument bridges it.

AC: two concurrent `reflect` calls for different groups (A and B) execute,
captured prompt logs (D2 prompt assembly) show only A's facts in A's
prompt and only B's facts in B's. Run 20× to catch races.

### D14 — Revert paths + kill switches (R-21)

Per-phase image tagging and env-var kill switches so a bad phase can be
disabled or reverted without rebuilding:

- **Image tags per phase**: `recall-mcp:p1`, `:p2`, `:p3`, `:p4`. The
  current `recall-mcp:local` is renamed to `recall-mcp:pre-hindsight`
  before P1 ships and stays available as a known-good rollback target.
- **Env-var feature flags** read at wrapper boot:
  - `RECALL_DESCRIPTIONS_ENABLED` (default true; false reverts to upstream descriptions)
  - `RECALL_REFLECT_ENABLED` (default false until P2 verified; true to register the tool)
  - `RECALL_BANK_CONFIG_ENABLED` (default false until P3 verified)
  - `RECALL_DIRECTIVE_ENABLED` (default false until P3 verified)
  - `RECALL_MENTAL_MODEL_ENABLED` (default false until P4 verified)
  - `RECALL_MM_REFRESH_TIMER_ENABLED` — checked by the systemd service ExecCondition; safest single-knob kill for the cron.
- **Eval-first deploy**: every phase ships to `recall-mcp-eval` first.
  The eval container becomes the canary; prod `recall-mcp` only updates
  after the eval container has run successfully for ≥24 h with no
  flag-rollback events.
- **Revert reproducer** for each phase, embedded in the spec for that
  phase's commit message: `docker compose pull recall-mcp:p<N-1> &&
  docker compose up -d recall-mcp recall-mcp-eval`.

### D15 — Eval fairness (R-23) — three-stack methodology

After P1–P4, recall's capability set itself has changed. The eval question
shifts from a two-way comparison (recall vs hindsight) to a three-way one
(recall-pre vs recall-post vs hindsight).

Methodology:
- Tag the pre-P1 image as `recall-mcp:pre-hindsight-parity` (= today's
  `recall-mcp:local`). Keep it pullable.
- The next eval round runs **three** memory configurations:
  1. **recall-pre** — current 9-tool surface, technical-reference descriptions
  2. **recall-post** — P1–P4 surface (22 tools, coaching descriptions, reflect, mental models, dispositions, directives)
  3. **hindsight** — already running, 57 tools, full hindsight surface
- Prod recall (juliet/yui/akane) does **NOT** auto-upgrade until the
  three-way eval result is documented. Decision to roll P1–P4 into prod
  recall is an explicit operator call after evidence, not a default.
- The eval task spec needs an explicit memory-config dimension; capture
  as a follow-up to `2026-05-29-new-eval-tasks-subagent-research.md`.

## Acceptance criteria

### AC1 — Coaching descriptions live

- [ ] `openclaw mcp show recall` and `hermes mcp test recall` return the
      new coaching descriptions (verify text contains the word
      "PROACTIVELY" for `add_memory`, `search_*`, and `reflect`).
- [ ] All 9 existing tools still accept the same arguments and return the
      same response shapes — `tools/list` JSON schema diff = description
      field only.
- [ ] Env-var override works: setting `RECALL_DESC_ADD_MEMORY="custom"`
      changes the description without rebuild.

### AC2 — `reflect` works end-to-end

- [ ] `tools/list` includes `reflect`. Total tool count = 10 (before AC3/4).
- [ ] `reflect("openrouter swap on 2026-04-30", group_id="juliet")` returns
      a synthesized paragraph that cites the underlying facts. (Verify
      against the dump we just generated.)
- [ ] When no facts match, response says so explicitly — no hallucination.
- [ ] Cost recorded in OpenRouter dashboard against the same key recall
      already uses.

### AC3 — `:BankConfig` round-trips

- [ ] `get_bank_config(group_id="juliet")` returns defaults the first time;
      auto-creates the node.
- [ ] `update_bank_config(group_id="juliet", disposition_skepticism=5,
      mission="be ruthlessly skeptical")` persists.
- [ ] Two `reflect` calls with same query but skepticism=1 vs 5 produce
      visibly different outputs (skepticism=5 calls out unsupported claims;
      skepticism=1 takes them at face value). Captured as a regression test.
- [ ] `entity_types_filter` default flows through to `search_nodes` calls
      when caller omits the arg.

### AC3b — `:Directive` round-trips + stacking

- [ ] `create_directive(name="always cite uuid", content="Every claim must
      reference the source fact UUID inline.", priority=10)` persists.
- [ ] `list_directives(group_id="juliet")` returns it; `list_directives(...,
      active_only=true)` honors the flag.
- [ ] `reflect` calls fetch active directives (sorted by priority DESC,
      capped at ~10) and inject them between disposition and facts in the
      prompt — verify via captured prompt logs.
- [ ] Conflict test: with `disposition_empathy=5` AND active directive
      "respond in three words or fewer," output respects the directive
      (length wins over warmth). Captured as a regression test.
- [ ] `delete_directive` round-trip works; deleted directives don't appear
      in `list_directives` and don't reach `reflect`'s prompt.

### AC4 — Mental models round-trip + refresher cron

- [ ] CRUD round-trip: create → list → get → refresh → update → delete.
- [ ] `create_mental_model(name="recent infra changes", source_query="what
      infrastructure changes happened in the last 7 days?")` returns
      `status="pending"`, then `status="fresh"` after the in-flight
      reflect resolves.
- [ ] systemd `recall-refresh-mental-models.timer` listed by
      `systemctl --user list-timers`; runs daily 04:00 ±5 min.
- [ ] Failed refresh → `status="failed"` + ntfy fires.
- [ ] `trigger_refresh_after_consolidation=true` MMs refreshed at end of
      the community-build job.

### Cross-cutting

- [ ] Wrapper unit tests (new): description override, group-id resolution,
      reflect prompt assembly with disposition + directives stacked,
      MM refresh path.
- [ ] Live integration smoke from inside `harbor-agents-rich:latest`:
      `hermes mcp test recall` → `Tools discovered: 22`.
- [ ] `search_nodes` and `search_memory_facts` never return `:BankConfig`,
      `:Directive`, or `:MentalModel` nodes (D11). Asserted by a probe that
      writes a directive named "test-leakage" then runs `search_nodes(query="test-leakage")` and confirms zero results.
- [ ] FastMCP description-override survives an SDK bump: the override
      registration uses `getattr(mcp, '_tool_manager', None) or
      mcp.tool_manager` and raises if neither exists (no silent no-op).
- [ ] No regressions: existing 9-tool `tools/call` shapes unchanged for
      a sample call of each tool against a known group.
- [ ] Source-of-truth mirrors + drift-prone docs updated (R-20):
      - `infra/recall-memory-stack.docker-compose.yml` (image-tag changes + env-var kill switches)
      - `infra/recall-wrapper-tree.md` (new — short ToC of the wrapper layout)
      - `infra/recall-config.eval.yaml` (only if eval descriptions diverge)
      - `harnesses/README.md` capability table — "recall: 9 tools" → "recall: 22 tools (P4)"
      - `tools/agent_status.py` MCP section — `tools/list` count expectation updated
      - `backlog/FOOTGUNS.md` — new entry for the FastMCP `_tool_manager._tools` private-API forward-compat pattern (D6 / R-10)
      - `~/sambashare/homelab/pinkleberry/thringle/CLAUDE.md` — recall section to note the new tool surface
- [ ] **Restart timing measured, not asserted (R-22):** actual cold-start
      time of `recall-mcp` after each phase is captured in the PR commit
      message; deploys scheduled outside the 03:00–04:30 window already
      used by community-build (03:30) and MM refresh (04:00).

## Implementation phasing

Each phase is independently shippable:

| Phase | Deliverable | Effort | Risk |
|---|---|---|---|
| **P1** | D5 file layout + Item 1 (descriptions only) + D14 kill switches + D11 search filter + D12 orphan clear hook (passive no-op until P3 schema) | ~3h | low |
| **P2** | Item 2 (`reflect` tool) — zero-fact short-circuit, OpenRouter 429 backoff, token-budget guard, contextvar-discipline audit per D13 | ~5h | low — additive |
| **P3** | D9 #1 resolution (~30 min before schema lands) → Items 3 + 3b (`:BankConfig` + `:Directive` schemas, 5 tools, reflect prompt stacks dispositions + directives, `retain_mission` shipped only if D9 #1 outcome 1 or 2) | ~6h | low |
| **P4** | Item 4 (`:MentalModel` schema + 7 tools + refresher cron with row-lock per R-15, retry policy per R-16) | ~6h | medium — touches scheduler |

**Hard ordering (R-19):**
- P1 → P2 → P3 → P4 (no skipping; each phase consumes the previous).
- P1 must register `RECALL_DESC_REFLECT` env-var slot even though reflect
  doesn't exist yet, so P2 can override description without an extra rebuild.
- P3 must NOT proceed before D9 #1's outcome is recorded in this spec.
- P4's cron timer is enabled only AFTER P3 verified — otherwise refresh
  calls into a missing `:BankConfig` schema and flips every MM to `failed`.
- Every phase: deploy to `recall-mcp-eval` first; promote to `recall-mcp`
  only after ≥24 h clean on eval.

Ship P1 first and measure agent behavior on the next eval run **before**
starting P2+. Hypothesis: P1 alone closes most of the observed
"agents-don't-use-recall" gap; if confirmed, P2+ becomes lower-priority.

## Migration impact

- One image rebuild + `docker compose up -d --build` for `recall-mcp` and
  `recall-mcp-eval`. ~30 s outage each, no data migration.
- One additive Neo4j constraint per phase (P3, P4) — idempotent
  `CREATE CONSTRAINT ... IF NOT EXISTS`, runs at wrapper boot.
- No prod data is touched. Existing graph keeps working; new tools light up.
- Backups (restic at `/mnt/crumbleton/docker/recall/`) cover the new node
  types automatically — no scheduling change needed.

## Follow-up tickets (deferred)

- Per-bank `mcp_enabled_tools` allowlist (if recall surface ever exceeds
  ~25 and creates noise).
- `retain_mission` (per-bank extraction directive for `add_memory`) —
  status depends on D9 #1's three-outcome resolution.
- Migrate prod recall (juliet/yui/akane) to use coaching descriptions
  in the SOUL.md instructions instead of/in addition to the MCP layer
  (belt-and-suspenders for proactive use).

## References

- Hindsight tool registrations: `/app/api/hindsight_api/mcp_tools.py:200–3211`
  (in `hindsight-app` container).
- Hindsight default descriptions: `/app/api/hindsight_api/config.py:772–790`.
- Hindsight actual tool count: **57** (verified via
  `grep -cE "@mcp\.tool" mcp_tools.py`), not 27 as casual references suggest.
- Current recall wrapper: `~/Docker/recall/wrapper_main.py` on wiley.
- Current recall MCP server: `/app/mcp/src/graphiti_mcp_server.py` in
  `recall-mcp` container (graphiti_mcp_server 1.26.0 / graphiti-core 0.28.2).
- FastMCP tool registry verified live: `Tool.description` mutable;
  `Tool.parameters` derived from type hints, NOT docstring `Args:` block —
  description rewrites do not alter input schemas.
- Companion shipped specs:
  - [`2026-05-29-memory-stack-deployment.md`](2026-05-29-memory-stack-deployment.md)
  - [`2026-05-29-recall-bge-m3-and-eval-ontology.md`](2026-05-29-recall-bge-m3-and-eval-ontology.md) — precondition: bge-m3 + deepseek-v4-flash + community-build cron + eval ontology

## Revision history

- **2026-05-29 v1** — initial draft (items 1, 2, 3a, 4); operator review folded in 3b (directives).
- **2026-05-29 v2** — adversarial subagent review surfaced 23 issues
  (11 must-fix, 9 should-fix, 3 verified-OK). Folded in: corrected tool-count
  math (21 → 22; hindsight 27 → 57); D2 zero-fact short-circuit + OpenRouter
  429 backoff + token-budget guard; D3a validators + conditional
  `retain_mission` shipping gated on D9 #1 outcome; D3b
  `(group_id, name)` directive uniqueness + 1024-char content cap; D4
  `status='refreshing'` row-lock + retry policy + ntfy granularity +
  explicit `max_tokens` plumbing; D5 explicit `register(mcp)` module
  contract; D6 FastMCP private-API forward-compat accessor; new sections
  D10 (datetime), D11 (search-result filtering), D12 (orphan cleanup), D13
  (contextvar discipline + Graphiti search audit), D14 (image-tag revert
  paths + env-var kill switches), D15 (three-stack eval-fairness
  methodology); hard phase-ordering rule; drift-prone docs list expanded
  to 7; restart-timing claim retracted (measure, don't assert).
- **2026-05-30 SHIPPED P1+P2+P3+P4** to `recall-mcp-eval` (canary) and
  `recall-mcp` (prod) on the same day, ahead of the spec's 24h canary clock
  per operator direction. D9 #1 resolved as **outcome 1** (clean public hook
  at `graphiti_core/utils/maintenance/node_operations.py:69`); `retain_mission`
  shipped. Final tool count: **23** (9 existing + `reflect` + `get_bank_config`
  + `update_bank_config` + `list_directives` + `create_directive` +
  `delete_directive` + `clear_bank_data` + 7 mental-model tools). Image
  ladder: `:pre-hindsight-parity` → `:p1` → `:p2` → `:p3` → `:p4`.
- **2026-05-30 v3 post-impl adversarial review** — surfaced 22 issues.
  3 must-fix folded in inline at ship time (R-03 APOC node-lock for claim
  race; R-13 ntfy on retain_mission lookup failure; R-21 monkey-patch
  idempotency sentinel). 9 deferred should-fixes resolved in a second pass
  (image `:p4-r2`): R-01 BankConfig 60s LRU+TTL cache with invalidate-on-write;
  R-02 retain_mission snapshot moved from worker-execution to enqueue time
  via `QueueService.add_episode` patch (audit-correct semantics); R-04
  `refresh_mental_model(force=true)` breaks stuck claims; R-06 `_ntfy_sync`
  schedules async via `loop.create_task` in async context; R-08
  `refresh_mental_model(unless_fresher_than_seconds=N)` skips redundant
  refreshes; R-10 `schema.close_driver()` in main.py + cron try/finally;
  R-12 mission validator rejects whitespace-only and `<3` chars; R-14
  `delete_mental_model` description rewritten with DANGEROUS framing;
  R-16 abort-marker `/app/mcp/.mm-retry-needed` + hourly
  `recall-refresh-mental-models-retry.timer` with ExecCondition; R-17
  Dockerfile COPY order reordered stable-to-volatile (descriptions LAST);
  R-19 cron moved 04:00 → 02:00 (clear of backup window); R-20 automated
  directive-override probe (`recall-test-directive-override.sh`) — PASSED
  (7 words out of 7-word cap). R-22 (Neo4j hot-backup risk) verified as
  pre-existing for ALL recall data, accepted, documented as FOOTGUN #25.
  FOOTGUN #24 added for `neo4j.time.DateTime` vs stdlib datetime arithmetic
  (discovered during R-08 verification — needs `.to_native()`).

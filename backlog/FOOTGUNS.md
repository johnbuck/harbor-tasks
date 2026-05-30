# FOOTGUNS

Hard-won, non-obvious traps in this repo's stack (Harbor + openclaw/hermes
adapters + OpenRouter + rewardkit). Each entry: the symptom, the real cause, and
the fix. Add to this as we hit new ones.

---

## 1. openclaw reasoning needs `reasoning: true` BEFORE it reads `compat` (the big one)

**Symptom:** openclaw aborts immediately with
`Error: Thinking level "<level>" is not supported for <provider>/<model>. Use one of: off.`
— identical message whether you used `--thinking high`, `xhigh`, the built-in
`openrouter` provider, the built-in `openai` provider, or a custom provider.
The agent never makes an API call → reward 0, no session file.

**The trap:** the openclaw docs say custom OpenAI-compatible providers opt into
`/think xhigh` by declaring
`models.providers.<p>.models[].compat.supportedReasoningEfforts`. That is
**necessary but NOT sufficient**, and the missing half is undocumented.

**Actual root cause** (openclaw 2026.5.26, `dist/thinking-*.js` +
`dist/model-catalog-*.js`):
- Each provider model row is normalized with
  `reasoning: typeof model.reasoning === "boolean" ? model.reasoning : false`
  — **defaults to `false`**.
- `resolveThinkingProfile()` does, in order:
  1. `if (context.reasoning === false) return buildOffOnlyThinkingProfile();`  ← short-circuit
  2. *only after that* `if (catalogSupportsXHigh(context.compat)) appendProfileLevel(profile, "xhigh")`
- So with `reasoning` unset (false), openclaw returns **off-only BEFORE it ever
  looks at your `compat` list**. The compat menu is real, but the `reasoning`
  flag is the gate in front of it.

**Why built-in providers can't be fixed at all:** built-in providers
(`openrouter`, `openai`, `anthropic`) resolve a model's reasoning profile from
openclaw's **own catalog**, not from your per-model config. A model the catalog
doesn't recognize (e.g. `deepseek/deepseek-v4-pro`) resolves to off-only and
your declared `compat`/`reasoning` are ignored. You MUST use a **custom-named**
provider for the per-model override to take effect.

**The full working recipe** (all parts required; any one missing → off-only or
auth failure):
```jsonc
{
  "models": { "providers": {
    "xrouter": {                                  // CUSTOM name, NOT "openrouter"/"openai"
      "baseUrl": "https://openrouter.ai/api/v1",  // OpenRouter's OpenAI-compatible endpoint
      "apiKey": "${XROUTER_API_KEY}",             // see footgun #2
      "models": [{
        "id": "deepseek/deepseek-v4-pro",         // BARE slug (no provider prefix) — see footgun #3
        "name": "deepseek/deepseek-v4-pro",
        "reasoning": true,                        // ← THE GATE. Without this, compat is never read.
        "compat": { "supportedReasoningEfforts": ["low","medium","high","xhigh"] }
      }]
    }
  }}
}
```
then run `--thinking high` and select `--model xrouter/deepseek/deepseek-v4-pro`.

**1a. Use `--thinking high`, NOT `xhigh`.** openclaw's `xhigh` emits a
`reasoning_effort` payload that deepseek-v4-pro's OpenRouter route rejects with
`400 reasoning_effort: Invalid option: expected one of "xhigh"|"high"|...`. `high`
is accepted and genuinely reasons. Keep `xhigh` in the *declared* compat list
(it's the gate menu), but run at `high`. (Per-model; re-check for other models.)

**Verified end-to-end 2026-05-28:** stock prebaked image + `OpenClawOpenRouter`
on a QuixBugs task → reward 1.0 with `reasoning_tokens = 327` across 4 turns.

**Verification gate (mandatory):** never trust "it ran". Confirm
`reasoning_tokens > 0` (or non-empty `message.reasoning`) in
`openclaw.session.jsonl`. A run with `reasoning: false` exits 0 and looks fine
but did zero thinking.

Implemented in `lib/openclaw_openrouter.py` (`OpenClawOpenRouter`). The provider
name lives in the `_PROVIDER` constant.

---

## 2. A custom openclaw provider gets NO free env-var auth

**Symptom:** thinking gate passes, then:
`Error: No API key found for provider "xrouter". Auth store: .../auth-profiles.json ...`

**Cause:** openclaw's built-in env mapping (`OPENROUTER_API_KEY` →
built-in `openrouter` provider) does NOT apply to custom providers, and
`shellEnvFallback` is disabled by default. Forwarding `XROUTER_API_KEY` into the
container is not enough on its own.

**Fix:** point the provider's `apiKey` at an **env-template SecretRef**:
`"apiKey": "${XROUTER_API_KEY}"`. openclaw resolves `${VARNAME}` from the
environment at runtime even in a `--local` run. The `${...}` string is a MARKER,
not the secret value, so it is safe to write into `openclaw.json`. Still forward
the actual `XROUTER_API_KEY` env into the container (Harbor's
`_provider_env_keys` override does this).

**Never** write the literal key into the config — `openclaw.upload.json` is
copied to `/logs/agent/` and would leak the secret into artifacts/context.

---

## 3. Provider model-entry `id` must be the BARE model slug

**Symptom:** provider is recognized (`openclaw models list` shows the model),
but reasoning/compat still isn't honored.

**Cause:** you select `--model xrouter/deepseek/deepseek-v4-pro`; openclaw splits
provider `xrouter` + model key `deepseek/deepseek-v4-pro`, then looks for a
catalog entry whose `id` is the **bare** `deepseek/deepseek-v4-pro`. Harbor's
base `_normalize_provider_models_schema` fills `id` with the FULL prefixed name
(`xrouter/deepseek/...`), which never matches → entry unused.

**Fix:** in the adapter, set the model entry `id`/`name` to the slug (strip the
leading `<provider>/`). openclaw still sends the bare slug to the OpenAI endpoint.

---

## 4. Harbor `reward.json` must contain ONLY numeric values

A single string key (e.g. a debug `"note"`) makes Harbor's reward parser reject
the **entire** reward → trial scores 0/errors. Keep `reward.json` numeric-only
(`reward`, `correctness`, axis scores). Put any commentary in stdout, not the
reward file.

---

## 5. `tests/` is BAKED into the task image at build

Editing a verifier (`tests/test.sh`, `tests/llm_judge.py`) has NO effect until
you rebuild the task image. Use `environment.force_build: true` (or bump the
Dockerfile) after any verifier change, or you'll keep testing the old verifier.

---

## 6. LLM judges return prose around their JSON

`json.loads()` chokes on a judge reply that wraps JSON in commentary or emits two
objects ("Extra data"). Parse with
`json.JSONDecoder().raw_decode(match.group(0))[0]` after regex-locating the first
`{...}`. All `tests/llm_judge.py` files use this.

---

## 7. rewardkit under `uvx` shadows the image python

rewardkit runs under `uvx`, whose venv `python` is NOT the task image's
interpreter — `python -m pytest` then fails to import the project. Call
`/usr/local/bin/python` explicitly inside rewardkit reward scripts.

---

## 8. A local dataset `path` must be a PARENT dir of task dirs

Pointing `datasets[].path` at a task dir itself yields
"Either datasets or tasks must be provided." Point it at the parent directory
that CONTAINS the task dir(s). To run a single task, symlink it into a temp
parent dir and point at that.

---

## 9. Not all benchmark adapters are current-schema

~52 of the bundled adapters are current-schema and run as-is, but some
(`ds1000`, `devopsgym`, `swegym`) ship a stale `task.toml` (e.g. missing
`task.name`) and need a rewrite. Validate any new benchmark with `--agent oracle`
before assuming it works.

---

## 10. tau3-bench's `model_name` is NOT the agent under test

tau3-bench ships its own reference agent (`Tau3LLMAgent`) and an internal
sim-user + judge LLM. The `model_name: gpt-5.2` in its yaml drives THAT agent and
the runtime LLMs — not the harness you're evaluating. For harness eval, point
`--agent openclaw`/`hermes` at the task directly (both adapters wire the task's
`[[environment.mcp_servers]]` runtime in natively); the sim-user/judge model is a
fixed environment constant, identical for both harnesses. Its `${OPENAI_*}` env
must be EXPORTED in the harbor process (task.toml `[verifier.env]` resolves
`${...}` at config-load), via `infisical run -- bash -c 'export ...; harbor run'`.

---

## 11. Infisical CLI secret leaks (carried from homelab SECRETS.md)

- `infisical secrets set NAME=@/path` silently stores the literal `@/path`
  string — use `--file=`/`--stdin`.
- `infisical secrets set` / `export` print the value to stdout by default
  (`--silent` does NOT suppress it) — redirect `>/dev/null 2>&1`.
- Never `ps`/`pgrep -af` a command carrying `--token=` — it dumps the JWT to
  context. Check background jobs without dumping args.
- Never `grep` a `.env` file for a value — use shape-only patterns or
  docker-exec passthrough.

---

## 12. Harbor's bundled `installed.*` adapters REBUILD a barebones harness config

The stock `harbor.agents.installed.openclaw` / `installed.hermes` adapters **throw
away the harness's real config and generate a minimal one** (openclaw
`_DEFAULT_CONFIG={}`; hermes `_build_config_yaml` → `toolsets:[hermes-cli]`, memory
off, no skills, no persona — AND it sets `HERMES_HOME=/tmp/hermes`, bypassing the
seeded `~/.hermes`). Every capability (reasoning, skills, memory, persona) then has
to be reverse-engineered field-by-field. This is the root cause of the whole
reasoning saga. **Fix:** pre-built harness images + a THIN adapter that invokes the
harness with its OWN baked config and only captures metrics. Don't reconstruct config.

---

## 13. Hermes skills are inert until `$HERMES_HOME/skills/` is seeded

A fresh hermes home has **0 skills active** (`hermes skills list` → 0 builtin/0
enabled). The package ships 90 builtin + 84 optional skills as a *source catalog*;
they only become "enabled" once present in `$HERMES_HOME/skills/`. Because Harbor's
adapter points `HERMES_HOME=/tmp/hermes` (fresh), hermes runs with **zero skills**
unless you seed a real home. (The image's `~/.hermes` shows 85 only because the
build populated it.) openclaw, by contrast, gates skills by requirements and shows
13 ready in a bare sandbox.

Also: hermes only declares `prerequisites.commands` + `platforms` in skill
frontmatter — NOT API-key/service needs — so its "runnable" count is **inflated**
(e.g. notion/linear/airtable look runnable but need keys). openclaw gates on
bins+env+config+os, so its count is honest.

---

## 14. `pyyaml` is NOT in the image's base `python3`

Parsing SKILL.md frontmatter with the image `python3` silently fails (`import yaml`
→ ImportError → your script sees zero metadata and mis-reports everything as
requirement-free). Use the hermes venv interpreter
`/usr/local/lib/hermes-agent/venv/bin/python`, which has pyyaml. (Cousin of #7.)

---

## 15. openclaw skills live in the PACKAGE, not `~/.openclaw/skills/`

`~/.openclaw/skills/` is the empty *user* skills dir. The ~57 bundled skills are in
`<npm-root>/openclaw/skills/` + extension skills under `dist/extensions/*/skills/`.
Use `openclaw skills check` (reports ready / visible / missing-requirements) — don't
infer "no skills" from an empty user dir.

---

## 16. "coding-agent" skills delegate to an EXTERNAL agent CLI (don't use for harness eval)

openclaw `coding-agent` and hermes `autonomous-ai-agents/{claude-code,codex,opencode}`
spawn a **different** coding agent (`claude`/`codex`/`opencode`/`pi`) as a background
worker (openclaw body: `claude --permission-mode bypassPermissions --print`, installs
`@anthropic-ai/claude-code`+`@openai/codex`). Using them measures the sub-CLI, not the
harness — and needs those CLIs installed. For agent-driven-development use the
harness's NATIVE subagents: openclaw `sessions_spawn`/`sessions_yield`, hermes
`delegate_task`. Likewise `canvas` (openclaw) renders to a connected OpenClaw *node*
(none in a headless container) → inert; don't include it.

---

## 17. Harbor's `environment.env` substitution does NOT reach the adapter's `_get_env`

**Symptom:** with `environment.env: ["XROUTER_API_KEY=${OPENROUTER_API_KEY}"]`, the
openclaw thin adapter still got `401 Missing Authentication header` — the key never
reached the container — while the hermes adapter (same run, same key) worked.

**Cause:** the bundled adapters forward provider keys by reading the **harbor
process env** (`self._get_env("XROUTER_API_KEY")` / `os.environ`), NOT the
`environment.env` map (that map is the *container's* docker env, populated
separately). infisical injects `OPENROUTER_API_KEY` into the harbor process; there
is no `XROUTER_API_KEY` there, so the adapter forwarded nothing.

**Fix:** use ONE key everywhere. Point the baked openclaw config's custom provider
at `${OPENROUTER_API_KEY}` (not `${XROUTER_API_KEY}`) and have the thin adapter
forward `os.environ["OPENROUTER_API_KEY"]` directly — exactly like the hermes
adapter. Don't rely on `environment.env` `${...}` substitution reaching adapter
code. (Verified: both reward 1.0 after the switch.)

---

## 18. openclaw (undici) ignores a `headers.Host`; recall's MCP DNS-rebind guard then 400s

**Symptom:** `[bundle-mcp] failed to start server "recall" ... Invalid Host header`.
A `mcp.servers.recall.headers.Host: "localhost:8407"` had no effect.

**Cause:** two things. (1) openclaw's HTTP client (undici) derives `Host` from the
URL authority and **ignores a custom `Host` header** — so it sends
`Host: wiley-pinkleberry.lan:8407`. (2) The mcp Python SDK's
`TransportSecuritySettings` defaults `allowed_hosts=["127.0.0.1:*","localhost:*",
"[::1]:*"]` with `enable_dns_rebinding_protection=True`, so any other Host → 400.
(`curl -H "Host: localhost:8407"` works because curl honors the override; undici
won't.) NON-`Host` custom headers (e.g. `X-Group-ID`) ARE forwarded by openclaw —
verified with a header-echo probe — so per-agent isolation still works.

**Fix (server-side, keeps protection ON):** widen recall's allowlist. In recall's
`wrapper_main.py`, before `streamable_http_app()`:
`server.mcp.settings.transport_security = TransportSecuritySettings(
enable_dns_rebinding_protection=True, allowed_hosts=[...localhost..., "wiley-pinkleberry.lan:*", "recall-mcp:*"], allowed_origins=[])`.
Then drop the vestigial `Host` header from the harness configs. (API clients send
no `Origin`, so `allowed_origins=[]` is fine.)

---

## 19. The hermes venv has NO pip — install plugin deps with uv

**Symptom:** `RUN .../venv/bin/pip install honcho-ai` fails (`No module named pip`);
a `|| pip install` fallback silently lands the package in the WRONG interpreter
(system python3.12), so hermes (its own venv, py3.11) never sees it.

**Cause:** hermes ships a **uv-managed venv** at `/usr/local/lib/hermes-agent/venv`
(note: `venv`, not `.venv`) with no pip seeded. (Cousin of #14, which used the venv
*python* for pyyaml.)

**Fix:** `uv pip install --python /usr/local/lib/hermes-agent/venv/bin/python <pkg>`
(uv is at `/root/.local/bin/uv`). Needed for honcho-ai (the honcho memory provider's
`pip_dependencies`).

---

## 20. hermes has TWO independent plugin activation systems — `hermes plugins list` shows only one

**Symptom:** `hermes plugins list` reports `0 enabled / 61 total`, but `memory/honcho`
is **demonstrably loaded** (`memory.provider: honcho` config + honcho-ai package
installed + verified at runtime).

**Cause:** hermes has two completely independent activation tracks that don't know
about each other:

- **System 1 — `plugins.enabled` allow-list.** `hermes_cli/plugins.py:_get_enabled_plugins()`
  reads `config.yaml`'s `plugins.enabled` / `plugins.disabled`. Source comment:
  `# None = opt-in default (nothing enabled)`. This is what `hermes plugins list`
  reflects, what `hermes plugins enable <name>` toggles, and what gates user-installed
  plugins under `$HERMES_HOME/plugins/`.
- **System 2 — direct config-driven import (the bypass).** `agent/agent_init.py`
  does `from plugins.memory import load_memory_provider as _load_mem` and calls
  `_load_mem(memory.provider)`. Same pattern for `context_engine`, `teams_pipeline`,
  `honcho.client`, …. This path **completely bypasses System 1**: if a config key
  selects a plugin, it loads, regardless of what `hermes plugins list` says.

**Practical consequences:**
- `hermes plugins list` omits entire categories. `memory/*` and `context_engine/*`
  do not appear at all — confirmed by greping the CLI output for "honcho" (absent).
- The filesystem (`/usr/local/lib/hermes-agent/plugins/<category>/<name>/`) is the
  canonical bundled set (69 plugin dirs as of hermes v0.14.0). The CLI's 61-row
  view is a subset.
- `agent.context.engine`'s **default** value `"compressor"` is a hardcoded
  built-in ContextCompressor — not a swappable plugin (no `plugin.yaml`). Treating
  it as a plugin makes "context_engine 0 active" look wrong; it isn't.

**Fix (when you need to know what's really active):** union of both systems.
1. Allow-list set = `config.yaml` `plugins.enabled` ∪ rows where CLI Status = `enabled`.
2. Config-driven set: register one mapping per known bypass category, e.g.
   ```python
   cat_getters = {
       'memory':         lambda c: (c.get('memory') or {}).get('provider'),
       'context_engine': lambda c: (((c.get('agent') or {}).get('context') or {})
                                    .get('engine')) or 'compressor',
       # browser, model-providers: not yet mapped — they use registry patterns.
   }
   ```
3. A plugin is active iff it's in either set AND a `plugin.yaml` exists for it on
   disk (filters out hardcoded built-ins like context_engine/compressor).

Implemented in `tools/agent_status.py` (the eval status dashboard). Adding a new
bypass mapping is one line in `cat_getters`. Full writeup:
`backlog/done/2026-05-29-hermes-dual-plugin-system.md`.

## 21. FastMCP tool registry is private API — silent no-op risk on SDK bump

`@mcp.tool()` registers tools into `mcp._tool_manager._tools` (a private dict).
We rewrite descriptions there from the wrapper at boot (see
`~/Docker/recall/wrapper/descriptions.py::apply` and `backlog/2026-05-29-recall-hindsight-style-plugin.md` D6).

Verified live against `mcp==…` shipped in `zepai/knowledge-graph-mcp:1.0.2`:
- `Tool.description` is a mutable attribute → mutation propagates to subsequent
  `tools/list` responses (no per-startup snapshot).
- `Tool.parameters` (the input JSON schema) is derived from **Python type hints**,
  NOT the docstring `Args:` block → rewriting descriptions does not alter input
  schemas. Backward-compat for argument shapes is safe.

**Footgun:** the MCP SDK is moving toward a public `mcp.tool_manager`
(no underscore). If `_tool_manager` disappears in a future bump, naive
`getattr(mcp, '_tool_manager')._tools` returns `None` and our override silently
no-ops — descriptions revert to upstream technical-reference style, agents quietly
stop using recall proactively. No log, no error.

**Fix (the pattern):** read both names and **raise on miss** so an SDK bump halts
boot instead of shipping un-coached descriptions:

```python
def _tool_registry(mcp):
    tm = getattr(mcp, "_tool_manager", None) or getattr(mcp, "tool_manager", None)
    if tm is None or not hasattr(tm, "_tools"):
        raise RuntimeError(
            "FastMCP tool registry not found at `_tool_manager._tools` or "
            "`tool_manager._tools` — private API has drifted. Halting boot."
        )
    return tm._tools
```

Surfaces the breakage as a deploy-time failure (visible) rather than a runtime
behavior regression (invisible). Apply the same pattern anywhere a wrapper
reaches into a server's tool registry to mutate it.

## 22. Neo4j claim/release patterns need `apoc.lock.nodes()` to be atomic

The naive Cypher `MATCH (n) WHERE n.status <> 'busy' SET n.status = 'busy' RETURN n`
is **NOT atomic across concurrent transactions** under Neo4j's read-committed
snapshot semantics. Two callers can both pass the `WHERE`, both proceed to
`SET`, both return the node — and both think they own the claim. Double-bills,
clobbered writes, undefined behavior.

Discovered in recall's `:MentalModel` row claim
(`wrapper/mental_model.py::_try_claim_for_refresh`) during adversarial review
of P4. The fix is to acquire the write lock **before** the predicate check via
APOC:

```cypher
MATCH (m:MentalModel {uuid: $uuid})
CALL apoc.lock.nodes([m])
WITH m
WHERE m.status <> 'refreshing'
   OR m.refresh_started_at IS NULL
   OR m.refresh_started_at < datetime() - duration({hours: 1})
SET m.status = 'refreshing',
    m.refresh_started_at = datetime(),
    m.updated_at = datetime()
RETURN m
```

`apoc.lock.nodes([m])` grabs an exclusive lock on the node for the duration
of the transaction. The `WHERE` then runs against the locked state, the `SET`
commits, and the lock releases on tx end. Concurrent callers serialize through
the lock; only one passes the predicate, the rest fall through to the empty
return.

Requires APOC installed (recall-neo4j has it via `NEO4J_PLUGINS=["apoc"]`).
**Any wrapper-side claim/release pattern in this codebase must use this idiom.**
A "MATCH-WHERE-SET" without `apoc.lock.nodes` is a bug, not an optimization.

## 23. Monkey-patches need idempotency sentinels

Wrapping an existing function via `original = obj.method; obj.method = wrapped`
is **not idempotent** — if `inject_xxx()` runs twice, the second invocation
captures the *already-wrapped* function as `original`, producing nested
wrappers that compound latency and side effects per call.

Discovered in recall's `inject_retain_mission` (P3 `patches.py`). Pattern:

```python
def inject_retain_mission(client, server_module) -> bool:
    if getattr(client.add_episode, "_recall_retain_mission_patched", False):
        return False  # already wrapped, no-op
    original = client.add_episode
    async def patched(*args, **kwargs):
        ...
        return await original(*args, **kwargs)
    patched._recall_retain_mission_patched = True
    client.add_episode = patched
    return True
```

Apply this sentinel pattern to **every** wrapper that monkey-patches a foreign
attribute. Triggers include: hot reloads (currently not in use, but future-proof),
multiple `inject_*` calls in the boot sequence, test fixtures that
mock-then-unmock.

## 24. Neo4j async driver returns its own `DateTime`, not Python's stdlib `datetime`

When the wrapper writes `b.last_refreshed_at = datetime()` (Cypher) and later
reads it back via the Python async driver, the value is a `neo4j.time.DateTime`
— a Neo4j-flavored class with its own `.year/.month/.day/...` accessors. It is
**NOT** subtractable from a stdlib `datetime.datetime`:

```python
>>> from datetime import datetime, timezone
>>> datetime.now(timezone.utc) - row["last_refreshed_at"]
TypeError: unsupported operand type(s) for -: 'datetime.datetime' and 'DateTime'
```

The fix is `.to_native()`, which converts to a stdlib `datetime.datetime`:

```python
last = row.get("last_refreshed_at")
last_py = last.to_native() if hasattr(last, "to_native") else last
delta = (datetime.now(timezone.utc) - last_py).total_seconds()
```

The `hasattr` guard keeps the code working if a caller passes an already-native
datetime (e.g. from a Pydantic model or a test fixture). Apply this conversion
anywhere wrapper-side Python code does arithmetic on neo4j-returned datetimes.

Discovered in recall's `refresh_mental_model(unless_fresher_than_seconds=...)`
during the R-08 fix verification.

## 25. Neo4j hot filesystem backups: known risk, currently accepted

`restic-docker-backup.timer` (hourly) snapshots `/mnt/crumbleton/docker/recall/`
as a **hot filesystem copy** — the recall-neo4j container keeps writing during
the snapshot. Per Neo4j's own docs, the safe pattern is either:

1. `neo4j-admin database dump` (offline; consistent snapshot)
2. Stop the container, copy, restart (consistent but downtime)

Option (3) — hot copy — is what we do. In practice Neo4j's WAL replays on
restore and most snapshots come out consistent, but the formal guarantee is
weaker than (1) or (2). The window during which a snapshot could capture an
inconsistent state is small (sub-second writes) and the agent-memory data is
recoverable from episodes if needed.

This applies to **all** recall data — `:Entity`, `:Episodic`, `:RELATES_TO`,
`:Community`, AND the wrapper-owned `:BankConfig` / `:Directive` / `:MentalModel`.
The hindsight-plugin spec inherits the existing risk without amplifying it.

**Operator decision pending**: switch to `neo4j-admin database dump` cron
(separate from this spec). Spec backlog entry to be added if/when scheduled.

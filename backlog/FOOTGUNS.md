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
`${...}` at config-load), via `infisical run --domain=http://internal-host:8380 --projectId=INFISICAL_PROJECT_ID --env=production --path=/proxy/ -- bash -c 'export ...; harbor run'` (self-hosted only — see §26).

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
`Host: internal-host:8407`. (2) The mcp Python SDK's
`TransportSecuritySettings` defaults `allowed_hosts=["127.0.0.1:*","localhost:*",
"[::1]:*"]` with `enable_dns_rebinding_protection=True`, so any other Host → 400.
(`curl -H "Host: localhost:8407"` works because curl honors the override; undici
won't.) NON-`Host` custom headers (e.g. `X-Group-ID`) ARE forwarded by openclaw —
verified with a header-echo probe — so per-agent isolation still works.

**Fix (server-side, keeps protection ON):** widen recall's allowlist. In recall's
`wrapper_main.py`, before `streamable_http_app()`:
`server.mcp.settings.transport_security = TransportSecuritySettings(
enable_dns_rebinding_protection=True, allowed_hosts=[...localhost..., "internal-host:*", "recall-mcp:*"], allowed_origins=[])`.
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

---

## 26. Infisical CLI: `--domain` is required on `login` AND `run` (env var ignored)

**HARD RULE: this project NEVER uses Infisical Cloud. The only instance is the
self-hosted `http://internal-host:8380`.** Any `infisical login`/`run`
WITHOUT an explicit `--domain=http://internal-host:8380` silently
defaults to cloud (`app.infisical.com`) and is WRONG — every command must carry
`--domain`, or use the `tools/run_*.sh` wrappers which do.

**Symptom 1 (login):** `infisical login --method=universal-auth ...` succeeds (rc=0) but emits an error message about `domain ... Current domain ... https://app.infisical.com` instead of a JWT. The CLI is hitting the **cloud** endpoint, not the self-hosted one set by `INFISICAL_SITE_URL`.

**Symptom 2 (run):** later, `infisical run --projectId ... -- <cmd>` returns:
```
CallGetRawSecretsV3: ... Get "https://app.infisical.com/api/v3/secrets/raw?...": ...
```
Same root cause — `run` also ignores `INFISICAL_SITE_URL`.

**Fix:** pass `--domain="$INFISICAL_SITE_URL"` explicitly on **both** commands:
```bash
infisical login --method=universal-auth --client-id=... --client-secret=... \
    --domain="http://internal-host:8380" --plain --silent >tokfile
infisical run --domain="http://internal-host:8380" \
    --projectId=... --env=production --path=/proxy/ -- <cmd>
```

`tools/run_track_a.sh` handles both for free.

---

## 27. Infisical `--plain --silent` JWT comes with a trailing newline → HTTP-header crash

**Symptom:** after a clean login, the next CLI call fails with:
```
CallGetRawSecretsV3: ... net/http: invalid header field value for "Authorization"
```

**Cause:** `--plain --silent` writes the token **followed by `\n`**. If you do
```bash
export INFISICAL_TOKEN="$(cat /tmp/tok)"
```
or worse, `export INFISICAL_TOKEN=$(infisical login ...)`, the newline survives into the env var, then into the `Authorization: Bearer <jwt>\n` header, which the Go `net/http` library rejects.

**Fix:** strip with `tr -d '\r\n'` before exporting:
```bash
export INFISICAL_TOKEN="$(tr -d '\r\n' < /tmp/tok)"
```

**Debug pattern (shape-only, never prints token bytes):**
```bash
printf 'bytes: '; wc -c < /tmp/tok
printf 'ends_with_newline: '; tail -c 1 /tmp/tok | od -An -c | tr -d ' '
printf 'starts_with: '; head -c 2 /tmp/tok | tr -c 'A-Za-z0-9' '?'; echo
printf 'has_jwt_pattern: '; grep -cE '^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\s*$' /tmp/tok
```
A clean JWT shows `bytes: ~400`, `ends_with_newline: \n` (or empty after strip), `starts_with: ey`, `has_jwt_pattern: 1`, two dots.

---

## 28. `multi_step_reward_strategy` placed after `[metadata]` is silently scoped to metadata

**Symptom:** Harbor's CLI reports `Correctness: 0.167` (= 1/6) on a multi-step task where the **final** step gets `correctness=1` and you set `multi_step_reward_strategy = "final"`. Per-step `reward.json` files all show `1.0`, but the trial-level rollup looks like a mean across steps.

**Cause:** TOML scoping. In `task.toml` like:
```toml
[metadata]
category = "..."
tags = [...]

multi_step_reward_strategy = "final"   # ← parsed as metadata.multi_step_reward_strategy
```
The blank line does NOT close the table. Once you enter `[metadata]`, every bare key belongs to it until another `[table]` header. So Harbor doesn't see your strategy override and defaults to `mean`.

**Fix:** put `multi_step_reward_strategy` **at the very top of the file** (before any `[table]` header) so it's a true root-level key:
```toml
schema_version = "1.1"
multi_step_reward_strategy = "final"

[task]
...
```

Sanity check via `python3 -c "import tomllib; d=tomllib.loads(open('task.toml').read()); print('root=', d.get('multi_step_reward_strategy'), 'metadata=', d.get('metadata',{}).get('multi_step_reward_strategy'))"` — root should be set, metadata should be `None`.

---

## 29. Browserless v2 advertises `ws://0.0.0.0:3000/` by default; consumers time out

**Symptom:** Hermes' `_resolve_cdp_override` (via `tools/browser_tool.py`) fetches `/json/version` from the CDP server, reads `webSocketDebuggerUrl`, and tries to connect. With browserless's default config, the URL is `ws://0.0.0.0:3000/` — which routes to nothing on the consumer side, leading to silent timeout.

**Fix:** set `EXTERNAL=<routable-url>` in the browserless compose env so it advertises the address that consumers can actually reach:

```yaml
environment:
  - EXTERNAL=http://internal-host:9222
```

Consumers then get back `ws://internal-host:9222/` and connect successfully. Verified at `~/Docker/agent-cdp/docker-compose.yml` on wiley.

---

## 30. Harbor's `harbor run` prompts interactively when verifier.env references host env

**Symptom:** background `harbor run` hangs forever (no log output, no Docker activity). `ps` shows the harbor process is alive but doing nothing.

**Cause:** when `task.toml` `[verifier.env]` references a host env var like `${ANTHROPIC_API_KEY}`, Harbor asks `Tasks in this run will load these from your environment. Proceed? (Y/n):` on stdin. In a non-tty context the prompt sits forever.

**Fix:** pass `-y` (or `--yes`) to `harbor run` to auto-confirm. `tools/run_track_a.sh` does this implicitly via the programmatic `Job.create()` API; the CLI form needs the flag explicit.

---

## 31. `grep -cE PATTERN file` counts matching LINES, not match occurrences

**Symptom:** a verifier requires "≥5 markdown links in the brief" and counts via `grep -cE '\[[^]]+\]\([^)]+\)' brief.md`. Oracle's brief actually has 5 links but the count comes back as 3 (or however many lines contain at least one link). Verifier fails legitimate output.

**Cause:** `grep -c` is line-oriented — multiple matches on the same line collapse to 1.

**Fix:** `grep -oE PATTERN file | wc -l` (extract each match on its own line, then count). Or `awk` with explicit per-match handling.

```bash
# wrong (counts lines)
n=$(grep -cE '\[[^]]+\]\([^)]+\)' "$BRIEF")

# right (counts matches)
n=$(grep -oE '\[[^]]+\]\([^)]+\)' "$BRIEF" | wc -l)
```

---

## 32. JobConfig YAML `environment.env` does NOT reach the trial container — only task.toml's `[environment.env]` does

**Symptom:** Every trial in the Track A sweep fails with `FailoverError: Unknown model: xrouter/...`. A verifier-side env probe inside the container shows `OPENROUTER_API_KEY_LEN=0` even though `configs/track-a-harness.yaml` has the keys declared:
```yaml
environment:
  env:
    - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
```
and the harbor process env (from infisical) clearly has them.

**Cause:** Harbor's per-trial `EnvironmentConfig` is built from each **task.toml's** `[environment]` block, not from the YAML's top-level `environment:`. `resolve_env_vars()` runs against `task_env_config.env` only. The YAML-level env is used for compose-mode infrastructure variables (e.g. service env in docker-compose.yaml overlays), NOT propagated into the agent container.

**Fix:** Add the keys to **each task.toml's** `[environment.env]` block:
```toml
[environment.env]
OPENROUTER_API_KEY = "${OPENROUTER_API_KEY}"
```
For multi-step tasks that only have a top-level `[environment]` section (no `[environment.env]` yet), add the block before the next `[agent]` / `[verifier]` section. Verifier env stays in `[verifier.env]` separately.

**Diagnostic pattern:** add `echo "OPENROUTER_API_KEY_LEN=${#OPENROUTER_API_KEY}" >&2` to a task's `tests/test.sh` and run as oracle. stderr captures what reaches the container.

Affected all 48 task.tomls; bulk-patched 2026-05-30.

---

## 33. `lib/openclaw_thin.py` mis-added a duplicate `--agent main` → openclaw 2026.5.26 fails with "Unknown model"

**Symptom:** "FailoverError: Unknown model: xrouter/deepseek/deepseek-v4-pro" from openclaw even after the env-propagation fix. The command line in the trial log shows `openclaw agent --local --json --agent main --agent main --thinking high --model ...` — the duplicate flag.

**Cause:** `build_cli_flags()` (from `harbor.agents.installed.openclaw.OpenClaw.CLI_FLAGS`) already emits `--agent main` (it's the default of the `openclaw_agent_id` CliFlag). An interim adapter edit added a second `--agent main` thinking the first was missing. Two flags → openclaw 2026.5.26 parser silently mis-parses → reports "Unknown model" rather than "duplicate arg".

**Fix:** never add `--agent` manually in the thin adapter — rely entirely on `cli_flags_arg = self.build_cli_flags()`. Clean command shape: `openclaw agent --local --json --agent main --thinking high --model xrouter/...` (one `--agent`).

**Sanity probe** (manual docker run, confirms the clean command works):
```bash
docker run --rm -e OPENROUTER_API_KEY="$OPENROUTER_API_KEY" harbor-agents-rich:latest bash -c '
    . ~/.nvm/nvm.sh && nvm use 22
    openclaw agent --local --json --agent main --thinking high \
        --model xrouter/deepseek/deepseek-v4-pro --message "say hi in 3 words"
' 2>&1 | tail -5
# Returns: completion stage with finishReason=stop
```

---

## 34. `allow_internet = false` in task.toml silently breaks any task whose AGENT needs LLM connectivity

**Symptom:** openclaw error `FailoverError: Unknown model: xrouter/deepseek/deepseek-v4-pro`. The model IS registered, the API key IS reaching the container (verified via in-container env probe = 73 chars), and the same openclaw command run via a fresh `docker run --rm` works fine. But Harbor-spawned trials all fail.

**Cause:** Harbor enforces task-level network isolation. When `task.toml` has `[environment] allow_internet = false`, Harbor adds `docker-compose-no-network.yaml` (which sets `network_mode: none`) to the compose stack. The agent container literally has no network connection. openclaw tries to call `https://openrouter.ai/...`, the request fails, and openclaw's error formatter labels this as "Unknown model" rather than reporting the network failure.

**Diagnostic pattern:** if openclaw says "Unknown model" but the env is verified correct:
```bash
# Inside the running trial container:
curl -s -o /dev/null -w "%{http_code}\n" https://openrouter.ai/api/v1/models
# Returns "000" (could not connect) → confirmed network-isolated
# Returns "200" → not a network issue, look elsewhere
```

**Fix:** set `allow_internet = true` in any task whose agent uses a hosted LLM. Most existing tasks already have this. Newly authored shapes should default to `true` unless the task EXPLICITLY tests offline behavior. Bulk-fixed all 48 task.tomls 2026-05-30.

**Side note:** since `allow_internet = true` removes the no-network override, agents can now also reach the recall/hindsight/honcho memory backends on `internal-host` — this is intended for memory-using tasks.

---

## 35. Task Dockerfiles `FROM harbor-agents-prebaked` miss the baked openclaw + persona config in `harbor-agents-rich`

**Symptom:** every openclaw trial in the Track A sweep dies with `FailoverError: Unknown model: xrouter/deepseek/deepseek-v4-pro` — even though:
- The harbor-agents-rich image has the baked openclaw.json with the `xrouter` custom provider
- The OPENROUTER_API_KEY reaches the trial container (probe: 73 chars)
- The container has internet (curl openrouter → 200)
- The openclaw command line is exactly what works under a manual `docker run`

**Root cause:** task Dockerfiles use `FROM harbor-agents-prebaked:latest` — that's the **base** image with just openclaw + nvm. The **rich** image (`harbor-agents-rich:latest`) is built ON TOP of prebaked and adds the baked openclaw.json (with xrouter), the workspace files at `/opt/harness/openclaw-workspace/`, hermes config, etc. Tasks built from prebaked never see those.

**Diagnostic that nailed it (in-container probe via the adapter):**
```bash
# Before openclaw runs, inside the trial container:
ls /root/.openclaw/
# Expected (rich):    drwx... plugins  -rw... openclaw.json  drwx... logs
# Observed (prebaked):drwx... plugins   ← no openclaw.json
openclaw models list
# Expected: shows xrouter/deepseek/deepseek-v4-pro
# Observed: only built-in models (openai/gpt-5.5, claude-cli/*)
```

When openclaw runs without a usable config, it bootstraps a DEFAULT agent dir at `/root/.openclaw/agents/main/agent/models.json` containing only the built-in `openrouter` provider — not our `xrouter`. So `xrouter/deepseek/deepseek-v4-pro` resolves to nothing → "Unknown model".

**Fix:** all task Dockerfiles must `FROM harbor-agents-rich:latest`, not `prebaked`. Bulk-patched 47 of 48 task Dockerfiles 2026-05-30. Re-run with `--force-build` so Harbor doesn't cache the prebaked-based image.

**Long-term:** add a CI check that `grep -L 'FROM harbor-agents-rich' tasks/*/*/environment/Dockerfile` returns empty.

---

## Note on prior diagnoses (#32, #33, #34)

While investigating #35, I cycled through three earlier hypotheses that turned out to be wrong or only contributing:
- #32 (YAML env not propagating) → real signal, but adding env to task.toml didn't fix the model resolution (env was reaching the container fine, openclaw just had no config to use it with).
- #33 (duplicate `--agent main`) → MY error in an interim adapter edit; reverted. Not a real bug.
- #34 (`allow_internet=false`) → real issue for memory-using tasks but not the openclaw crash; the trial config showed `allow_internet=true` AND the network probe to OpenRouter returned 200 BEFORE openclaw failed.

---

## 36. `infisical-identity.env` uses bare assignments (no `export`) — `source` alone doesn't reach child scripts

**Symptom:** `tools/run_track_a.sh` dies immediately with `INFISICAL_CLIENT_ID: set INFISICAL_CLIENT_ID via ~/.config/infisical/infisical-identity.env` — even though you just ran `source ~/.config/infisical/infisical-identity.env` in the same command.

**Root cause:** `~/.config/infisical/infisical-identity.env` defines `INFISICAL_CLIENT_ID=...` etc. as **bare assignments without `export`**. Sourcing makes them shell variables in the current shell, but they are NOT exported, so the child process (`run_track_a.sh`) doesn't inherit them. The `: "${INFISICAL_CLIENT_ID:?...}"` guard inside the script then fails.

**Fix:** wrap the source in auto-export: `set -a && source ~/.config/infisical/infisical-identity.env && set +a`. `set -a` marks every subsequently-assigned variable for export. (Do NOT `cat`/`grep` the file to "fix" it — that risks leaking secret values to context. Leave the file as-is; just auto-export at source time.) Verified the file holds exactly 3 keys (INFISICAL_CLIENT_ID / _CLIENT_SECRET / _SITE_URL) via shape-only `grep -oE '^[A-Za-z_]+=' | sed 's/=$//'` (key names only, no values).

---

## 37. `wipe_memory_state` hook crashes with `'NoneType' object has no attribute 'lower'` — AgentConfig.name is None for import_path agents

**Symptom:** the very first `TrialEvent.START` aborts the whole sweep:
```
File ".../hooks/wipe_memory_state.py", line 58, in _resolve_group
    key = agent_name.lower().replace("-", "").replace("_", "")
AttributeError: 'NoneType' object has no attribute 'lower'
```

**Root cause:** Track A's YAML defines each agent by `import_path` + `model_name` only — no explicit `name`. Harbor's `AgentConfig.set_default_name` validator only falls back to `ORACLE` when BOTH `name` and `import_path` are None; with `import_path` set, `name` stays `None`. The hook read `event.config.agent.name` (None) and passed it straight into `.lower()`.

**Fix:** derive the agent identity from `import_path` when `name` is None — `"lib.openclaw_thin:OpenClawThin".rsplit(":",1)[-1]` → `"OpenClawThin"` → normalized `"openclawthin"`, which is already a `GROUP_MAP` key. Also made `_resolve_group` null-safe (returns None for falsy input). Both `OpenClawThin`→`eval-openclaw` and `HermesThin`→`eval-hermes` verified.

**Related wipe bugs found + fixed (2026-05-31, while the smoke ran):**
- **honcho 409:** `DELETE /v3/workspaces/{id}` 409s with "active session(s) remain" — it never wiped anything. Fix: empty the workspace *in place* — page `conclusions/list` + `sessions/list` and DELETE each; do NOT delete the workspace (avoids a recreate race). Verified: seeded session 1→0.
- **hindsight 405 silent no-op:** the old `_wipe_hindsight` DELETEd `/memories /entities /mental-models /directives /documents`, but only `/memories` supports DELETE — the other four are GET/POST-only and returned **405**, which the code *tolerated*, so entities/mental-models/directives/documents leaked across trials. Fix: bulk `DELETE /memories` + `DELETE /observations` (both exist), then list+per-id-delete `mental-models`/`directives`/`documents`. Bank shell + eval entity-type config (task #59) preserved. Verified: 1→0.

**DATA-SAFETY hardening (operator-requested — recall/honcho are shared with real agents):**
- recall, honcho, hindsight ALL share their backend with production agents (recall-neo4j holds prod groups `juliet`/`yui`/`akane`; both `recall-mcp` and `recall-mcp-eval` point at the same neo4j, isolated only by `group_id`).
- The wipe targets are **exact-match** (`eval-openclaw`/`eval-hermes`), never wildcards, so they physically cannot match prod groups. Confirmed eval recall writes land in `eval-openclaw`/`eval-hermes` via the `X-Group-ID` header in `harnesses/openclaw/openclaw.json` + `harnesses/hermes/config.yaml` (the MCP's `GRAPHITI_GROUP_ID=eval-default` is only a no-header fallback).
- Added `_assert_eval_scope(id)` — every destructive call raises `ValueError` unless `id` starts with `eval-`. Verified it rejects `juliet`/`yui`/`akane`/`''`/`None`/`prod-default` and accepts only `eval-*`. So even a future GROUP_MAP typo cannot wipe prod. gather() exceptions are now logged (no silent guard trips).
- **NOTE:** these fixes landed AFTER the running n=1 smoke imported the hook, so the smoke still uses the old (contaminating) wipe — fine for grid/plumbing validation. The fixed hook is picked up by the next launch (the n=5 real run), where memory-axis fidelity matters.

Keeping all four entries because each chase produced a real lesson about Harbor's env / network / config-propagation paths.

---

## 38. Harbor rejects non-scalar reward values — `reward.json` must be a flat dict of float/int

**Symptom:** a task's trials all error with no reward:
```
ValidationError: 2 validation errors for VerifierResult
rewards.per_file.float  Input should be a valid number [input_value={...dict...}]
rewards.per_file.int    Input should be a valid integer [input_value={...dict...}]
```

**Root cause:** Harbor's `VerifierResult.rewards` is typed `dict[str, float|int]` — **every value must be a scalar.** A verifier that writes a rich debug structure (`"per_file": {…nested…}`, `"checks": {k:v}`, `"done_slot": [a,b]`) into `/logs/verifier/reward.json` passes its own bash/python logic but fails Harbor's schema at result-collection time — so the trial errors AFTER doing all the work. Bit 6 subagent-authored verifiers at once (they each added a nested per-item breakdown).

**Fix:** emit ONLY scalar fields. Keep `reward`, `correctness`, and flat scalar counts (`matched`, `found`, `recalled`, …); drop any dict/list value. If you want per-item detail, flatten it (`item1_ok`, `item2_ok`) or write it to a *separate* file the verifier doesn't return.

**Lesson:** local oracle-validation (run solve.sh + test.sh, eyeball reward.json) does NOT catch this — only Harbor's Pydantic layer does. After authoring a verifier, grep its emission for `"key": {` / `"key": [` before trusting it. A cheap n=1 trial is the real validator (this is exactly what the focused n=1 caught).

**Update 2026-05-31 — the LIST-valued variant.** The first sweep fixed nested-*dict* keys; the focused n=1 baseline then caught a second instance the dict-only grep missed: `skill-discovery-and-use-01` emitted `"skill_runs_logged": sorted(ran_files)` — a *list*, not a dict — and died with the same `ValidationError` (reward=None) on **both** harnesses. Fix: emit the scalar `len(ran_files)`. So the audit grep must catch **both** `"key": {` AND `"key": [` (plus `sorted(`/`list(`/`.split(`/`.keys()` value expressions). Any reward-dict value that isn't a bare float/int — dict OR list — fails the schema.

---

## 39. `/tmp` is tmpfs (RAM) on these boxes — never persist job results there; pin `jobs_dir` to an absolute path

**Symptom:** expensive run results (a $13 sweep) silently at risk of vanishing; also runs scattered between `/tmp/harbor-jobs` and `<repo>/jobs` so the post-run report + dashboard couldn't find them.

**Root cause (two parts):**
1. `/tmp` on landon is **tmpfs** (`findmnt -no FSTYPE /tmp` → `tmpfs`, 31G RAM-backed) — wiped on reboot AND consuming RAM. 142M of trajectory data lived there.
2. Harbor's `JobConfig.jobs_dir` defaults to `Path("jobs")` — **CWD-relative**, not absolute. So where output lands depends on the launch CWD, and the wrapper's separate `JOBS_DIR` (for the post-report) defaulted to `/tmp/harbor-jobs`, diverging from where Harbor actually wrote.

**Fix:** pin `jobs_dir` to an ABSOLUTE persistent path. `run_track_a.sh` now sets `JOBS_DIR="${REPO}/jobs"` AND passes it into the JobConfig (`raw["jobs_dir"]`), so Harbor + the report + the dashboard all agree. `harbor-tasks/jobs/` is on the encrypted `/home` (327G) and is gitignored (`.gitignore:7`) — persists without bloating the repo. Moved all 84 existing runs there.

---

## 40. `harbor view` dashboard is a foreground process — it dies silently; runs on a chosen port over the jobs folder

**Symptom:** "the dashboard isn't loading anymore." No error — the process just wasn't running.

**Notes:**
- `harbor view <folder> --port <P> --host 0.0.0.0 [--no-build]` starts a uvicorn server browsing job dirs. It is NOT a daemon — it dies when its shell/session ends or on reboot, and does not auto-restart.
- `--no-build` reuses prebuilt static viewer files (fast); drop it / use `--build` only if the viewer assets are missing.
- It does **not** follow symlinks in the jobs folder — symlinking run dirs in makes them invisible (and briefly broke the listing). Use real dirs (move, don't link).
- `/api/jobs` returns `{"items":[...]}` (not a bare list); a brief "0 items" right after startup is just the initial scan, not a failure.
- The viewer points at ONE folder — keep all runs under the single pinned `jobs_dir` (see #39) so one dashboard shows everything.

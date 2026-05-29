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

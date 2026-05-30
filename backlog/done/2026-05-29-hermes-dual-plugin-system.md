# Hermes plugin activation: two independent systems (RESEARCH 2026-05-29)

**Status:** investigation + dashboard implementation shipped.
**Related:** `FOOTGUNS.md` #20, `tools/agent_status.py`,
`backlog/done/2026-05-29-agent-status-dashboard.md`.

## TL;DR

`hermes plugins list` returns `0 enabled / 61` on a fresh image — but
`memory/honcho` **is** loaded and actively serving the agent's memory tools.
That's not a bug. hermes has two completely independent plugin activation
systems and the CLI command only reports one of them. Any tooling that wants
to know what's *really* active must compute the union from both.

## System 1 — `plugins.enabled` allow-list

- **Source of truth:** `~/.hermes/config.yaml` keys `plugins.enabled` and
  `plugins.disabled`.
- **Default:** `None` ⇒ opt-in default ⇒ nothing enabled. Verbatim source
  comment: `# None = opt-in default (nothing enabled)`.
- **What it gates:** user-installed plugins via `hermes plugins install
  <git-url>`, plus anything dropped into `$HERMES_HOME/plugins/`. Bundled
  System-2 categories (memory, context_engine, …) are NOT gated by this
  allow-list.
- **CLI surface:** `hermes plugins list` (and `enable`, `disable`,
  `install`, `remove`).
- **Code:** `/usr/local/lib/hermes-agent/hermes_cli/plugins.py` —
  `_get_enabled_plugins()` reads the config; the CLI list iterates installed +
  bundled plugins and reports `enabled` only when this allow-list contains the
  plugin name.

## System 2 — direct config-driven import (the bypass)

- **Source of truth:** category-specific config keys, applied during agent
  initialization.
- **What it gates:** bundled plugins that are loaded by direct Python import in
  `agent_init.py` (and a few other entry points). These bypass the allow-list
  entirely.
- **CLI surface:** none. `hermes plugins list` is blind to System 2 — for
  example, `grep -i honcho` against its output returns nothing even when
  `memory.provider: honcho` is set.
- **Code:** `/usr/local/lib/hermes-agent/agent/agent_init.py` —
  `from plugins.memory import load_memory_provider as _load_mem; _load_mem(
  config.memory.provider)`. Same pattern for `from plugins.context_engine
  import load_context_engine; load_context_engine(name)` and other
  category-specific loaders.

### Known System-2 mappings (verified)

| Category | Config key | Default | Notes |
|---|---|---|---|
| `memory` | `memory.provider` | none (built-in file memory only) | Only one provider active at a time. Verified loads via `plugins/memory/<name>/__init__.py`. |
| `context_engine` | `agent.context.engine` | `"compressor"` (hardcoded built-in, NOT a plugin) | The default `compressor` is a built-in `ContextCompressor`, not a swappable plugin (no `plugin.yaml`). A real-plugin override would be e.g. `agent.context.engine: my-engine` with `plugins/context_engine/my-engine/`. |

### Suspected (NOT yet verified) System-2 mappings

These categories live in `plugins/` and appear to be loaded outside the
allow-list, but I haven't traced the exact config key yet:

| Category | Likely config key | Why suspected |
|---|---|---|
| `model-providers` | `model.provider` and/or model-string prefix matching | Dir has hyphen (`model-providers`) so it can't be `from plugins.model-providers import …` directly. Likely auto-discovered via `importlib`. |
| `browser` | `browser_provider` or a registry pattern | `agent/browser_provider.py` + `agent/browser_registry.py` use `register_browser_provider` / `get_active_browser_provider`. |
| `teams_pipeline` | gateway runtime binding | `from plugins.teams_pipeline.runtime import bind_gateway_runtime` in `gateway/run.py`. |
| `kanban`, `dashboard_auth`, `image_gen`, `observability`, `platforms`, `security-guidance`, `spotify`, `video_gen`, `web`, `disk-cleanup`, `google_meet`, `hermes-achievements`, `example-dashboard` | various | TBD — when each is actually wanted, trace the loader. |

Add a row to the table whenever a new mapping is verified by reading the
hermes source.

## The misleading numbers, side-by-side

| View | Count | What it actually measures |
|---|---|---|
| `hermes plugins list` rows | 61 | Plugins tracked by System 1 (allow-list). EXCLUDES memory + context_engine + several other System-2 categories. |
| `/usr/local/lib/hermes-agent/plugins/<cat>/<name>/` dirs with `plugin.yaml` | 69 | Canonical bundled plugin set. |
| `hermes plugins list` "enabled" | 0 | What System 1 says is on. On a fresh image, always 0 unless the user has run `hermes plugins enable …`. |
| Real loaded plugins | ≥1 | Whatever System 1 enabled (0 here) PLUS whatever System 2 selected via config (in our rich image: `memory/honcho`). |

## Computing the real activation set (the algorithm)

```python
# Inputs available to the introspection:
#   hc            = parsed ~/.hermes/config.yaml dict
#   cli_status    = {plugin_full_name: "enabled" | "not enabled" | ...} from `hermes plugins list`
#   bundled       = list of (category, name, dir) from a filesystem walk of plugins/

# 1. System 1 allow-list set
enabled_allow = set(((hc.get('plugins') or {}).get('enabled') or []))

# 2. System 2 set — one entry per known bypass category
cat_getters = {
    'memory':         lambda c: (c.get('memory') or {}).get('provider'),
    'context_engine': lambda c: (((c.get('agent') or {}).get('context') or {})
                                 .get('engine')) or 'compressor',
}
cfg_active = {}
for cat, fn in cat_getters.items():
    v = fn(hc)
    if v:
        cfg_active.setdefault(cat, set()).add(v)

# 3. Plugin is active iff it's in either set AND a plugin.yaml exists on disk.
for cat, name, dpath in bundled:
    full = f"{cat}/{name}" if cat else name
    s1 = (cli_status.get(full) == 'enabled') or (full in enabled_allow) or (name in enabled_allow)
    s2 = (cat in cfg_active and name in cfg_active[cat])
    active = bool(s1 or s2)
```

Implemented verbatim in `tools/agent_status.py` (see the
`# ---------- hermes plugins: dual-system activation ----------` block).
Adding a new bypass mapping is one line in `cat_getters`.

## Why the dashboard surfaces this distinction

Operator request 2026-05-29: distinguish "active / enabled" from "just present /
available" for plugins (and skills). Without the union approach the dashboard
shows `0 enabled` for hermes plugins on a config where honcho is provably
running — confusing and wrong-looking. With the union approach:

- Section header reads `1 active / 69 bundled`.
- `memory/honcho` is the only green chip in the hermes plugins section.
- Clicking it opens a modal that prepends an activation banner:

  ```
  # Activation: ACTIVE
  # Via: config: memory.provider
  # `hermes plugins list` status: (not tracked by System 1)
  # ------------------------------------------------------------
  name: honcho
  …
  ```

- Flipping `memory.provider: honcho` → `memory.provider: mem0` and regenerating
  the dashboard would flip `memory/honcho` to grey and turn `memory/mem0`
  green — fully dynamic, no hand-edits.

## Open work

- Verify the `model-providers`, `browser`, `teams_pipeline` mappings and add
  them to `cat_getters` (probably during task #54 browser/CDP work).
- Note in the dashboard when a config selects a value that does NOT correspond
  to a real `plugin.yaml` on disk (e.g. `agent.context.engine: compressor` is a
  built-in, not a plugin — currently no chip; that's correct but easy to
  misread as a missing plugin).

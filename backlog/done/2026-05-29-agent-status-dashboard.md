# `tools/agent_status.py` — eval harness status dashboard (SHIPPED 2026-05-29)

**Epic:** E5 — Observability & reporting
**Status:** shipped, single-file output (`agent-status.html`).
**Companion:** `tools/README.md`,
`backlog/done/2026-05-29-hermes-dual-plugin-system.md`, FOOTGUNS #20.

## Purpose

Give the operator a "super-duper basic" one-glance view of what each rich-image
harness is configured with — model, reasoning, persona, skills, plugins, MCP
servers, memory wiring — without grepping through configs or running CLIs by
hand. Re-runnable; the data is always live.

## Design constraints (from the operator)

- **Visual.** A single page is fine; no app, no server, no React. Open it from
  disk and read it.
- **Accurate.** No hand-typed data. Anything shown must be derivable from the
  image or the running services.
- **Honest active/available distinction.** A green chip means "in use," a grey
  chip means "shipped but not loaded." For hermes this required understanding
  the dual plugin activation system (see the companion doc).
- **Dynamic.** Re-running the generator after a config change must reflect the
  change. No hardcoded "honcho is active." Active state comes from reading the
  current config.
- **Self-contained.** The output HTML must work from `file://` — no fetches.
- **Click-through.** Each persona, config, skill, and plugin chip opens a modal
  with its full file contents and (when applicable) a GitHub deep-link.

## Architecture

```
                    <dev-host>
   ┌──────────────────────────────────────────────────┐
   │  python3 tools/agent_status.py                   │
   │                                                  │
   │   1) docker run --rm harbor-agents-rich          │
   │      └─ inline python introspection script       │
   │         (reads configs, runs `openclaw skills    │
   │         check`, `openclaw plugins list --json`,  │
   │         `hermes skills list`, `hermes plugins    │
   │         list`, walks /usr/local/lib/hermes-      │
   │         agent/plugins/, reads SKILL.md + plugin  │
   │         .yaml file contents).                    │
   │         emits ONE JSON blob to stdout.           │
   │                                                  │
   │   2) urllib pings memory services on <memory-host>.      │
   │                                                  │
   │   3) python templating → agent-status.html       │
   │      (inline CSS + JS, embeds all file content   │
   │      in a `const FILES = {…}` script var).       │
   └──────────────────────────────────────────────────┘
                            │
                            ▼
                  agent-status.html
            (open in browser; click chips)
```

## Data sources

| Section | CLI / file | Notes |
|---|---|---|
| openclaw model, reasoning, MCP | `/root/.openclaw/openclaw.json` | parsed as JSON |
| openclaw skills (active vs not) | `openclaw skills check` | 4 sections parsed: Ready/Missing/Disabled/Blocked. Active = "Ready and visible to model". |
| openclaw plugins | `openclaw plugins list --json` | per-plugin `enabled` bool. Single source — openclaw doesn't have the dual-system problem. |
| openclaw persona files | `/opt/harness/openclaw-workspace/*.md` | embedded full content |
| hermes model, reasoning, mem provider, MCP | `/root/.hermes/config.yaml` (yaml-parsed via hermes venv) | |
| hermes skills (active vs not) | `hermes skills list` (rich table parsed) | active = Status column == `enabled` |
| **hermes plugins** | **filesystem walk of `/usr/local/lib/hermes-agent/plugins/<cat>/<name>/`** + `hermes plugins list` (rich table) + `config.yaml` config-driven keys | **dual-system computation; see FOOTGUNS #20** |
| hermes persona | `/root/.hermes/SOUL.md` | |
| Memory service health | HTTPS pings from <dev-host>: `http://internal-host:{8407,8888,8000}/health` | colored dots in the legend |

## Dual-system activation (hermes plugins)

The hardest part. See the companion doc for the full investigation. Algorithm
in code:

```python
cat_getters = {
    'memory':         lambda c: (c.get('memory') or {}).get('provider'),
    'context_engine': lambda c: (((c.get('agent') or {}).get('context') or {})
                                 .get('engine')) or 'compressor',
    # ← add new bypass mappings as discovered in agent_init.py
}

# For each bundled plugin dir on disk:
s1 = (cli_status[full] == 'enabled') or (full in enabled_allow_list)
s2 = (category in cfg_active and name in cfg_active[category])
active = s1 or s2
```

This is the single hot spot for keeping the dashboard accurate as we trace
more of hermes's loading paths. Each new entry takes one line.

## Embedding gotchas (already shipped fixes)

| Symptom | Cause | Fix |
|---|---|---|
| `Invalid or unexpected token` in console | Some SKILL.md contains a literal `</script>` (e.g. the `p5js` skill), which closes the embedding `<script>` tag prematurely | `json.dumps(...).replace("</", "<\\/")` — JSON accepts `\/` for `/`; HTML tokenizer stops matching `</script>`. |
| Modal showed on page load empty | Base CSS for `#mo` was `display: flex` instead of `display: none` | Changed base to `display:none`; show toggles to `flex` |
| `python3 tools/agent_status.py` SyntaxError on the parse_rich_table docstring | The introspection block is `r"""…"""`; a triple-quoted docstring inside the embedded python closes the outer raw string early | Use `# comment` not `"""docstring"""` inside `_INTROSPECT` |
| python3.12 (system) doesn't have pyyaml (FOOTGUNS #14) | hermes config is YAML | Parse it inside the container using the hermes venv python (`/usr/local/lib/hermes-agent/venv/bin/python`) which has yaml |
| The hermes venv has no pip (FOOTGUNS #19) | uv-managed venv without pip | Install plugin deps via `uv pip install --python /usr/local/lib/hermes-agent/venv/bin/python …` |

## Output size

Currently ~1.4 MB. Drivers:
- 57 openclaw skill SKILL.md files embedded
- 85 hermes skill SKILL.md files embedded
- 46 openclaw plugin manifests (`openclaw.plugin.json` / `package.json`)
- 69 hermes plugin.yaml files
- 7 persona files
- 3 configs (incl. the full 60 KB hermes `config.yaml`)

Total: 117+ files, each capped at 80 KB. The page loads instantly in modern
browsers. If size becomes a problem (mobile?), lazy-loading file content on
first click is a one-line refactor (fetch via XHR vs embed).

## Extension points

| Hook | Where | Note |
|---|---|---|
| Add a new hermes System-2 mapping | `_INTROSPECT` → `cat_getters` dict | one line; reads live config |
| Add a per-skill status flavor | `count_active` / `chips_for` + CSS `.chip.skill.<flavor>` | currently active/inactive; could add "missing-deps", "disabled-by-user", … |
| Switch to lazy file loading | `files_js` builder + `showFile` JS | drop full content from embed; fetch on click via `text/plain` data URL or sidecar JSON |
| Add a new harness (third agent) | rename `AGENT_*` constants from `oc`/`hm` to a dict; thread through render | hour-of-work refactor; not needed yet |
| Snapshot the live page | `tools/agent_status.py --open` writes the file; pair with a cron / git hook | currently manual |

## Reproducer

```bash
cd ~/harbor-tasks
python3 tools/agent_status.py            # writes agent-status.html
python3 tools/agent_status.py --open     # also opens in default browser
# open the file directly:
xdg-open agent-status.html
```

Re-run after any of these and the dashboard reflects the change:
- editing a baked persona/config file in `harnesses/` and rebuilding the image,
- flipping `memory.provider:` or `agent.context.engine:` in `harnesses/hermes/config.yaml`,
- adding a plugin to `plugins.enabled` in the hermes config,
- starting/stopping a memory service on <memory-host>.

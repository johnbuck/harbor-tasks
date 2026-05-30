# `tools/` — operator utilities

Standalone scripts for inspecting / refreshing the eval setup. Stdlib-only
where possible; runs on landon's system python (or whatever python3 is on
PATH).

## Scripts

### `agent_status.py` — eval harness status dashboard

Generates a single-file HTML dashboard of the current state of both rich-image
harnesses: model, reasoning, persona/identity files, active vs. available
skills + plugins (color-coded), MCP servers, and memory-service health.

```bash
python3 tools/agent_status.py            # writes agent-status.html
python3 tools/agent_status.py --open     # also opens it in the browser
```

**Live data, regenerable.** The script:
1. `docker run`s `harbor-agents-rich:latest` once and introspects: configs,
   `openclaw skills check`, `openclaw plugins list --json`,
   `hermes skills list`, `hermes plugins list`, a filesystem walk of
   `/usr/local/lib/hermes-agent/plugins/`, and the full contents of every
   persona/SKILL.md/plugin.yaml/config.
2. Pings `recall:8407 / hindsight:8888 / honcho:8000` on wiley from landon.
3. Templates everything into a self-contained ~1.4 MB `agent-status.html`
   with inline CSS + JS and embedded file contents (works opened from
   `file://`).

Click any chip (persona file, config, skill, plugin) → modal viewer with the
full file contents + a "View on GitHub" deep-link when the source location is
known.

**Hermes plugin activation is dual-system aware.** See FOOTGUNS #20 and
[`backlog/done/2026-05-29-hermes-dual-plugin-system.md`](../backlog/done/2026-05-29-hermes-dual-plugin-system.md)
for why. The single hot spot for adding a new bypass-category mapping is the
`cat_getters` dict inside the `_INTROSPECT` block — one line per category.

Full design + extension points:
[`backlog/done/2026-05-29-agent-status-dashboard.md`](../backlog/done/2026-05-29-agent-status-dashboard.md).

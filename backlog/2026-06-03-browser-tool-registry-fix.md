# Browser tool enablement — stale plugin registry (the real #90 fix)

**Epic:** E3 — Capability infrastructure (memory + browser)
**Status:** IMPLEMENTED 2026-06-03
**Date:** 2026-06-03
**Origin / triggered-by:** #90 — openclaw's `browser` tool never surfaced in the agent's
tool catalog at runtime, even with `browser.enabled: true` baked. This spec records the
**actual** root cause and fix, which supersedes the two earlier theories
(CDP-unreachable; embedded-vs-gateway — see `2026-06-03-gateway-backed-full-harness.md`,
now REJECTED).

## Problem

`browser.enabled: true` + `browser.cdpUrl` were baked into `openclaw.json`, yet the `browser`
tool was absent from the agent's tool catalog every run. `openclaw plugins inspect browser` →
"Plugin not found". CDP reachability was a red herring (curl to `internal-host:9222`
from inside the trial container returns Chrome 148). The embedded-vs-gateway theory was also
wrong (proven below).

## Root cause (verified in-container, 2026-06-03)

The rich image shipped a **stale persisted plugin registry** at `/root/.openclaw/plugins`.
openclaw caches a `source: "persisted"` plugin registry; the baked one had only **46** plugins
indexed (providers + `memory-core`) — it was built before the `browser` plugin's runtime deps
(`playwright-core`, `express`, `ws`, `@modelcontextprotocol/sdk`) were in place, so discovery
skipped `dist/extensions/browser/` and never indexed it. The `browser` plugin registers its
tool unconditionally (`registerBrowserPlugin` → `api.registerTool(createLazyBrowserTool(...))`)
— but only **if the plugin is in the registry**. It wasn't, so the tool never registered.

`openclaw plugins registry --refresh` rebuilds the registry from current manifests: **46 → 64
enabled** (91 total indexed). After refresh, `browser` (plus `canvas`, `file-transfer`,
`phone-control`, `talk-voice`) appear, and the `browser` tool surfaces in the agent catalog.

### The embedded-vs-gateway theory was disproven

The prior spec claimed thin `openclaw agent --local` runs EMBEDDED, dropping the gateway's
"browser control server" → no browser tool. Four in-container experiments (real model turns,
key injected via Infisical, never printed):

| Run | `browser` in catalog? | tool count |
|---|---|---|
| Gateway-backed, stale registry | ❌ | 53 |
| Gateway-backed, registry refreshed | ✅ | 59 |
| Embedded `--local`, stale registry (= all prior runs) | ❌ | ~46 |
| **Embedded `--local`, registry refreshed** | ✅ | 59 |

Conclusion: the registry was the sole blocker. After refresh, **embedded `--local` exposes the
identical 59-tool catalog as gateway-backed** — browser, the full hindsight memory suite,
`sessions_spawn`/`subagents`, 14 skills. Embedded is not a reduced runtime for anything the
core-11 exercises. The gateway adds only channels / cron / device-pairing / multi-session
routing / sidecars — none of which the eval tasks touch.

## Fix (shipped)

One step baked into `environments/agent-rich/Dockerfile`, right after `openclaw.json` is copied:

```dockerfile
RUN . ~/.nvm/nvm.sh && nvm use 22 >/dev/null 2>&1 \
    && openclaw plugins registry --refresh >/dev/null 2>&1 \
    && openclaw plugins list --json 2>/dev/null | grep -q '"browser"' \
    && echo "browser plugin indexed OK"
```

The registry persists into the image layer, so every trial boots with a fresh registry — no
per-trial refresh, no runtime cost. The `grep '"browser"'` assertion fail-fasts the build if a
future base-image change drops the plugin again. The adapter (`lib/openclaw_thin.py`) is
**unchanged** — it keeps running `openclaw agent --local`.

## Design decisions

- **Keep embedded `--local`** (operator decision 2026-06-03): browser + memory + the full
  catalog all present; no gateway lifecycle / port-collision / teardown risk; proven fair.
- **Bake the refresh, don't refresh per-trial**: the registry is HOME-state that persists in
  the image layer; baking it is free at runtime and deterministic.
- **Assert at build time**: a stale base image silently dropping browser again is exactly the
  failure we just spent a session diagnosing — fail the build instead.

## Acceptance criteria

- [x] Baked image ships `source: persisted` registry with `browser` indexed, no runtime refresh.
- [x] Embedded `openclaw agent --local` exposes the `browser` tool in the catalog.
- [x] `browser-find-fact-01` → `browser_used=1` + correct answer for openclaw (live e2e:
      reward 1.0, browser_tool_calls=24, answer correct, no decoy).
- [x] hermes `browser_navigate` parity verified end-to-end (live e2e: reward 1.0,
      browser_tool_calls=69 across navigate/snapshot/click, answer correct, no decoy).
- [x] Re-baseline browser-dependent tasks: `browser-find-fact-01` is the only one; both
      harnesses 1.0 → "BLUNT" (it's a capability check, not a discriminator). The rest of the
      catalog never lacked its tools, so no further re-baseline is needed for the browser fix.

## Result (live e2e, `configs/browser-e2e.yaml`, n=1 each, 2026-06-03)

| Harness | reward | browser_used | browser_tool_calls | answer |
|---|---|---|---|---|
| openclaw | 1.0 | 1 | 24 (`browser`) | correct, no decoy |
| hermes | 1.0 | 1 | 69 (`browser_navigate`/`snapshot`/`click`) | correct, no decoy |

Both rendered the JS page, paginated to page 3, and returned the site's "Jim Henson"
attribution. The `browser_used` gate guarantees a real browse, not the memorization shortcut.

## Pointers

- Fix: `environments/agent-rich/Dockerfile` (registry-refresh RUN + assertion).
- Adapter (unchanged): `lib/openclaw_thin.py`.
- Disproven theory: `2026-06-03-gateway-backed-full-harness.md` (REJECTED).
- Browser task + e2e: `tasks/tool-orchestration/browser-find-fact-01/`, `configs/browser-e2e.yaml`.
- Discovery internals: `dist/discovery-DHnXdmOi.js` (manifest scan); the persisted registry
  lives under `/root/.openclaw/plugins`.

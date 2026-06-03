# Self-contained in-container browser (no cross-machine CDP)

**Epic:** E3 — Capability infrastructure (memory + browser)
**Status:** IMPLEMENTED 2026-06-03
**Date:** 2026-06-03
**Origin / triggered-by:** operator caught that the browser tool drove a **shared headless
Chromium on <memory-host>** (`~/Docker/agent-cdp`, CDP `:9222`) over the LAN — a cross-machine
dependency that violates the explicit "keep things self-contained, no weird cross-computer
situation" requirement. (I wired the <memory-host> version; this corrects it.)

## Problem

Both harnesses' browser tools were pointed at a **remote** Chromium on <memory-host>:
`openclaw.json` `browser.cdpUrl` and `hermes/config.yaml` `browser.cdp_url` both =
`http://internal-host:9222`. Consequences:
- Cross-machine: every browser action is a LAN round-trip to <memory-host>; a <memory-host>/VPN/`agent-cdp`
  hiccup breaks the eval. Not self-contained.
- It also **disabled each harness's own built-in local browser** — setting `cdp_url` is exactly
  what makes hermes "skip the local headless launcher" (`browser_tool.py::_get_cdp_override`);
  openclaw likewise attaches instead of managing its own.
- The image bakes **no Chromium** (only the `playwright-core` lib), which is *why* it was
  pointed at <memory-host> in the first place — expedient, not principled.

## Goal / definition of done

Each trial container runs its **own** headless Chromium; each harness's browser tool drives
**that** in-container browser. No <memory-host>, no LAN, no `agent-cdp`. `browser-find-fact-01` passes
for both harnesses with `browser_used=1`, driving the local browser.

## Design decisions

**One Chromium per trial container; both harnesses attach to `http://127.0.0.1:9222`.**
- A trial container runs exactly one harness, so "one Chromium in the container" *is* "each
  harness has its own browser." No sharing across harnesses, no cross-machine anything.
- **Why attach-to-local-CDP, not each harness's native self-launch:** hermes's native "local
  mode" drives Chromium through an `agent-browser` daemon (`npm i -g agent-browser` +
  `agent-browser install` for its own Chromium) which is **absent** from the image; openclaw
  self-launches via `executablePath`. Mixing two different Chromium builds/flag-sets would
  *confound* a harness-vs-harness comparison. Pointing both at one controlled in-container
  Chromium keeps the browser backend **identical** — only the harness's tool/strategy differs,
  which is the variable under test. It's also the smallest delta from the working setup
  (swap `<memory-host>` → `127.0.0.1` + add an in-container launcher).
- **Concurrency bonus:** because each trial container has its own Chromium (not one shared on
  <memory-host>), browser trials no longer have to run sequentially — the `n_concurrent_trials: 1`
  constraint can be relaxed for browser tasks later (kept at 1 for the direct e2e comparison).

**Chromium provisioning (validated in-container before writing this):**
- Base is **Debian 13 (trixie)**; `apt-get install chromium` yields a real `/usr/bin/chromium`
  **148.0.7778.215** (matches the <memory-host> Chrome 148 we replaced) — no Ubuntu snap-stub problem.
- Container gotcha: Chromium as **root** needs `--no-sandbox` (+ `--disable-dev-shm-usage`).
  Debian's `/usr/bin/chromium` is a wrapper that sources `/etc/chromium.d/*` and honors
  `$CHROMIUM_FLAGS`, so a drop-in flags file applies the flags to **every** launch (covers the
  launcher script, and any harness that shells out to `/usr/bin/chromium`). Verified: a headless
  CDP launch as root came up in ~2s → `Chrome/148.0.7778.215`.
- Launch via a baked, idempotent `start-cdp.sh` (no-op if `:9222` already answers; waits for
  `/json/version` readiness — not a fixed sleep). Each adapter calls it immediately before the
  agent run; Chromium is disowned (`nohup … &`) so it outlives the launcher and dies with the
  container (`delete: true`).

## Implementation

1. **`environments/agent-rich/Dockerfile`**: `apt-get install -y --no-install-recommends
   chromium fonts-liberation`; write `/etc/chromium.d/00-harbor-container` with
   `--no-sandbox --disable-dev-shm-usage --disable-gpu`; `COPY` + `chmod +x` `start-cdp.sh`;
   build-time assert `/usr/bin/chromium --version`.
2. **`environments/agent-rich/start-cdp.sh`** (new): idempotent headless launch on
   `127.0.0.1:9222` + readiness poll.
3. **`harnesses/openclaw/openclaw.json`**: `browser.cdpUrl` `internal-host` →
   `127.0.0.1`.
4. **`harnesses/hermes/config.yaml`**: `browser.cdp_url` `internal-host` → `127.0.0.1`
   (update the "running on <memory-host>" comment to "in-container").
5. **`lib/openclaw_thin.py` + `lib/hermes_thin.py`**: prepend `bash /opt/harness/start-cdp.sh &&`
   to the agent command so the local browser is up before the agent runs.
6. Rebuild `:latest`; verify `/usr/bin/chromium` present + a local CDP launch; run
   `configs/browser-e2e.yaml` and confirm `browser_used=1` for both with **no** <memory-host> reference
   in the trajectory.

## Acceptance criteria

- [x] Rich image bakes `/usr/bin/chromium` (148.0.7778.215) + `/etc/chromium.d` no-sandbox flags + `start-cdp.sh`.
- [x] `start-cdp.sh` brings up `127.0.0.1:9222` in-container (readiness-gated, idempotent) — verified in a clean container (`Chrome/148.0.7778.215`, ~2s).
- [x] openclaw `browser` tool drives the **local** Chromium (`browser_used=1`, 13 calls, answer correct, no decoy).
- [x] hermes `browser_navigate` drives the **local** Chromium (`browser_used=1`, 60 calls, answer correct, no decoy).
- [x] No `internal-host:9222` reference remains — configs use `127.0.0.1`; the self-contained trajectory shows `127.0.0.1` and **0** <memory-host> refs (vs 18 <memory-host> refs in the prior run).

## Result (live e2e, `configs/browser-e2e.yaml`, n=1 each, 2026-06-03)

| | reward | browser_used | browser calls | answer | CDP host in trajectory |
|---|---|---|---|---|---|
| openclaw | 1.0 | 1 | 13 (`browser`) | correct, no decoy | `127.0.0.1` (0 <memory-host>) |
| hermes | 1.0 | 1 | 60 (`browser_navigate`/…) | correct, no decoy | (0 <memory-host>) |

The `&&` gate is the proof of locality: each agent only ran *because* `start-cdp.sh`
exited 0 (local CDP up). A failed local launch would have aborted the run before the agent.
Prior (<memory-host>) run for contrast: 18 `internal-host` references in the trajectory.

## Note — memory stack is still on <memory-host> (separate, out of scope here)

This change makes the **browser** self-contained. The **hindsight memory** MCP
(`openclaw.json` mcp.hindsight, hermes honcho/hindsight) still points at
`internal-host:8888` — that's the deliberately-shared eval memory substrate
(`done/2026-05-29-memory-stack-deployment.md`), a separate architectural decision. If
self-containment should extend to memory too, that's its own spec.

## Pointers

- Image: `environments/agent-rich/Dockerfile` + new `start-cdp.sh`.
- Configs: `harnesses/openclaw/openclaw.json` (`browser.cdpUrl`),
  `harnesses/hermes/config.yaml` (`browser.cdp_url`).
- Adapters: `lib/openclaw_thin.py`, `lib/hermes_thin.py`.
- Predecessor: `2026-06-03-browser-tool-registry-fix.md` (made the tool *exist*; this makes its
  backend *local*). The shared-<memory-host> wiring traces to `2026-06-02-browser-and-pin-findings.md`.
- hermes local-launch internals: `tools/browser_tool.py` (agent-browser local mode),
  `hermes_cli/browser_connect.py` (chromium resolver). openclaw managed launch:
  `dist/chrome-*.js` (`--no-sandbox` gated on `browser.noSandbox`), `dist/config-bkMW3D5-.js`
  (`executablePath`/`headless`/`noSandbox`/`cdpUrl`).

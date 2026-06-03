# Gateway-backed full-harness execution (openclaw + hermes)

**Epic:** E3 — Capability infrastructure (memory + browser)
**Status:** APPROVED 2026-06-03 — root cause found; implementation to start after compact.
**Date:** 2026-06-03
**Origin / triggered-by:** chasing #90 (openclaw `browser` tool never surfacing) revealed
the thin adapter runs openclaw in **embedded `--local` mode**, not its full gateway-backed
runtime — so gateway-hosted capabilities (the browser control server) are silently absent.
Operator decision: the eval must exercise the **full** harnesses (that was the point of the
rich setup), not a reduced thin client. Complete the gateway path; do not defer.

## The premise we broke

The rich harnesses (`harbor-agents-rich`) were built to compare openclaw vs hermes as the
**real, full-capability agents** — same model, same provider (novita), isolated state — so a
score gap is the harness. "Thin adapter" was only ever meant to mean **"invoke the BAKED
config without regenerating it"** (FOOTGUNS #12). But `lib/openclaw_thin.py` runs
`openclaw agent --local`, which is the **embedded** runtime — it does NOT stand up the
gateway, so any capability the gateway hosts is dropped. We were comparing *embedded*
openclaw, not *full* openclaw. Same risk to re-audit on the hermes side.

## What we found (2026-06-03, all verified in-container)

1. **CDP is reachable** from inside the trial container (`curl internal-host:9222/json/version`
   → Chrome 148). #90 is NOT a network problem.
2. **The browser plugin loads** and `createLazyBrowserTool` registers the `browser` tool
   **unconditionally** (no `enabled`/`available` gate on the tool object). Yet `browser` is
   **absent** from the agent's tool catalog (while `exec`/`web_search`/`web_fetch`/… are present).
3. The browser tool's own description: *"Control the browser via **OpenClaw's browser control
   server**."* That server is part of the **gateway**, which `agent --local` (embedded) does
   not run → the tool is filtered out for lack of a backing server.
4. **The gateway refuses to start without auth:** `openclaw gateway` →
   *"Refusing to bind gateway to auto without auth. Set `OPENCLAW_GATEWAY_TOKEN` or
   `OPENCLAW_GATEWAY_PASSWORD`, or pass `--token`/`--password`."* Without it the agent emits
   `EMBEDDED FALLBACK: Gateway agent failed; running embedded agent` (target `ws://127.0.0.1:18789`).
5. **With a token, the gateway gets past auth** (logs `resolving authentication` + seeds
   `gateway.controlUi.allowedOrigins`) **but the `browser` tool still did not surface** in the
   one-shot test — so exposure is a **3-step chain**, not a single flag:
   (a) gateway reaches a real listening/ready state; (b) the agent actually connects
   gateway-backed (no silent embedded fallback); (c) the gateway's browser control server
   initializes and attaches to the wiley CDP, exposing the `browser` tool.

## Validity implication (must disclose)

Every harbor-tasks run to date used the thin `--local` (embedded) path. So the proven
discriminators and any prior numbers reflect **embedded openclaw vs hermes**, not the full
harnesses. Once gateway-backed execution lands, re-baseline before trusting comparisons; note
this in RESULTS.md.

## Goal / definition of done

Both harnesses run their **full runtime** in every trial, exposing all baked capabilities:

1. openclaw runs **gateway-backed** (gateway up with a token, agent connects to it, no embedded
   fallback); the `browser` tool surfaces and drives the wiley CDP.
2. hermes runs its full stack; its native browser (`browser_navigate`) is verified to actually
   navigate (not just be listed).
3. `browser-find-fact-01` passes for BOTH harnesses with `browser_used=1` (real browse, not a
   memorized answer — the grader already gates on `browser_used`).
4. The **core-11 suite still runs green** under the new invocation (gateway-backed must not
   regress the non-browser tasks); re-baseline cost/behaviour.
5. Symmetric + fair: each harness runs its own real runtime; provider pin (novita) + state
   wipe + memory substrate unchanged.

## Implementation plan (phased)

**Phase 1 — openclaw gateway lifecycle in the adapter.**
- `lib/openclaw_thin.py`: at agent run, (a) start `openclaw gateway` in the background with
  `OPENCLAW_GATEWAY_TOKEN` (generated per-trial or a fixed eval token), (b) **wait for a real
  readiness signal** (poll the gateway status / port `18789` / a ready log line — NOT a fixed
  sleep), (c) run `openclaw agent` **gateway-backed** (drop `--local`) with the matching token,
  (d) tear the gateway down in `finally`. Assert no `EMBEDDED FALLBACK` in the output (fail
  loud if it falls back — a silent embedded run is a void trial).
- Decide where the token lives: env injected by the adapter vs baked `gateway.auth` in
  `openclaw.json`. Keep it byte-stable and documented; it's a local-only gateway token, not a
  cross-host secret.

**Phase 2 — browser tool exposure + CDP attach.**
- Confirm the gateway's browser control server initializes and attaches to
  `browser.cdpUrl = http://internal-host:9222`. Check `attachOnly` / the
  remote-CDP-vs-local-launch path (no Chromium is baked, so a local launch would fail — remote
  attach is required). Verify `browser` appears in the agent catalog (the `--json` toolCatalog).
- Re-run `configs/browser-e2e.yaml`; assert `browser_used=1` and a real navigation.

**Phase 3 — hermes full-stack + browser parity.**
- Verify `hermes --yolo chat` exercises hermes's full runtime (it has no separate gateway, but
  confirm no embedded/reduced mode silently drops capabilities). Verify `browser_navigate`
  actually drives the shared CDP end-to-end (navigate + read), not just appears in the catalog.

**Phase 4 — re-baseline.**
- Re-run the core-11 at n=1 under gateway-backed openclaw to confirm no regression, then the
  n≥3 pass^k verdict grid. Update RESULTS.md (incl. the embedded→full validity note).

## Risks / open questions

- **Gateway lifecycle in a trial container** — start/stop, port `18789` collisions under
  concurrency (each trial is its own container, so per-container localhost is fine; confirm),
  readiness detection, clean teardown so a hung gateway doesn't wedge the trial.
- **Cost/behaviour shift** — gateway-backed routing may change token/cost vs embedded; that's
  why Phase 4 re-baselines rather than trusting old numbers.
- **Shared wiley CDP** — one Chromium for all trials → browser trials run sequentially
  (`n_concurrent_trials: 1`), already known.
- **controlUi allowedOrigins / auth** — the gateway seeds localhost origins; confirm nothing
  else (CSRF/origin, TLS ws:// vs wss://) blocks the agent↔gateway connection.
- Does any OTHER baked capability (beyond browser) also require the gateway and was silently
  dropped under `--local`? Audit the full tool catalog embedded-vs-gateway.

## Acceptance criteria

- [ ] openclaw runs gateway-backed every trial (token + readiness wait + no embedded fallback);
      `browser` tool present in the catalog and drives wiley CDP.
- [ ] hermes full stack verified; `browser_navigate` navigates end-to-end.
- [ ] `browser-find-fact-01` → `browser_used=1` + correct answer for BOTH harnesses.
- [ ] core-11 re-runs green under gateway-backed openclaw (no regression).
- [ ] RESULTS.md updated with the embedded→full re-baseline note.

## Pointers

- Adapters: `lib/openclaw_thin.py`, `lib/hermes_thin.py`. Baked configs:
  `harnesses/openclaw/openclaw.json` (`browser`, `gateway`), `harnesses/hermes/config.yaml`.
  Image: `environments/agent-rich/Dockerfile` (rebuild on baked-config change).
- Browser task + e2e: `tasks/tool-orchestration/browser-find-fact-01/`, `configs/browser-e2e.yaml`.
- Prior findings: `2026-06-02-browser-and-pin-findings.md` (CDP wiring, #90 origin).
- Tool gate read this session: `dist/plugin-registration-DN5HQRHd.js::createLazyBrowserTool`
  (registers `browser` unconditionally → exposure depends on the gateway/control server).

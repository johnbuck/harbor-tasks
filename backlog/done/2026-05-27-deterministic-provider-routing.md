# Deterministic provider routing — pin OpenRouter upstream host

- **Epic:** E2 — Fair-comparison controls
- **Date:** 2026-05-27
- **Status:** IMPLEMENTED 2026-05-27; REGRESSED 2026-06-02; **RESOLVED 2026-06-03** — re-pinned both harnesses to `novita` (byte-identical `only:["novita"]` in `harnesses/openclaw/openclaw.json` + `harnesses/hermes/config.yaml`, verified end-to-end). The regression record below is kept as history.
  The pinned routing was set to `only:["deepseek"]`, an INVALID OpenRouter provider
  slug for deepseek-v4-pro → every request 404s ("No endpoints found matching your
  data policy"). Consequence: hermes can't make a single call, and openclaw's
  xrouter path silently ignores the bad pin and routes freely — so NEITHER harness
  is actually pinned. Fix = a valid non-training single host (`fireworks` or
  `novita`, both 200 / 1M ctx) in BOTH `harnesses/openclaw/openclaw.json` and
  `harnesses/hermes/config.yaml`, then rebuild the image. Full detail:
  `backlog/2026-06-02-browser-and-pin-findings.md`. Tracked as the roadmap E2 blocker.
- **Origin:** v9 showed openclaw 0 cache hits vs hermes 21,504 on the same model — investigation revealed an OpenRouter routing confound.

## Problem

OpenRouter load-balances each request across many upstream hosts for a given
model (DeepSeek/Kimi are served by 12–19 providers). Two consequences corrupt
comparison:

1. **Per-host caching.** DeepSeek/Kimi prompt caches live on each upstream
   host. v9's openclaw calls hit SiliconFlow → Novita → DeepInfra → SiliconFlow
   (confirmed via `/generation` records), so no host ever saw the same prefix
   twice → `native_cached=0` every call. Hermes happened to stay on caching
   hosts → 21,504 cached. **Pure load-balancer luck, not harness behavior** —
   a rerun could swap the result.
2. **Per-host pricing.** The same model costs ~$0.435/M on DeepSeek-direct but
   ~$1.6/M on SiliconFlow/Novita. Unpinned routing made openclaw silently
   ~4× more expensive than the price we'd recorded.

Either confound would make a cost/latency comparison meaningless.

## Scope

**In:**
- Pin every call to one upstream host via OpenRouter's `provider` routing.
- openclaw: `models.providers.openrouter.params.provider = {only:[host], allow_fallbacks:false}`
  (openclaw's documented extra-body passthrough). Injected in
  `OpenClawOpenRouter._merge_provider_base_url_from_env`.
- hermes: `provider_routing: {only: [host]}` in config.yaml (hermes maps it to
  `extra_body.provider` on every OpenRouter call). Injected by overriding
  `HermesNoInstall._build_config_yaml`.
- `PINNED_OPENROUTER_PROVIDER` constant in both modules, kept in sync.

**Out:**
- Relaxing the account privacy guardrail to reach cheaper (data-training)
  hosts — that's an operator privacy decision, left untouched.
- Per-request provider variety. We intentionally fix one host.

## Design decisions

- **`provider.only` + `allow_fallbacks:false`** over `order` — strict single
  host guarantees deterministic caching; a fallback flip mid-run would
  reintroduce the cache confound. A pinned-host outage failing the trial is an
  acceptable (rare) tradeoff for determinism.
- **Io Net** chosen for kimi-k2.6: cheapest host that passes the account's
  privacy guardrail ($0.73/$3.49). Chutes/Cloudflare are blocked by the data
  policy; pinning respects the homelab's privacy-first posture.
- **Determinism over caching savings.** Io Net doesn't do prompt caching, so
  both harnesses get `cache=0` — consistently. Fair comparison matters more
  than per-run cost here; revisit if cost-per-run dominates.
- **No forking.** Both adapters expose provider routing through documented
  config; subclass injection is enough.

## Acceptance criteria

- [x] All calls from both harnesses hit the pinned host (v10: 4/4 openclaw
      calls = Io Net, verified via `/generation`).
- [x] Cache behavior is identical for both harnesses (both 0 on Io Net).
- [x] openclaw cost reconciles exactly with billed `/generation` cost.

## Revision history

- v9 (unpinned, DeepSeek V4 Pro): openclaw spread across 4 hosts, 0 cache,
  inflated price — exposed the confound.
- v10 (pinned to Io Net, Kimi K2.6): deterministic, costs reconcile.

## Open questions

- For sweeps where cost-per-run matters more than determinism, pick a
  caching-capable pinned host and accept that caching helps repeated runs.
  Still deterministic as long as one host is pinned.

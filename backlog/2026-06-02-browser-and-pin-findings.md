# Browser tool + provider-pin findings (2026-06-02) — pre-compact handoff

- **Epic:** E3 — Capability infrastructure (memory + browser)

Single source of truth for the browser-task + provider-pin work. Read first after
the compact. **Two live problems, both surfaced by a real e2e of the browser task.**

> **UPDATE 2026-06-03 — Problem 1 (provider pin) is RESOLVED; Problem 2 (openclaw
> browser, E3) is still open.** Both harnesses re-pinned `deepseek → novita`,
> rebuilt, and verified (commits d6421e2 + 7f63a40). Hermes write-persistence (#92)
> fixed in the same pass (`cd /app`). See the "RESOLVED" notes inline below. The
> only remaining item in this doc is the browser surfacing (NEXT ACTION).

## NEXT ACTION — RESOLVED 2026-06-03 (stale plugin registry)
**Both findings in this doc are now closed.** The browser-tool blocker was neither
CDP reachability nor `--local`/embedded mode — it was a **stale baked plugin
registry** that never indexed the `browser` plugin. Fix: bake `openclaw plugins
registry --refresh` into the rich image (46 → 64 enabled). Full write-up +
disproof of the embedded-vs-gateway theory: `2026-06-03-browser-tool-registry-fix.md`.
The four guesses above (CDP unreachable / `--local` suppresses / config path /
gateway-backed required) were ALL wrong; recorded here so the dead ends aren't
re-explored.

## Problem 1 — the provider pin is BROKEN → **RESOLVED 2026-06-03 (pinned to novita)**

> **RESOLUTION (2026-06-03).** Re-pinned BOTH harnesses `deepseek → novita` and
> rebuilt the image; verified end-to-end via `tasks/_verify/file-persistence-01`
> (oracle + openclaw + hermes all reward 1.0 / answer_present 1). `data_collection:
> deny` preserved (privacy intact). **Correction to the fix table below: `fireworks`
> is deny-eligible but its deepseek-v4-pro endpoint has NO native tool-use**, so
> hermes 404s "No endpoints found that support tool use" on it (openclaw masks this —
> its xrouter path routes tools differently and 200s even on a tool-use-less host, so
> ALWAYS verify the pin host with hermes, not just openclaw). Providers confirmed to
> serve `deny + tool-use + reasoning + require_parameters`: **novita, deepinfra,
> together, parasail, siliconflow** (NOT fireworks / gmicloud / atlascloud / baidu).
> Picked **novita**. Also note the precise failure mode: `deepseek` is a valid slug,
> but DeepSeek's own endpoint became *training-flagged*, so it's deny-incompatible
> (the "invalid slug" framing below was imprecise). Commits d6421e2 + 7f63a40.

Direct OpenRouter tests (real calls, deepseek/deepseek-v4-pro):

| provider routing | result |
|---|---|
| `only:["deepseek"]` + `data_collection:deny` (the CURRENT pin) | **404** "No endpoints found matching your data policy (Paid model training)" |
| `only:["deepseek"]` (no data policy) | **404** "No endpoints available matching your guardrail restrictions" |
| `data_collection:deny` + `allow_fallbacks:true` (no `only`) | 200 — served by Parasail |

**`only:["deepseek"]` is an invalid provider slug for this model — it matches NO
endpoint and always 404s.** So:
- **hermes** (native OpenRouter) 404'd on every call → never ran a single LLM turn
  in the e2e. Its 0.0 was NOT a browser/quality signal.
- **openclaw** only "worked" because its **xrouter** path silently IGNORES the
  broken `only:[deepseek]` and routes freely. So **neither harness was ever
  actually pinned** — the whole fairness premise was void, and the `pinned-v2`
  image I promoted to `:latest` is built on this broken pin. (My error.)

**The fix** — valid single NON-training hosts (confirmed 200 under
`data_collection:deny`, no fallback):

| `only:[host]` | status | context |
|---|---|---|
| `fireworks` | 200 ✓ | 1M |
| `novita` | 200 ✓ | 1M |
| `together` | 200 ✓ | 512K |
| `atlas-cloud`, `siliconflow` | 200 ✓ | 1M |
| `parasail`, `deepinfra` | 429 transient (serve it) | 1M |
| `deepseek` (current) | 404 invalid | — |
| `gmicloud` | 404 (trains) | — |

Change `only:["deepseek"]` → `only:["fireworks"]` (or `novita` — both full 1M ctx,
non-training) in BOTH `harnesses/openclaw/openclaw.json`
(`models.providers.xrouter.params.provider`) AND `harnesses/hermes/config.yaml`
(`provider_routing`). Keeps fairness (one shared host) + privacy (`deny` satisfied)
+ unblocks hermes. **OPERATOR: pick fireworks or novita.** Then rebuild + the pin
is finally real (also fixes the long-standing "neither harness pinned" issue).
Test script: `/tmp/confirm_hermes_endpoint.py` + `/tmp/find_pin_host.py` (rerun via
`infisical run --domain=http://internal-host:8380 --projectId=<infisical-project-id> --env=production --path=/proxy/ -- python3 <script>`; key never printed).

## Problem 2 — browser task is memorization-confounded (mitigated by gating)
`quotes.toscrape.com` is a top scraping-tutorial site, so its quote→author data
(incl. the "Jim Henson" attribution) is in training. In BOTH e2e runs openclaw
answered "Jim Henson" correctly WITHOUT browsing (`answer_correct=1`,
`browser_used=0`). Mitigation already shipped: the grader now **gates reward on
`browser_used`** (a correct answer with no browser call scores 0), so memory
shortcuts don't pass. Once openclaw's browser actually works, a real browse →
`browser_used=1` → reward 1. (If we want the answer itself to require the browser,
switch to a non-memorized target later; gating is sufficient for now.)

## browser-find-fact-01 task spec (built this session)
- Path: `tasks/tool-orchestration/browser-find-fact-01/` (single-step,
  `allow_internet=true`, `mcp_servers=[]`, agent timeout 600s).
- Target: `https://quotes.toscrape.com/js/` (JS-rendered → curl sees 0 quotes;
  forces a real browser). Asked quote: "...give a stupid or misinformed beholder a
  black eye" → site attributes to **Jim Henson**, on **page 3** (forces pagination).
- Grader (`tests/test.sh`): `reward = 1.0 iff answer_correct AND browser_used`.
  answer_correct = "henson" present AND no decoy author (sibling penalty, format-
  robust). browser_used = trajectory has a `browser`/`browser_*` tool call
  (matches BOTH openclaw `"browser"` and hermes `browser_navigate`). Oracle gets
  answer_correct=1, browser_used=0 → headline 0 (EXPECTED; browser tasks aren't
  oracle-provable end-to-end — documented in task.toml).
- Oracle `solution/solve.sh` writes "Jim Henson" (validates the answer-check).

## Browser wiring facts (verified)
- Both harnesses wired to a SHARED headless Chromium on the memory host via CDP:
  openclaw `browser.cdpUrl`, hermes `browser.cdp_url` = `http://internal-host:9222`
  (LIVE: Chrome 148, `ws://...:9222/`). Shared → run browser trials SEQUENTIALLY
  (`n_concurrent_trials:1`, as `configs/browser-e2e.yaml` does) or they collide.
- Remote browser can't see a site served INSIDE the trial container (localhost) —
  hence a real external site (operator chose this), not a container-local one.
- **Thin adapters DO NOT forward Harbor `mcp_servers`** (`lib/openclaw_thin.py`
  runs `openclaw agent --local --json` against the BAKED config; ditto hermes).
  So Harbor-level `[[environment.mcp_servers]]` injection never reaches the model
  — capabilities MUST be enabled in the baked config + image rebuild.

## Config + image state
- Source configs baked via `environments/agent-rich/Dockerfile` (COPY lines 32
  openclaw.json, 40 hermes config.yaml). Rebuild:
  `docker build -f environments/agent-rich/Dockerfile -t harbor-agents-rich:latest .`
- **UNCOMMITTED edits (this session):**
  - `harnesses/openclaw/openclaw.json` — added `browser.enabled: true`
  - `harnesses/hermes/config.yaml` — `cli: [hermes-cli, browser]` (was `[hermes-cli]`)
  - `tasks/tool-orchestration/browser-find-fact-01/{task.toml,tests/test.sh}` —
    grader gated on browser_used + both-convention detection
  - `configs/browser-e2e.yaml` (new) — both-harness sequential e2e config
  - These are NOT yet committed (pin still broken; browser not yet surfacing).
    Commit alongside the pin fix once both are resolved.
- **Image tags:**
  - `:latest` (rebuilt 2026-06-03) — pinned to **novita** (deny + tool-use +
    reasoning, verified), recall MCP removed from both harnesses, `cd /app` write-
    persistence fix live (adapter, not baked). Pin + #92 are trustworthy; the only
    unverified capability left is openclaw browser surfacing (E3).
  - `:pre-browser-bak` = e494e1d1cd2a — the promoted pinned-v2 (broken deepseek pin).
  - `:pre-browser-bak` = e494e1d1cd2a — = the promoted pinned-v2 (broken pin).
  - `:pre-pin-unpinned-bak` = 19cce11e1834 — old UNPINNED image; hermes WORKED on
    it (routed via fallback to a non-training host). The only currently-working-
    for-hermes image, but load-balanced (cost-contaminated).

## e2e run log (what actually happened)
- Run 1 (pinned `:latest`, browser DISABLED): openclaw 1.0 (memory answer, no
  browser), hermes 0.0 (pin 404). Headline "DISCRIMINATES" — FALSE on both counts.
- Run 2 (browser-enabled rebuild): openclaw reward 0 (answer right from memory,
  but browser_used=0 gate), hermes 0.0 (pin 404). Browser tool still not surfacing.
- Conclusion: NO valid browser signal yet. Need (a) pin fix so hermes runs, (b)
  openclaw browser surfacing. THEN re-run for a real result.

## Sequenced plan to finish
1. ~~Operator picks pin host (fireworks/novita). Edit both source configs
   `only:[deepseek]` → `only:[<host>]`.~~ **DONE 2026-06-03 — pinned to novita,
   rebuilt, verified (#92 fixed too).**
2. Diagnose + fix openclaw browser surfacing (NEXT ACTION above). **← only remaining item.**
3. Rebuild `:latest`; verify openclaw exposes `browser` + hermes exposes
   `browser_navigate`, and hermes makes LLM calls (no 404).
4. Re-run `configs/browser-e2e.yaml`; confirm `browser_used=1` for both and read
   the real reward split.
5. Commit the source edits + task + this doc together.

# openclaw reasoning on OpenRouter — RESOLVED 2026-05-28

- **Epic:** E1 — Harness runtime & adapters
- **Date:** 2026-05-28
- **Status:** ✅ RESOLVED. Verified end-to-end: QuixBugs task → reward 1.0 with
  `reasoning_tokens = 327` across 4 turns. openclaw reasoning runs ARE now
  trustworthy when the recipe below is used (and the `reasoning_tokens > 0` gate
  is checked).
- **Canonical writeup:** `backlog/FOOTGUNS.md` #1 (+1a, #2, #3). This file is the
  investigation log.

## Resolution (the recipe)

Four parts, all required (none sufficient alone):
1. **Custom-named provider** `xrouter` (NOT built-in `openrouter`/`openai`) at
   OpenRouter's OpenAI endpoint — built-ins ignore per-model reasoning config.
2. **`reasoning: true`** on the model entry — THE gate. openclaw returns
   off-only before reading `compat` when this is false (its default). This was
   the actual root cause the two earlier attempts missed.
3. **`compat.supportedReasoningEfforts`** declared (the level menu behind the gate).
4. **`apiKey: "${XROUTER_API_KEY}"`** env-template SecretRef (custom providers get
   no free env auth) + **`--thinking high`** (xhigh's payload is rejected by
   deepseek-v4-pro's OpenRouter route).

Implemented in `lib/openclaw_openrouter.py` (`OpenClawOpenRouter`).

## Original investigation (kept for history)

- **Supersedes:** the earlier `backlog/done/2026-05-28-openclaw-reasoning-passthrough.md`,
  which FALSELY claimed success — ignore/deleted.

## The problem (real, reproduced)

openclaw, run against an OpenRouter model, forces `--thinking high` (Harbor's
stock `CliFlag` default) and openclaw's **built-in `openrouter` provider plugin**
rejects it:

```
Error: Thinking level "high" is not supported for openrouter/deepseek/deepseek-v4-pro. Use one of: off.
```

Confirmed model-independent: identical error on `kimi-k2.6` AND
`deepseek-v4-pro`. openclaw aborts before doing any work → reward 0, no session.

## What I tried, and why each FAILED (both verified)

1. **Forced `--thinking off`** (committed as `67a6f51`, currently on `origin/main`).
   Result: openclaw RUNS but produces **zero reasoning** — verified
   `reasoning_tokens = 0`, no reasoning content in `openclaw.session.jsonl`.
   This is **silently wrong** (looks like it works; agent isn't thinking).
   **⚠️ The pushed adapter is in this state — do NOT trust any openclaw run for
   reasoning until this is fixed.**

2. **Declared `models[].compat.supportedReasoningEfforts`** on the model entry
   + kept a real `--thinking` level (working-tree, uncommitted).
   Result: the field lands in `openclaw.upload.json` but openclaw STILL errors
   `Use one of: off`. The built-in `openrouter` provider plugin **ignores
   entry-level `compat`** — it computes thinking support from its OWN model
   profiles/catalog, and does not recognize `deepseek-v4-pro` as reasoning-capable.

## Root cause (from https://docs.openclaw.ai/tools/thinking + the config dump)

- openclaw gates `--thinking` on a model's resolved thinking profile.
- For **built-in providers** (`openrouter`, `anthropic`, …) the profile comes
  from the plugin's own model matching + **merged catalog facts** (fetched
  metadata), NOT from the user's `models[].compat`. The plugin's "DeepSeek V4"
  profile exposes `xhigh` (per docs) but our id `deepseek/deepseek-v4-pro`
  isn't matched → off-only.
- The docs' `compat.supportedReasoningEfforts` override applies to **custom
  OpenAI-compatible providers**, not the built-in `openrouter` provider.

## Candidate fixes for next session (NOT yet attempted/verified)

1. **Custom OpenAI-compatible provider** (most likely correct): define our own
   provider (name != a built-in like `openrouter`), `baseUrl =
   https://openrouter.ai/api/v1`, with `models[].compat.supportedReasoningEfforts`
   — which IS honored for custom providers. Needs adapter rework: provider name,
   the `<PROVIDER>_API_KEY`/`<PROVIDER>_BASE_URL` env convention
   (stock `_provider_env_keys`), and possibly `_SUPPORTED_PROVIDERS`. Then set
   `--thinking` to a declared level and VERIFY `reasoning_tokens > 0`.
2. **Use the correct level for the built-in profile**: docs say OpenRouter
   DeepSeek V4 exposes only `xhigh` (not `high`). But the error said `off` for
   `deepseek-v4-pro`, so the id likely isn't matched — test `xhigh` AND/OR an id
   the plugin recognizes (e.g. without the `-pro` suffix). (xhigh test was set
   up but not run — user halted.)
3. **openclaw's NATIVE `deepseek` provider** (direct, not via OpenRouter): docs
   say "DeepSeek V4 (direct) exposes /think xhigh|max" — native thinking works.
   Needs a DeepSeek API key + clearing the privacy guardrail for DeepSeek-direct.
   (Open question the user was probing: does stock openclaw + DeepSeek-direct
   "just work"? Not yet tested — provider-key availability unverified.)
4. **`openclaw models scan`** to populate the OpenRouter catalog so the built-in
   plugin learns the model's reasoning support. Lighter; unverified.

## MANDATORY verification gate (the lesson from this session)

Do NOT claim reasoning works from "it ran" or "session.jsonl mentions
reasoning". VERIFY `completion_tokens_details.reasoning_tokens > 0` (or non-empty
`message.reasoning`) in `openclaw.session.jsonl`. Attempt #1 ran fine and the
word "reasoning" appeared 17× as empty schema fields — actual reasoning_tokens
were 0.

## Code state at handoff

- `origin/main` `67a6f51`: adapter forces `--thinking off` (runs, NO reasoning).
- working tree `lib/openclaw_openrouter.py` (uncommitted): attempt #2 —
  `OPENCLAW_THINKING_LEVEL="xhigh"` + `compat.supportedReasoningEfforts` declared
  + `_normalize_provider_models_schema` override. **Does not work** (errors).
  Keep as reference for the custom-provider rework, or revert.
- hermes side untouched; hermes never had the registry error (routes cleanly),
  but whether hermes actually enables reasoning is also UNVERIFIED — check
  parity before trusting any openclaw-vs-hermes reasoning comparison.

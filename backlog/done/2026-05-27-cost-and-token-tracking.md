# Cost + token tracking — per-trial usage with live OpenRouter pricing

- **Epic:** E2 — Fair-comparison controls
- **Date:** 2026-05-27
- **Status:** IMPLEMENTED 2026-05-27
- **Origin:** v3 trial reported `cost_usd: null` for openclaw; hermes reported 0 tokens.

## Problem

Cost and tokens are core comparison axes, but Harbor's bundled adapters under-
reported both:

- **openclaw** sets `cost_usd` from `FinalMetrics.total_cost_usd`, which is
  always `None` because openclaw's JSON doesn't emit cost. Its `FinalMetrics`
  also has no `cache_write` field, so even downstream cost math would miss the
  25%-premium cache-write tokens.
- **hermes** only populated `n_input/output_tokens` from the ATIF-derived
  `final_metrics`, which came out 0 — even though `hermes-session.jsonl`
  carried `input_tokens`, `cache_read_tokens`, `cache_write_tokens`,
  `output_tokens`, and `estimated_cost_usd` ready to use.

A naive hardcoded price table also produced two wrong-rate bugs (Sonnet
cache_write omitted; DeepSeek cache_read set 120× too high).

## Scope

**In:**
- `lib/openclaw_no_install.py`: read `openclaw.session.jsonl` per-message
  usage (input/output/cacheRead/cacheWrite), recompute cost with all four.
- `lib/hermes_no_install.py`: read `hermes-session.jsonl` totals; prefer
  `actual_cost_usd` > `estimated_cost_usd`; map to Harbor's
  `n_input_tokens = real_input + cache_read` convention.
- `lib/openclaw_openrouter.py`: `_openrouter_pricing()` — lru_cached fetch of
  per-token pricing for all OpenRouter models from `/api/v1/models`;
  authoritative. Hardcoded `_FALLBACK_PRICES_PER_MTOK` only on fetch failure.

**Out:**
- A unified cost basis across adapters. openclaw cost uses our live-pricing
  calc; hermes cost uses hermes's own `estimated_cost_usd`. Close but not
  identical methodology — acceptable for now (see Open questions).

## Design decisions

- **Read each agent's own session file** rather than rely on Harbor's
  normalized `FinalMetrics`, which drops cache_write and (for hermes) came
  out empty. The session files are the ground truth each tool writes.
- **Live pricing over a hardcoded table.** Hand-maintaining rates produced
  repeated errors; OpenRouter's `/api/v1/models` returns exact per-token
  `prompt` / `completion` / `input_cache_read` / `input_cache_write`. The
  table is now a fallback only.
- **Token-naming convention** matches Harbor: `n_input_tokens` includes
  cache_read; `n_cache_tokens` is cache_read alone. Cost splits real_input
  from cache_read to bill each correctly.

## Acceptance criteria

- [x] Both adapters report non-null `cost_usd` and full token counts in
      per-trial `result.json`.
- [x] openclaw cost reconciles with OpenRouter `/generation` records
      (v10: $0.0449 computed == sum of per-call generation costs).
- [x] Adding a new model requires no price-table edit (live fetch covers it).

## Open questions

- Unify cost methodology across adapters? Could compute hermes cost from the
  same live-pricing path instead of trusting its self-report. Deferred until a
  discrepancy actually bites.

## Follow-up tickets

- [[2026-05-27-deterministic-provider-routing]] — pricing is per-upstream-host;
  pinning the provider is what makes the live price match the billed price.

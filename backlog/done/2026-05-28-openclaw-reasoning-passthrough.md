# openclaw reasoning passthrough — IMPLEMENTED

- **Date:** 2026-05-28
- **Status:** DONE
- **Origin:** Operator — "fix the openclaw reasoning passthrough."

## Problem

openclaw could not run reasoning-capable models via OpenRouter. Harbor's
OpenClaw adapter sets `--thinking high` by default; openclaw's internal model
registry is blind to the underlying model behind the OpenRouter passthrough, so
it rejects every level except `off` and **errors before doing any work**:

```
Error: Thinking level "high" is not supported for openrouter/<model>. Use one of: off.
```

Confirmed model-independent (kimi-k2.6 AND deepseek-v4-pro → identical error).
This blocked every openclaw comparison run (bespoke + benchmark).

## Fix (`lib/openclaw_openrouter.py`)

Decouple "don't error" from "do reason":

1. **Force `--thinking off`** — override `CLI_FLAGS` in `OpenClawOpenRouter` so
   the thinking flag defaults to `off` (the only value openclaw's registry
   accepts for OR models). openclaw no longer errors on its own flag.
2. **Enable reasoning at the OpenRouter layer** — inject OpenRouter's
   `reasoning` body param via the same `models.providers.openrouter.params`
   extra-body passthrough already used for `provider` (the privacy pool):
   `params["reasoning"] = {"effort": "low"}` (module const `OPENROUTER_REASONING`,
   set to `None` to disable). OpenRouter maps `effort` to each model's native
   reasoning control, independent of openclaw's registry.

The `NoInstall` subclass inherits both, so bespoke (prebaked) and benchmark
(install-capable) paths are fixed. Hermes already routes cleanly; its
`provider_routing` could carry the same `reasoning` field if we want parity
(not required — hermes never had the registry error).

## Validation

Smoke test, openclaw × `openrouter/deepseek/deepseek-v4-pro`, 1 task:
- **reward 1.0** (completed; previously instant-failed)
- **0 thinking-level errors** (previously 1 per run)
- **reasoning active** — 17 reasoning-field entries in `openclaw.session.jsonl`,
  809 output tokens, ~4 min runtime (vs. instant fail before)
- cost captured: $0.0234

## Impact

Unblocks all openclaw-vs-hermes comparison runs (bespoke 17-category suite,
multi-step suite, and the oracle-validated benchmarks compilebench /
spreadsheetbench / bfcl / quixbugs). Next: run those comparisons.

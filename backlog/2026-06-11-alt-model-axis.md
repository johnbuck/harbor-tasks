---
status: IMPLEMENTED
epic: E4
date: 2026-06-11
---

# Alternate-model axis — run BOTH harnesses on the same non-deepseek model

**Epic:** E4 — Task Suite (methodology)
**Date:** 2026-06-11 (wired 06-11/06-12)
**Status:** IMPLEMENTED — committed `e8a1279`; smoke-validated on the rich image.
**Origin / triggered-by:** operator wanted to re-test the "harness > model" thesis
on a SECOND model (an Anthropic/Claude model) without weakening the core invariant.

## Principle (operator-stated, load-bearing)

The model is a **free variable**. The ONLY invariant is that **both harnesses run
the SAME model** — deepseek-v4-pro, Kimi K2.6, a Claude model, anything — so any
measured gap is the HARNESS, not the model. The infrastructure is therefore
model-agnostic and routes off the model string; a run config just instantiates one
choice. Do NOT hardcode a single model into the infra.

## What was wired (all general)

- **Key forwarding** — `lib/openclaw_thin.py` + `lib/hermes_thin.py` forward
  `ANTHROPIC_API_KEY` into the agent container when present (absent ⇒ no-op, so
  deepseek/OpenRouter runs are unaffected).
- **Provider routing off the model string:**
  - openclaw: `model_name` is `<provider>/<model>`. `anthropic/<model>` routes to
    openclaw's BUILT-IN native Anthropic provider (`api: anthropic-messages`,
    reads `ANTHROPIC_API_KEY`); `xrouter/<model>` → pinned OpenRouter host. The
    adapter already allows the `anthropic` provider prefix
    (`lib/openclaw_openrouter.py` base `_SUPPORTED_PROVIDERS`). No openclaw.json
    change needed.
  - hermes: a Claude `model_name` → adapter adds `--provider anthropic` (direct
    Anthropic API); anything else → baked OpenRouter default. `reasoning_effort`
    maps to the provider's native thinking surface.
- **Run-path key injection** — `tools/run_track_a.sh` optionally fetches the
  Anthropic key from a SEPARATE, Harbor-scoped Infisical project and exports it as
  the standard `ANTHROPIC_API_KEY` (covers the alt-model agent runs AND LLM-judge
  verifiers). No-op when `INFISICAL_ANTHROPIC_PROJECT_ID` is unset.
- **Run config** — `configs/core-suite-claude.yaml`: same 11 tasks/harnesses as
  `core-suite.yaml`; swap the two `model_name`s to any model, keep them identical.

## Infisical / secret plumbing

- Created a dedicated, **Harbor-scoped** project so the key can't be reached by
  anything but Harbor. It was originally an existing project named **DeepEval**;
  the operator had it **renamed to `Harbor`** (project id + slug are stable on
  rename, so all ID references keep working).
- Secret name in Infisical is **`BH_ANTHROPIC_API_KEY`** (env `prod`, path
  `/proxy/`). `run_track_a.sh` fetches it under that name and EXPORTS it as the
  standard `ANTHROPIC_API_KEY` (what the SDK / both harnesses read). The secret
  name is configurable via `INFISICAL_ANTHROPIC_SECRET_NAME`.
- Coords live in the gitignored `configs/local.env`
  (`INFISICAL_ANTHROPIC_PROJECT_ID`, `_ENV=prod`, `_PATH=/proxy`,
  `_SECRET_NAME=BH_ANTHROPIC_API_KEY`); placeholders in `local.env.example`.

## Validation

Smoke on the `harbor-agents-rich` image (real key fetched, `sk-ant-…`):
- **hermes** `--provider anthropic --model claude-sonnet-4-6` → returned `PONG`.
- **openclaw** `--agent main --model anthropic/claude-sonnet-4-6` (built-in
  provider) → returned `PONG`.
- No `temperature/top_p/budget_tokens` 400s; **no image rebuild needed** (adapters
  read live by Harbor, openclaw built-in provider, hermes CLI flag).

## How to run

```bash
source ~/.config/infisical/agent-architect.env   # universal-auth creds (see note)
CONFIG=$PWD/configs/core-suite-claude.yaml N_ATTEMPTS=1 \
  JOB_NAME=core-suite-alt-n1 tools/run_track_a.sh
```
The driver injects `BH_ANTHROPIC_API_KEY` (as `ANTHROPIC_API_KEY`) from the Harbor
project alongside the Shared OpenRouter key. To run a DIFFERENT alternate model,
edit the two `model_name`s in the config (same on both sides). Same-model invariant
is the only rule.

## Open items / caveats

- **LLM-judge tasks** must declare `ANTHROPIC_API_KEY = "${ANTHROPIC_API_KEY}"` in
  their `[verifier.environment.env]` to actually consume the injected key. The core
  eleven have no judge tasks; this is for the Track-B judged tasks
  (marketing/email-copy, backup-dr/restore-runbook, etc.).
- The Anthropic param surface is model-specific (e.g. Opus 4.8 rejects
  temperature/top_p/budget_tokens; Sonnet 4.6 is more lenient). Re-run the 1-call
  smoke after any model change to confirm the harness param mapping.
- Operator-knowledge note (stale doc): the Infisical universal-auth creds file on
  both hosts is `~/.config/infisical/agent-architect.env`, NOT the
  `infisical-identity.env` that `AGENTS.md` / `run_track_a.sh` usage comments cite.

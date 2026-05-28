# Agent adapters — pre-baked base image + NoInstall + OpenRouter subclasses

- **Date:** 2026-05-27
- **Status:** IMPLEMENTED 2026-05-27
- **Origin:** First real-LLM trial: hermes hit `AgentSetupTimeoutError`; openclaw couldn't reach OpenRouter.

## Problem

Harbor's bundled adapters install the agent CLI inside a fresh sandbox on
every trial (apt-get + nvm + `npm install -g openclaw@latest`; curl-pipe
install.sh for hermes). Two failures surfaced:

1. **Setup too slow.** Hermes's installer ran past the 360s default and the
   trial errored before the agent ever ran. Even when it succeeded, per-trial
   install is 2–4 min — untenable for sweeps (51 trials × ~3 min = ~2.5 h of
   pure install).
2. **openclaw couldn't use OpenRouter.** Its `_SUPPORTED_PROVIDERS` is
   `{anthropic, nvidia, openai}` — the `openrouter/…` model prefix raised a
   ValueError.

## Scope

**In:**
- `environments/agent-prebaked/Dockerfile`: base image with openclaw + hermes
  + node22/nvm pre-installed (same install commands the adapters run, deduped).
- `lib/openclaw_openrouter.py::OpenClawOpenRouter`: adds `openrouter` to
  `_SUPPORTED_PROVIDERS`, injects the OpenRouter base URL.
- `lib/openclaw_no_install.py::OpenClawNoInstallOpenRouter`: overrides
  `install()` to a no-op `openclaw --version` verify.
- `lib/hermes_no_install.py::HermesNoInstall`: overrides `install()` to a
  no-op `hermes version` verify (+ HERMES_HOME dirs).
- Task `environment/Dockerfile` FROM `harbor-agents-prebaked:latest`.

**Out:**
- Editing Harbor's core adapters. All behavior added by subclass.
- Pinning the base image by digest (noted for later; `:latest` upstream of
  openclaw/hermes is unpinned — a known Harbor risk).

## Design decisions

- **Skip install, don't just pre-bake.** Harbor's `install()` runs every trial
  regardless of image contents (idempotent but network-bound). Pre-baking the
  image alone saves nothing without overriding `install()` to a presence check.
- **Default sandbox user is root** (python:3.12-slim has no non-root user), so
  the prebaked image installs everything as root — `exec_as_agent` runs as
  root too, no user/PATH juggling needed.
- **Subclass naming kept literal** (`OpenClawNoInstallOpenRouter`) even though
  later runs went Anthropic-direct then back to OpenRouter — the class still
  supports the prefix; the name documents capability, not the active route.

## Acceptance criteria

- [x] `docker build -t harbor-agents-prebaked:latest environments/agent-prebaked/`
      succeeds; image has `openclaw --version` + `hermes version`.
- [x] A trial with both NoInstall subclasses completes with no setup timeout.
- [x] Total wall-clock for 2 harnesses drops from ~10m (v3) to ~2.5m (v5+).

## Revision history

- v3 trial: hermes `AgentSetupTimeoutError` at 360s → motivated pre-bake.
- v4: openclaw `openrouter/…` prefix failed → motivated the OpenClaw subclass
      (later folded into the OpenRouter subclass).
- v5: prebaked + no-install → 2m 30s, both agents succeed.

## Follow-up tickets

- [[2026-05-27-deterministic-provider-routing]] — pin the OpenRouter upstream.
- [[2026-05-27-cost-and-token-tracking]] — surface usage from each adapter.

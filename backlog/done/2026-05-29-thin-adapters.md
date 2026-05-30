# Thin Harbor adapters for openclaw + hermes (SHIPPED 2026-05-29)

**Status:** shipped + parity-verified end-to-end.
**Replaces:** the bundled `harbor.agents.installed.openclaw` / `installed.hermes`
adapters and the older `*NoInstall` subclasses.
**Companion:** [`2026-05-28-prebuilt-rich-harnesses.md`](2026-05-29-prebuilt-rich-harnesses-SHIPPED.md)
(rich image), [`2026-05-29-memory-stack-deployment.md`](2026-05-29-memory-stack-deployment.md)
(memory endpoints), `FOOTGUNS.md` #1, #17–#20.

## Why thin

Harbor's bundled adapters and our previous `NoInstall` subclasses **rebuild the
harness's config on every run**:

- `OpenClaw._build_full_openclaw_config()` writes `openclaw.upload.json` and
  copies it over `~/.openclaw/openclaw.json` — overwriting any baked config.
- `Hermes.run()` forces `HERMES_HOME=/tmp/hermes` (a fresh empty home) and writes
  a barebones `config.yaml` (`memory_enabled: false`, no skills, no persona, no
  reasoning).

This is why reasoning was off by default, why hermes ran with 0 skills, and why
every capability (reasoning, skills, memory, persona, sub-agents) had to be
reverse-engineered field-by-field through adapter code. Operator's verdict
2026-05-29: **"STOP USING THE PACKAGED HARNESSES."** Hence the pivot:
pre-built rich images (the harnesses' OWN config baked in) plus a thin adapter
whose only job is to invoke and capture metrics.

## What ships

| Adapter | Class | Purpose |
|---|---|---|
| `lib/openclaw_thin.py` | `OpenClawThin(OpenClawOpenRouter)` | invoke baked openclaw config; no rewrite |
| `lib/hermes_thin.py`   | `HermesThin(HermesOpenRouter)`    | invoke baked hermes home; no rewrite |
| `environments/agent-rich/Dockerfile` | `harbor-agents-rich:latest` | image with baked configs + persona + skills + honcho-ai |
| `configs/verify-rich.yaml` | — | end-to-end parity verification (1 task × 2 agents) |
| `tasks/_verify/reasoning-parity-01/` | — | the verification task (clone of fix-bug, `FROM harbor-agents-rich`) |

### What each `run()` actually does

**OpenClawThin.run** (`lib/openclaw_thin.py`):
1. Validate `model_name` provider is allowed (inherits xrouter from
   `OpenClawOpenRouter._SUPPORTED_PROVIDERS`).
2. Forward `OPENROUTER_API_KEY` from the process env into the container env.
3. Copy persona files from `/opt/harness/openclaw-workspace/` into the task cwd
   with `cp -rn` (no-clobber). openclaw loads SOUL/AGENTS/IDENTITY/USER from
   workspace = cwd every session; `skipBootstrap: true` (baked in
   `openclaw.json`) suppresses the first-run ritual that would otherwise seed
   generic files.
4. Run `openclaw agent --local --json --thinking high --model <m> --message <…>`
   against the BAKED `~/.openclaw/openclaw.json`.
5. Copy `openclaw.session.jsonl` out for metrics + ATIF trajectory.

**HermesThin.run** (`lib/hermes_thin.py`):
1. Validate `model_name` format.
2. Forward `OPENROUTER_API_KEY` from the process env into the container env.
3. Run `hermes --yolo chat -q "$HARBOR_INSTRUCTION" -Q --model <m>` with
   `HERMES_HOME=/root/.hermes` (the BAKED rich home).
4. Export the session for metrics: `hermes sessions export … --source cli`.

### What's deliberately NOT in the thin adapters

- **No `_build_full_openclaw_config` / `_build_config_yaml` invocation.** The
  baked config is authoritative.
- **No task-MCP merging.** Memory MCPs come from the baked config. If a task
  needs additional MCP servers, that's an edge case we'll handle separately
  (no such task in the suite as of 2026-05-29).
- **No HERMES_HOME=/tmp/hermes override.** That was the bundled adapter's
  workaround that bypassed the seeded home.

## The "one key everywhere" auth simplification

The first verification run had openclaw fail with `401 Missing Authentication
header` while hermes (same key, same image) succeeded. Root cause: the
verify config's `environment.env: ["XROUTER_API_KEY=${OPENROUTER_API_KEY}"]`
substitution is for the **container** env, not the **adapter** process env that
`OpenClaw._get_env("XROUTER_API_KEY")` reads. So `XROUTER_API_KEY` was empty in
the adapter, never forwarded into the container.

**Fix (FOOTGUNS #17):** one key everywhere.
- The baked `openclaw.json` xrouter provider apiKey is now `${OPENROUTER_API_KEY}`
  (not `${XROUTER_API_KEY}`).
- Both thin adapters forward `OPENROUTER_API_KEY` from `os.environ` directly
  (don't rely on harbor's environment.env substitution).
- `configs/verify-rich.yaml` simplified to a single env line.

Re-verification: openclaw + hermes both **reward 1.0, 0 exceptions** on
`reasoning-parity-01`.

## Persona / workspace handling

openclaw conflates "workspace dir" (file-tool root) with "persona dir"
(SOUL/AGENTS/IDENTITY/USER are loaded from workspace each session). Setting
`agents.defaults.workspace` to a fixed persona dir breaks file tools for tasks
that work on the per-task cwd. Setting it to the cwd means persona files must
exist in the cwd.

**Decision:** persona files are **staged** in the image at
`/opt/harness/openclaw-workspace/`. The thin adapter `cp -rn`s them into the
task cwd at run start (no-clobber, so task files always win). `skipBootstrap`
prevents the first-run ritual from creating generic alternatives. The risk
(verifier seeing persona MD files) is small in practice — they're distinctly
named and uppercase; current task verifiers check specific outputs.

If a future task verifier does a diff-style check, alternatives:
- A bespoke skipPersona flag in the adapter for those tasks.
- An openclaw upstream fix that decouples workspace dir from persona dir.

## Reasoning gate (mandatory; FOOTGUNS #1)

Every parity run MUST confirm reasoning_tokens > 0 (or non-empty
`reasoning_content`) **for both** harnesses. Verified 2026-05-29:

- openclaw: `reasoning_tokens = 161` across the run (parsed from
  `openclaw.session.jsonl`).
- hermes: 8 `reasoning_content` blocks / 1870 chars (the deepseek OpenRouter
  route returns a 0 token counter — `reasoning_tokens: 0` — but emits real
  reasoning text; presence of `reasoning_content` is the substantive signal).

Re-run this gate whenever the model, OpenRouter route, or rich-image config
changes.

## Verification reproducer

```bash
cd ~/harbor-tasks
# Build the rich image once (see Dockerfile in environments/agent-rich/).
docker build -f environments/agent-rich/Dockerfile -t harbor-agents-rich:latest .

# Mint an infisical token from env (never on cmdline). Self-hosted instance.
set -a; source ~/.config/infisical/infisical-identity.env; set +a
export INFISICAL_UNIVERSAL_AUTH_CLIENT_ID="$INFISICAL_CLIENT_ID" \
       INFISICAL_UNIVERSAL_AUTH_CLIENT_SECRET="$INFISICAL_CLIENT_SECRET"
export INFISICAL_TOKEN=$(infisical login --method=universal-auth --silent --plain \
                          --domain="${INFISICAL_SITE_URL%/}/api" 2>/dev/null)

# Run both harnesses on the parity task.
infisical run \
  --projectId INFISICAL_PROJECT_ID --env=production \
  --path=/proxy/ --domain="${INFISICAL_SITE_URL%/}/api" -- \
  uv run --project /home/trumble/harbor harbor run -c configs/verify-rich.yaml
```

Expected result: both rows show `Reward 1.000 / Exceptions 0` and the post-run
gate finds reasoning content in both session files.

## Open follow-ups (separate tasks)

- `#54` Verify CDP browser wiring for both harnesses.
- `#55` Sub-agent-spawning eval task.
- `#56` Research eval task.
- `#57` recall bge-m3 re-embed migration.

Reasoning the thin adapters cleanly don't try to solve: task-MCP merging beyond
what's baked, persona-cwd pollution for diff-style verifiers, and the upstream
openclaw workspace/persona conflation.

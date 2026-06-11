"""Thin OpenClaw adapter: invoke the BAKED rich config, never rebuild it.

The bundled Harbor adapter (and our OpenClawOpenRouter subclass) reconstruct
``~/.openclaw/openclaw.json`` from scratch on every run via
``_build_full_openclaw_config`` + a copy over the baked file (FOOTGUNS #12).
That threw away the harness's real config and forced every capability
(reasoning, memory, persona, skills) to be reverse-engineered field by field.

This adapter is the "STOP USING THE PACKAGED HARNESSES" path: the rich image
(`harbor-agents-rich`) bakes ``~/.openclaw/openclaw.json`` (custom ``xrouter``
provider with ``reasoning:true``, memory MCP servers, ``thinkingDefault:high``,
``skipBootstrap``) and stages persona files under
``/opt/harness/openclaw-workspace``. We only:

  1. forward the provider API key into the container,
  2. seed the persona into the task working dir (openclaw loads SOUL/AGENTS/
     IDENTITY/USER from the workspace = cwd every session; ``-n`` no-clobber so
     task files are never overwritten),
  3. run ``openclaw agent --local --json`` against the BAKED config,
  4. copy the session JSONL out for metrics.

Cost computation, the ``xrouter`` provider validation, and the ``--thinking``
flag are inherited from OpenClawOpenRouter. We do NOT call
``_build_full_openclaw_config`` — the baked config is authoritative.

Usage:

    harbor run --path tasks/... \
        --agent-import-path lib.openclaw_thin:OpenClawThin \
        --model xrouter/deepseek/deepseek-v4-pro

Requires XROUTER_API_KEY in env (the OpenRouter key; see FOOTGUNS #2).
"""

import os
import shlex

from harbor.agents.installed.openclaw import _nvm22
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from lib.openclaw_openrouter import OpenClawOpenRouter

# Where the image stages the persona workspace files (see agent-rich Dockerfile).
_BAKED_WORKSPACE = "/opt/harness/openclaw-workspace"


class OpenClawThin(OpenClawOpenRouter):
    """Invoke the rich baked openclaw config; no config regeneration."""

    async def install(self, environment: BaseEnvironment) -> None:
        # Rich image already has openclaw + the baked config; just verify.
        await self.exec_as_agent(
            environment,
            command=_nvm22("openclaw --version"),
            timeout_sec=30,
        )

    async def run(  # type: ignore[override]
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        instruction = self.render_instruction(instruction)

        if not self.model_name or "/" not in self.model_name:
            raise ValueError("Model name must be in the format provider/model_name")
        provider, _ = self.model_name.split("/", 1)
        self._validate_provider(provider)  # xrouter is in _SUPPORTED_PROVIDERS

        # Forward the OpenRouter key into the container; the baked config's
        # xrouter provider resolves ${OPENROUTER_API_KEY} at runtime. We read it
        # directly from the process env (infisical-injected) rather than relying
        # on Harbor substituting an environment.env passthrough — that
        # substitution doesn't reach the adapter's _get_env, which is what bit
        # the XROUTER_API_KEY approach (401 Missing Authentication header).
        # Mirrors the hermes thin adapter: one key (OPENROUTER_API_KEY) for both.
        env: dict[str, str] = {}
        openrouter_key = self._get_env("OPENROUTER_API_KEY") or os.environ.get(
            "OPENROUTER_API_KEY"
        )
        if not openrouter_key:
            raise ValueError("No API key found. Set OPENROUTER_API_KEY.")
        env["OPENROUTER_API_KEY"] = openrouter_key
        # Also honor an explicit XROUTER_* override if the operator set one.
        for key in self._provider_env_keys(provider):
            val = self._get_env(key)
            if val:
                env[key] = val

        # Persist the instruction for the trajectory converter.
        try:
            (self.logs_dir / "instruction.txt").write_text(instruction)
        except OSError:
            pass

        # Seed persona into the task working dir WITHOUT clobbering task files.
        # openclaw injects SOUL/AGENTS/IDENTITY/USER (Project Context) from the
        # workspace = cwd each session; skipBootstrap (baked) suppresses the
        # first-run ritual that would otherwise seed generic files.
        await self.exec_as_agent(
            environment,
            command=f"cp -rn {shlex.quote(_BAKED_WORKSPACE)}/. ./ 2>/dev/null || true",
            env=env,
        )

        cli_flags = self.build_cli_flags()
        cli_flags_arg = (cli_flags + " ") if cli_flags else ""
        # build_cli_flags() already emits `--agent main` (and `--thinking high`)
        # for the openclaw CLI; do NOT add another --agent or openclaw 2026.5.26+
        # will silently fail with `Unknown model: xrouter/...` because the
        # duplicated arg breaks model resolution.
        # Bring up the self-contained in-container headless Chromium before the
        # agent runs; openclaw's browser tool attaches to 127.0.0.1:9222 (baked
        # browser.cdpUrl). Idempotent + readiness-gated. Spec:
        # backlog/2026-06-03-self-contained-browser.md.
        # Multi-step session threading (OPT-IN per task). If the task image bakes
        # /opt/harness/thread-session, every step of the trial targets ONE explicit
        # openclaw session id (--session-id), so the conversation actually
        # accumulates across steps — required for the context tasks (context-fill /
        # context-rot) to exercise window overflow / in-window rot. Absent the
        # marker, each step is a FRESH session (the default): correct for single-
        # step tasks AND for the memory tasks, where facts must survive via the
        # memory MCP, not in-context. The per-trial container is isolated, so a
        # fixed id can't collide across pass^k repeats. Flag confirmed in-image:
        # `openclaw agent --session-id <id>`. Spec: 2026-06-10-core-eleven-remediation D1.
        command = (
            ". ~/.nvm/nvm.sh && nvm use 22 && "
            "bash /opt/harness/start-cdp.sh && "
            'SID=""; [ -f /opt/harness/thread-session ] && SID="--session-id harbor-trial"; '
            f"openclaw agent --local --json {cli_flags_arg}$SID "
            f"--model {shlex.quote(self.model_name)} "
            f"--message {shlex.quote(instruction)} "
            "2>&1 </dev/null | stdbuf -oL tee /logs/agent/openclaw.txt"
        )
        await self.exec_as_agent(environment, command, env=env)
        await self._copy_openclaw_session_file_to_agent_logs(environment, env)

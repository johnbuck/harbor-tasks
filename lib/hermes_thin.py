"""Thin Hermes adapter: invoke the BAKED rich home/config, never rebuild it.

The bundled Harbor adapter forces ``HERMES_HOME=/tmp/hermes`` (a fresh, empty
home) and writes a barebones ``config.yaml`` (memory off, no skills, no persona,
no reasoning) on every run (FOOTGUNS #12 / #13). That bypassed the installer's
seeded ``~/.hermes`` entirely, so hermes ran with 0 skills and reasoning off.

This adapter is the "STOP USING THE PACKAGED HARNESSES" path: the rich image
(`harbor-agents-rich`) bakes ``/root/.hermes`` with our rich ``config.yaml``
(deepseek via OpenRouter, ``agent.reasoning_effort: high``, ``provider_routing
data_collection: deny``, memory on, ``mcp_servers`` recall+hindsight,
``delegation``), ``SOUL.md`` persona, and the installer's 24 seeded skills. We
only:

  1. point HERMES_HOME at the baked rich home (NOT /tmp/hermes),
  2. forward the OpenRouter API key,
  3. run ``hermes --yolo chat`` against the BAKED config (model/provider/
     reasoning_effort/toolsets/skills all come from it),
  4. export the session JSONL for metrics.

We do NOT call ``_build_config_yaml`` — the baked config is authoritative.
Token/cost reading is inherited from HermesOpenRouter (reads
hermes-session.jsonl).

Usage:

    harbor run --path tasks/... \
        --agent-import-path lib.hermes_thin:HermesThin \
        --model deepseek/deepseek-v4-pro

Requires OPENROUTER_API_KEY in env.
"""

import os
import shlex

from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from lib.hermes_no_install import HermesOpenRouter

# Baked rich home in the image (installer seeds ~/.hermes; we overwrite its
# config.yaml + SOUL.md there in the Dockerfile). Container runs as root.
_BAKED_HERMES_HOME = "/root/.hermes"


class HermesThin(HermesOpenRouter):
    """Invoke the rich baked hermes home/config; no config regeneration."""

    async def install(self, environment: BaseEnvironment) -> None:
        # Rich image already has hermes + the baked home; just ensure the binary
        # resolves on PATH and verify.
        await self.exec_as_agent(
            environment,
            command=(
                'export PATH="$HOME/.local/bin:/usr/local/bin:$PATH"; '
                "ln -sf /usr/local/bin/hermes \"$HOME/.local/bin/hermes\" 2>/dev/null || true; "
                f"HERMES_HOME={shlex.quote(_BAKED_HERMES_HOME)} hermes version"
            ),
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

        # deepseek (and any non-native provider) routes through OpenRouter; the
        # baked config sets provider: openrouter + reasoning_effort: high.
        openrouter_key = os.environ.get("OPENROUTER_API_KEY") or self._get_env(
            "OPENROUTER_API_KEY"
        )
        if not openrouter_key:
            raise ValueError("No API key found. Set OPENROUTER_API_KEY.")

        env: dict[str, str] = {
            "HERMES_HOME": _BAKED_HERMES_HOME,
            "TERMINAL_ENV": "local",
            "OPENROUTER_API_KEY": openrouter_key,
            "HARBOR_INSTRUCTION": instruction,
        }

        # Run against the BAKED config. --model honors Harbor's model selection;
        # provider + reasoning_effort + toolsets + skills come from config.yaml.
        run_cmd = (
            'export PATH="$HOME/.local/bin:/usr/local/bin:$PATH" && '
            # #92 write-persistence fix: hermes's file tools are workspace-rooted
            # at the terminal backend's cwd (baked config `terminal.cwd: "."`).
            # If the process doesn't start in the task workdir, write_file lands
            # in a cwd-shadow the verifier (reading /app) never sees — the
            # context-rot-02 false-zero (write_file reported 85 bytes; /app stayed
            # empty). cd into /app so writes persist where they're graded.
            "cd /app && "
            "hermes --yolo chat "
            '-q "$HARBOR_INSTRUCTION" '
            "-Q "
            f"--model {shlex.quote(self.model_name)} "
            "2>&1 | stdbuf -oL tee /logs/agent/hermes.txt"
        )
        try:
            await self.exec_as_agent(environment, command=run_cmd, env=env)
        finally:
            try:
                await self.exec_as_agent(
                    environment,
                    command=(
                        'export PATH="$HOME/.local/bin:/usr/local/bin:$PATH" && '
                        "hermes sessions export /logs/agent/hermes-session.jsonl "
                        "--source cli 2>/dev/null || true"
                    ),
                    env={"HERMES_HOME": _BAKED_HERMES_HOME},
                    timeout_sec=30,
                )
            except Exception:
                pass

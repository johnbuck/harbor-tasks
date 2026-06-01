"""Hermes subclass that skips install + populates tokens/cost from session.

Two fixes over Harbor's bundled adapter:

1. install() is a no-op verify (assumes harbor-agents-prebaked base image).
2. populate_context_post_run reads the rich token + cost data hermes
   already writes to hermes-session.jsonl. Harbor's adapter only fills
   context from the ATIF-derived final_metrics, which in our trials came
   out as 0 — but the JSONL has input_tokens / cache_read_tokens /
   cache_write_tokens / output_tokens / estimated_cost_usd ready to go.
"""

import json

import yaml

from harbor.agents.installed.hermes import Hermes
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

# DETERMINISTIC SINGLE-HOST PIN — both harnesses pin to ONE upstream host so any
# token/cost/cache delta is the HARNESS, not OpenRouter load-balancer luck. An
# unpinned pool is NOT fair: the two harnesses load-balance independently and hit
# different hosts run-to-run. `require_parameters` keeps reasoning_effort intact.
# MUST stay byte-identical to lib/openclaw_openrouter.py and the two baked configs.
OPENROUTER_PROVIDER_ROUTING: dict = {
    "data_collection": "deny",
    "only": ["deepseek"],
    "allow_fallbacks": False,
    "require_parameters": True,
}


class HermesOpenRouter(Hermes):
    """Install-capable Hermes with the privacy provider pool + accurate cost.

    Use this for EXTERNAL benchmark task images (which lack the agent) — it
    self-installs via Hermes' bundled installer. For OUR prebaked-image tasks
    use HermesNoInstall (below), which skips the install.
    """

    @staticmethod
    def _build_config_yaml(model: str) -> str:
        base = Hermes._build_config_yaml(model)
        cfg = yaml.safe_load(base)
        # Hermes passes provider_routing through as extra_body.provider on
        # every OpenRouter call (no effect on direct-provider connections).
        cfg["provider_routing"] = dict(OPENROUTER_PROVIDER_ROUTING)
        return yaml.dump(cfg, default_flow_style=False)

    def populate_context_post_run(self, context: AgentContext) -> None:
        super().populate_context_post_run(context)
        self._populate_from_session_jsonl(context)

    def _populate_from_session_jsonl(self, context: AgentContext) -> None:
        """Read tokens + cost from hermes-session.jsonl as ground truth.

        Falls back to whatever super() set, but the session JSONL is the
        authoritative source — hermes writes it itself with its own cost
        accounting.
        """
        session_path = self.logs_dir / "hermes-session.jsonl"
        if not session_path.exists():
            return

        # Aggregate across all session entries in the file (usually 1 row).
        agg_input = agg_cache_read = agg_cache_write = agg_output = 0
        cost_estimate: float | None = None
        cost_actual: float | None = None

        try:
            for line in session_path.read_text().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                agg_input += int(row.get("input_tokens") or 0)
                agg_cache_read += int(row.get("cache_read_tokens") or 0)
                agg_cache_write += int(row.get("cache_write_tokens") or 0)
                agg_output += int(row.get("output_tokens") or 0)
                est = row.get("estimated_cost_usd")
                if est is not None:
                    cost_estimate = (cost_estimate or 0.0) + float(est)
                act = row.get("actual_cost_usd")
                if act is not None:
                    cost_actual = (cost_actual or 0.0) + float(act)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.logger.debug(
                f"Failed to parse hermes-session.jsonl for token/cost data: {exc}"
            )
            return

        # Convention (matching openclaw): n_input_tokens = real_input + cache_read.
        context.n_input_tokens = agg_input + agg_cache_read
        context.n_cache_tokens = agg_cache_read
        context.n_output_tokens = agg_output
        # Prefer actual cost when hermes has it; otherwise estimated.
        context.cost_usd = cost_actual if cost_actual is not None else cost_estimate


class HermesNoInstall(HermesOpenRouter):
    """Fast path for OUR prebaked-image tasks: skip the full install/setup."""

    async def install(self, environment: BaseEnvironment) -> None:
        await self.exec_as_agent(
            environment,
            # In the prebaked image hermes lives at /usr/local/bin/hermes, but
            # the stock Hermes.run() command only puts ~/.local/bin on PATH (where
            # hermes' own installer would place it). Symlink it there so both this
            # check AND the stock run command resolve `hermes`.
            command=(
                "set -euo pipefail; "
                'mkdir -p "$HOME/.local/bin"; '
                "ln -sf /usr/local/bin/hermes \"$HOME/.local/bin/hermes\"; "
                'export PATH="$HOME/.local/bin:$PATH"; '
                'export HERMES_HOME="${HERMES_HOME:-/tmp/hermes}" && '
                'mkdir -p "$HERMES_HOME" "$HERMES_HOME/sessions" "$HERMES_HOME/skills" "$HERMES_HOME/memories" && '
                "hermes version"
            ),
            timeout_sec=30,
        )

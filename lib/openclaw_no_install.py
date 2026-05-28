"""OpenClaw subclass that skips install + reports accurate cost.

Two improvements over the bundled adapter:

1. install() is a no-op verify (assumes harbor-agents-prebaked image),
   saving ~2-4 minutes per trial of network-bound work.

2. populate_context_post_run reads the raw openclaw.session.jsonl for
   per-step usage and includes cache_write tokens in cost. Harbor's
   FinalMetrics has no cache_write field; without this override the
   reported cost misses the 25%-premium cache-write rate (which can
   be the majority of a turn's cost for prompt-cached workflows).
"""

import json

from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext

from lib.openclaw_openrouter import OpenClawOpenRouter, _compute_cost_usd


class OpenClawNoInstallOpenRouter(OpenClawOpenRouter):
    async def install(self, environment: BaseEnvironment) -> None:
        await self.exec_as_agent(
            environment,
            command="openclaw --version",
            timeout_sec=30,
        )

    def populate_context_post_run(self, context: AgentContext) -> None:
        super().populate_context_post_run(context)
        self._populate_from_session_jsonl(context)

    def _populate_from_session_jsonl(self, context: AgentContext) -> None:
        """Recompute cost from openclaw.session.jsonl with cache_write."""
        session_path = self.logs_dir / "openclaw.session.jsonl"
        if not session_path.exists():
            return

        totals = {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0}
        try:
            for line in session_path.read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = row.get("message")
                if not isinstance(msg, dict):
                    continue
                usage = msg.get("usage")
                if not isinstance(usage, dict):
                    continue
                for k in totals:
                    totals[k] += int(usage.get(k) or 0)
        except OSError as exc:
            self.logger.debug(
                f"Failed to read openclaw.session.jsonl for cost data: {exc}"
            )
            return

        if not any(totals.values()):
            return

        # Update context.* to reflect raw session totals (in case super's
        # ATIF-derived values diverge), then recompute cost with cache_write.
        # Harbor's convention: n_input_tokens = real_input + cache_read.
        context.n_input_tokens = totals["input"] + totals["cacheRead"]
        context.n_cache_tokens = totals["cacheRead"]
        context.n_output_tokens = totals["output"]
        if self.model_name:
            context.cost_usd = _compute_cost_usd(
                self.model_name,
                real_input_tokens=totals["input"],
                output_tokens=totals["output"],
                cache_read_tokens=totals["cacheRead"],
                cache_write_tokens=totals["cacheWrite"],
            )

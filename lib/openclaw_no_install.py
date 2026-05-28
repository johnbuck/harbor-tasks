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

from harbor.environments.base import BaseEnvironment

from lib.openclaw_openrouter import OpenClawOpenRouter


class OpenClawNoInstallOpenRouter(OpenClawOpenRouter):
    """Fast path for OUR prebaked-image tasks: skip the ~2-4 min self-install.

    Cost (session-jsonl) + provider pool are inherited from OpenClawOpenRouter;
    only install() is overridden. For EXTERNAL benchmark task images (which lack
    the agent), use OpenClawOpenRouter directly so it self-installs.
    """

    async def install(self, environment: BaseEnvironment) -> None:
        await self.exec_as_agent(
            environment,
            command="openclaw --version",
            timeout_sec=30,
        )

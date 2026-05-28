"""Hermes subclass that skips the install step.

Assumes the task's environment Dockerfile FROM harbor-agents-prebaked,
which has hermes + its deps pre-installed. The default Hermes adapter
re-runs apt-get + curl-pipe-to-bash install.sh on every trial; that
took 6+ minutes in our first real trial and timed out at the 360s
default.
"""

from harbor.agents.installed.hermes import Hermes
from harbor.environments.base import BaseEnvironment


class HermesNoInstall(Hermes):
    async def install(self, environment: BaseEnvironment) -> None:
        # Verify the binary + ensure HERMES_HOME dirs exist (the upstream
        # install does this; we replicate just the non-network parts).
        await self.exec_as_agent(
            environment,
            command=(
                "set -euo pipefail; "
                'export HERMES_HOME="${HERMES_HOME:-/tmp/hermes}" && '
                'mkdir -p "$HERMES_HOME" "$HERMES_HOME/sessions" "$HERMES_HOME/skills" "$HERMES_HOME/memories" && '
                "hermes version"
            ),
            timeout_sec=30,
        )

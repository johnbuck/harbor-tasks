"""OpenClaw subclass that skips the install step.

Assumes the task's environment Dockerfile FROM harbor-agents-prebaked,
which has openclaw + node + nvm pre-installed. The default OpenClaw
adapter re-runs apt-get update, curl-pipe-to-bash nvm install,
nvm install 22, and npm install -g openclaw@latest on every trial,
each of which is idempotent but still hits the network and adds 2-4
minutes per trial.

Combines with OpenClawOpenRouter to also add openrouter provider
support.
"""

from harbor.environments.base import BaseEnvironment

from lib.openclaw_openrouter import OpenClawOpenRouter


class OpenClawNoInstallOpenRouter(OpenClawOpenRouter):
    """OpenClaw with OpenRouter + pre-baked-image fast-path install."""

    async def install(self, environment: BaseEnvironment) -> None:
        # Verify the binary is present; fail fast if the image isn't
        # what we expect.
        await self.exec_as_agent(
            environment,
            command="openclaw --version",
            timeout_sec=30,
        )

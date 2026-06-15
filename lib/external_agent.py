"""Drive a production agent the way it is actually invoked, capture the answer.

This generalizes the thin-adapter pattern (``lib/openclaw_thin.py``): instead of
a baked harness CLI, the invocation command is configurable so it matches the
real entrypoint of whatever agent runs in the attached container
(``ExternalContainerEnvironment``). It is the single point that knows HOW a given
production agent is driven.

``run()``:
  1. renders the user instruction into the ``invoke`` template, shell-quoting it
     so a hostile-looking message can never break out of the command,
  2. execs ``invoke`` in ``workdir`` against the handed environment,
  3. captures the response per the ``response`` mode
     (``stdout`` | ``file:<path>`` | ``json:<jsonpath>``),
  4. writes the captured transcript to ``logs_dir/external.txt`` on the HOST
     (``logs_dir`` is the trial's host-side agent dir) for the verifier to grade,
     and mirrors the instruction for the trajectory.

Cost/token capture is best-effort and omitted for the MVP (production agents
rarely emit OpenRouter-style usage; spec open question #3).
"""

from __future__ import annotations

import json
import shlex
from pathlib import Path

from harbor.agents.base import BaseAgent
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


class ExternalAgentAdapter(BaseAgent):
    """Invoke a production agent via a configurable command and capture output."""

    SUPPORTS_ATIF = False

    def __init__(
        self,
        *args,
        invoke: str,
        response: str = "stdout",
        workdir: str | None = None,
        **kwargs,
    ):
        if not invoke:
            raise ValueError("ExternalAgentAdapter requires an 'invoke' command.")
        self._invoke = invoke
        self._response = response
        self._workdir = workdir
        super().__init__(*args, **kwargs)

    @staticmethod
    def name() -> str:
        return "external-agent"

    def version(self) -> str | None:
        return "0.1.0"

    async def setup(self, environment: BaseEnvironment) -> None:
        # No install: the production agent already exists in its container. A
        # heavier preflight (docker inspect / a healthcheck) is the environment's
        # job; nothing to set up here.
        return

    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        command = self._invoke.replace("{instruction}", shlex.quote(instruction))

        # Persist the instruction for the trajectory converter (best-effort).
        try:
            (self.logs_dir / "instruction.txt").write_text(instruction)
        except OSError:
            pass

        result = await environment.exec(command, cwd=self._workdir)

        # A nonzero invoke (crash, CLI error, OOM) is an INFRA failure, not a wrong
        # answer. Do NOT write external.txt in that case: the host-side verifier
        # keys answer_present on the file's existence, so a missing file scores the
        # trial VOID (answer_present=0) instead of manufacturing a false 0.0 LOSS
        # that is indistinguishable from a genuinely wrong response.
        if result.return_code != 0:
            return

        captured = await self._capture(result, environment)

        (self.logs_dir / "external.txt").write_text(captured)

    async def _capture(self, result, environment: BaseEnvironment) -> str:
        if self._response == "stdout":
            return result.stdout or ""

        if self._response.startswith("file:"):
            source = self._response[len("file:") :]
            target = self.logs_dir / "external_download.tmp"
            await environment.download_file(source, target)
            return Path(target).read_text()

        if self._response.startswith("json:"):
            json_path = self._response[len("json:") :]
            data = json.loads(result.stdout or "{}")
            for key in json_path.split("."):
                if not isinstance(data, dict) or key not in data:
                    raise ValueError(
                        f"response json path {json_path!r} does not resolve: "
                        f"missing key {key!r}."
                    )
                data = data[key]
            return data if isinstance(data, str) else json.dumps(data)

        raise ValueError(
            f"Unknown response mode {self._response!r}; expected 'stdout', "
            "'file:<path>', or 'json:<jsonpath>'."
        )

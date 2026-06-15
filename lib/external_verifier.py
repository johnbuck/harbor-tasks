"""Grade a captured conversational transcript HOST-side, off the prod container.

For the production-agent eval mode (spec 2026-06-12) the agent runs in a foreign
container with no ``/app`` and no eval backend; the thing to grade is the
RESPONSE the agent gave, captured by ``ExternalAgentAdapter`` to the trial's
host-side ``agent_dir/external.txt``. Harbor's verifier normally runs in the task
container — this verifier instead reads the captured transcript on the host and
ignores ``self.environment`` entirely (it is the foreign prod container, which we
must not touch).

It reuses the ordinary rewardkit-grader authoring pattern: it stages the
transcript as the answer file a normal recall grader expects (``answer.md`` by
default), then runs the task's rewardkit grader on the host (rewardkit is
importable in the harbor venv). This lets conversational tasks author graders
exactly like every other task.

VOID-vs-loss discipline (per the discrimination methodology): a MISSING transcript
emits ``answer_present=0`` — a VOID, not a false ``0.0`` loss. A present-but-wrong
transcript is a real ``0.0`` with ``answer_present=1``.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from harbor.models.verifier.result import VerifierResult
from harbor.verifier.base import BaseVerifier

_TRANSCRIPT_FILENAME = "external.txt"

_REWARDKIT_RUNNER = (
    "import sys, rewardkit\n"
    "rewardkit.run(sys.argv[1], workspace=sys.argv[2], output=sys.argv[3])\n"
)


class ExternalTranscriptVerifier(BaseVerifier):
    """Grade ``agent_dir/external.txt`` with the task's host-side rewardkit grader."""

    def __init__(
        self,
        *,
        tests_dir: str | None = None,
        answer_filename: str = "answer.md",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._tests_dir = tests_dir
        self._answer_filename = answer_filename

    async def verify(self) -> VerifierResult:
        transcript = self.trial_paths.agent_dir / _TRANSCRIPT_FILENAME

        if not transcript.exists():
            # VOID: the agent never persisted a response. Not a false 0.0 loss.
            self.logger.warning(
                "ExternalTranscriptVerifier: no transcript at %s; emitting VOID "
                "(answer_present=0).",
                transcript,
            )
            return VerifierResult(rewards={"reward": 0.0, "answer_present": 0})

        if not self._tests_dir:
            raise RuntimeError(
                "ExternalTranscriptVerifier requires 'tests_dir' (the directory of "
                "the rewardkit grader for this conversational task)."
            )

        flat = self._grade(transcript.read_text())

        rewards: dict[str, float | int] = {"answer_present": 1}
        for key, value in flat.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                rewards[key] = value
        rewards.setdefault("reward", 0.0)
        return VerifierResult(rewards=rewards)

    def _grade(self, transcript_text: str) -> dict:
        """Stage the transcript as the answer file and run the rewardkit grader."""
        with tempfile.TemporaryDirectory() as ws_str:
            workspace = Path(ws_str)
            (workspace / self._answer_filename).write_text(transcript_text)
            out = workspace / "reward.json"

            proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    _REWARDKIT_RUNNER,
                    str(self._tests_dir),
                    str(workspace),
                    str(out),
                ],
                capture_output=True,
                text=True,
                timeout=180,
            )
            if proc.returncode != 0:
                raise RuntimeError(
                    f"rewardkit grading failed for {self._tests_dir}:\n"
                    f"{proc.stdout}\n{proc.stderr}"
                )
            return json.loads(out.read_text())

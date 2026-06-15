"""Minimal rewardkit grader FIXTURE for the ExternalTranscriptVerifier test.

This is test infrastructure, not a production task grader. It mirrors the real
recall-grader pattern (read ``answer.md`` from the workspace, score a fact,
ride ``answer_present`` along at weight 0) so the verifier-under-test can stage
the captured transcript as ``answer.md`` and grade it host-side exactly as it
would a real conversational task.

Reward = 1.0 iff the staged transcript names PARIS as the capital, else 0.0.
"""
from pathlib import Path

import rewardkit as rk


def _answer_text(workspace) -> str:
    p = Path(workspace) / "answer.md"
    return (p.read_text() if p.exists() else "").lower()


@rk.criterion(description="capital == paris")
def capital(workspace: Path) -> bool:
    return "paris" in _answer_text(workspace)


capital_inst = rk.capital()

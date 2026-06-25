"""rewardkit grader for prod-behavioral-basic-knowledge-qa.

The production-agent eval mode captures the external agent's response to the trial's
host-side ``agent_dir/external.txt``; ``ExternalTranscriptVerifier`` stages that text
as ``answer.md`` in a fresh workspace and runs THIS grader on the host (it never
touches the prod container). The verifier rides ``answer_present`` alongside the
reward to distinguish a VOID (no transcript) from a present-but-wrong loss, so this
grader scores only the fact.

reward = 1.0 iff the captured answer names PARIS as the capital, else 0.0.
"""
from pathlib import Path

import rewardkit as rk


def _answer_text(workspace: Path) -> str:
    p = Path(workspace) / "answer.md"
    return (p.read_text(encoding="utf-8", errors="replace") if p.exists() else "").lower()


@rk.criterion(description="capital of France == Paris")
def capital(workspace: Path) -> bool:
    return "paris" in _answer_text(workspace)


capital_inst = rk.capital()

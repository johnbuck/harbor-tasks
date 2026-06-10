"""rewardkit grader for shell-pipeline-01 — log-analysis pipeline.

Five independent KEY=value sub-results in /app/answer.txt, each an equal-weight
criterion; reward = correct/5. Each is gated on the access.log being untouched
(tamper check vs the pristine /opt/canonical copy). Replaces the bespoke bash
grader; rewardkit guarantees the flat reward.json + per-criterion breakdown.
"""
from pathlib import Path

import rewardkit as rk

# Ground truth, computed from the baked access.log (see solution/solve.sh).
EXPECTED = {
    "TOP_500_IP": "10.0.0.2",        # tie at 3x500 broken by total volume
    "TOTAL_5XX": "10",               # 500..599 (502/503 included)
    "DISTINCT_5XX_IPS": "5",
    "TOP_4XX_PATH": "/search",       # query string stripped
    "TOTAL_2XX_BYTES": "440",        # "-" counts as 0
}
CANONICAL_LOG = Path("/opt/canonical/access.log")


def _answer(workspace: Path) -> dict:
    out = {}
    p = workspace / "answer.txt"
    if p.exists():
        for line in p.read_text().splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                out[k.strip()] = v.strip()
    return out


def _tampered(workspace: Path) -> bool:
    """True if the agent altered the input log (would invalidate the answers)."""
    try:
        return (workspace / "access.log").read_bytes() != CANONICAL_LOG.read_bytes()
    except FileNotFoundError:
        return True


@rk.criterion(description="{key} correct")
def field(workspace: Path, key: str) -> bool:
    if _tampered(workspace):
        return False
    return _answer(workspace).get(key) == EXPECTED[key]


for _key in EXPECTED:
    rk.field(_key)

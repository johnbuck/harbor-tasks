"""rewardkit grader for refresh-config-over-cached-value / 04-query.

Stale-memory-vs-live-file: a value the agent memorized early (45) is silently
changed in the file to 275 before the query. reward = 1.0 iff /app/answer.txt
reports the CURRENT re-fetched value (275) AND does NOT also carry the stale
memorized value (45) — i.e. exclusivity, so hedging by dumping "45 and 275"
forfeits the point (S3). An HONEST update note ("275 (was 45)", "updated from
45") is carved out: acknowledging the prior value while reporting the current one
is correct, not stale. The single scored criterion (weight 1) is this exclusive
check; the legacy current/stale signals ride along weight-0 as diagnostics.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk


@lru_cache(maxsize=4)
def _text(workspace_str: str) -> str:
    p = Path(workspace_str) / "answer.txt"
    return p.read_text() if p.exists() else ""


def _nums(workspace_str: str) -> tuple:
    return tuple(re.findall(r"\d+", _text(workspace_str)))


# Honest "I know it used to be 45, it is now 275" phrasings — these acknowledge
# the prior value rather than report it as the answer, so they are NOT stale.
_CARVEOUT = re.compile(
    r"\bwas\s+45\b"
    r"|previous(?:ly)?[^.\n]*\b45\b"
    r"|updated\s+from\s+45\b"
    r"|45\s*(?:->|=>|→)"
    r"|old(?:er)?[^.\n]*\b45\b"
    r"|formerly[^.\n]*\b45\b",
    re.I,
)


def _stale_present(workspace_str: str) -> bool:
    """True iff the stale value 45 is reported (not merely noted as the old value)."""
    nums = _nums(workspace_str)
    if "45" not in nums:
        return False
    return not _CARVEOUT.search(_text(workspace_str))


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str) -> bool:
    ws = str(workspace)
    if key == "answered_current_exclusive":
        return ("275" in _nums(ws)) and not _stale_present(ws)
    if key == "answered_current":
        return "275" in _nums(ws)            # diagnostic: current value present
    if key == "not_stale":
        return not _stale_present(ws)        # diagnostic: did not echo stale 45
    return (Path(ws) / "answer.txt").exists()   # file_present


rk.check("answered_current_exclusive",
         "reported the current value (275) and not the stale 45", weight=1.0)
rk.check("answered_current", "current value (275) present", weight=0.0)
rk.check("not_stale", "did not return the stale memorized value (45)", weight=0.0)
rk.check("file_present", "answer.txt present", weight=0.0)

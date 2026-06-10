"""rewardkit grader for multistep-stale-memory-vs-file-01 / 04-query.

Stale-memory-vs-live-file: a value the agent memorized early (45) is silently
changed in the file to 275 before the query. reward = 1.0 iff /app/answer.txt
reports the CURRENT re-fetched value (275); returning the stale 45 (or neither)
scores 0. Single scored criterion (weight 1) = current value present; stale/file
diagnostics ride along weight-0. Same number-token check as the prior grader.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk


@lru_cache(maxsize=4)
def _nums(workspace_str: str) -> tuple:
    p = Path(workspace_str) / "answer.txt"
    return tuple(re.findall(r"\d+", p.read_text())) if p.exists() else ()


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str) -> bool:
    nums = _nums(str(workspace))
    if key == "answered_current":
        return "275" in nums            # ground-truth value after the silent change
    if key == "not_stale":
        return "45" not in nums         # diagnostic: didn't echo the memorized stale value
    return (Path(str(workspace)) / "answer.txt").exists()   # file_present


rk.check("answered_current", "reported the current re-fetched value (275)", weight=1.0)
rk.check("not_stale", "did not return the stale memorized value (45)", weight=0.0)
rk.check("file_present", "answer.txt present", weight=0.0)

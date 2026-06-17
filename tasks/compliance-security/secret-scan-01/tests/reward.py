"""rewardkit grader for secret-scan-01 — precision+recall over secret-bearing files.

The repo has 4 files with real hardcoded secrets and 3 clean/decoy files (one a
placeholder-only decoy that LOOKS like secrets). reward = max(0, found - fp)/4 —
flagging a clean/decoy file SUBTRACTS (the precision penalty is the difficulty).
Same normalization + file sets as the prior bash grader.

Penalty pattern (see pr-diff-review-01): the exact formula lives in a weight-1
`score` criterion; per-file detection + the precision check ride along as weight-0
informational criteria.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

SECRET = {"auth.py", "config.py", "db.py", "deploy/id_rsa"}
CLEAN = {"utils.py", "README.md", "example_settings.py"}
N = 4


@lru_cache(maxsize=4)
def _seen(workspace_str: str) -> frozenset:
    """Normalized set of files the agent flagged in /app/findings.txt."""
    p = Path(workspace_str) / "findings.txt"
    if not p.exists():
        return frozenset()
    out = set()
    for line in p.read_text(errors="replace").splitlines():
        s = line.strip()
        if not s:
            continue
        s = re.sub(r'^/app/repo/', '', s)
        s = re.sub(r'^repo/', '', s)
        s = re.sub(r'^\./', '', s)
        out.add(s)
    return frozenset(out)


def _found_fp(workspace: Path):
    seen = _seen(str(workspace))
    return len(SECRET & seen), len(CLEAN & seen)


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    found, fp = _found_fp(workspace)
    if key == "score":
        # 2x FP weight: a zero-precision dump-everything drives the score to ~0.
        return max(0, found - 2 * fp) / N
    if key == "no_false_positives":
        return fp == 0
    return key in _seen(str(workspace))  # per-secret-file detection


rk.check("score", "reward = max(0, found - false_positives) / 4", weight=1.0)
for _f in sorted(SECRET):
    rk.check(_f, f"detected secret in {_f}", weight=0.0)
rk.check("no_false_positives", "precision: flagged no clean/decoy files", weight=0.0)


# VOID-vs-wrong diagnostic (weight-0; never moves the FLAT reward -- FOOTGUNS #2).
@rk.criterion(description="{label}")
def present(workspace: Path, key: str, label: str):
    p = Path(workspace) / "findings.txt"
    return p.exists() and bool(p.read_text(errors="replace").strip())


rk.present("answer_present", "answer persisted (VOID vs present-but-wrong)", weight=0.0)

"""rewardkit grader for multistep-context-fill-02 / 19-recall.

Long-context UPDATE-trap: 12 facts each updated mid-stream; the recall must report
the CURRENT value (+1) and not a stale/intermediate one (-1 each). reward =
max(0, current_hits - stale_hits)/12. Same patterns as the prior bash grader; the
net formula lives in a weight-1 `score` criterion, per-fact recall + no-stale are
weight-0 detail.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

CURRENT = {  # fact -> current-value pattern (+1 each)
    "lead": "okafor", "date": "2026-10-30", "version": r"2\.8", "nodes": r"\b32 node",
    "region": "eu-central-1", "db": "aurora", "deploy": "blue[ -]green",
    "window": "90[ -]?min|ninety[ -]?min", "topology": "multi[ -]primary",
    "monitoring": "datadog", "compliance": "soc ?2", "location": "dallas",
}
STALE = [  # any present -> -1 each
    "reyes", "tanaka", "2026-08-01", "2026-09-15", r"2\.0", r"\b48 node", r"\b64 node",
    "us-east-1", "us-west-2", "postgresql ?14|postgres ?14|pg ?14",
    "postgresql ?16|postgres ?16|pg ?16", "big[ -]bang", "phased", r"\b4 hour|four hour",
    "single[ -]primary", "gcp|google cloud",
]
TOTAL = 12


@lru_cache(maxsize=4)
def _text(workspace_str: str) -> str:
    p = Path(workspace_str) / "answer.md"
    return p.read_text().lower() if p.exists() else ""


def _hit(pat: str, text: str) -> bool:
    return re.search(pat, text) is not None


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    text = _text(str(workspace))
    if key == "score":
        cur = sum(1 for p in CURRENT.values() if _hit(p, text))
        stale = sum(1 for p in STALE if _hit(p, text))
        return max(0, cur - stale) / TOTAL
    if key == "no_stale":
        return not any(_hit(p, text) for p in STALE)
    return _hit(CURRENT[key], text)   # per-fact current recall


rk.check("score", "reward = max(0, current_hits - stale_hits)/12", weight=1.0)
for _k in CURRENT:
    rk.check(_k, f"current value recalled: {_k}", weight=0.0)
rk.check("no_stale", "no stale/intermediate values leaked", weight=0.0)

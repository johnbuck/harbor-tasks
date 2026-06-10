"""rewardkit grader for multistep-context-fill-01 / 19-recall.

Long-context UPDATE-trap: 12 facts updated mid-stream; recall the CURRENT value
(+1), not a stale one (-1 each). reward = max(0, current_hits - stale_hits)/12.
Same patterns as the prior bash grader; net formula in a weight-1 `score`
criterion, per-fact recall + no-stale weight-0.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

CURRENT = {
    "lead": "okonkwo", "product": "cardinal",
    "timeline": "2027[ -]q4|q4[ -]2027|q4 of 2027", "version": r"5\.1",
    "satellites": "(4|four) satellite", "battery": "b12", "os": r"orbitos ?3\.1",
    "supplier": "northwind", "warranty": "(7|seven) year", "date": "2026-03-15",
    "location": "phoenix", "refrigerant": "r-?32",
}
STALE = [
    r"\bvance\b", "brightpath", "2027[ -]q3|q3[ -]2027|q3 of 2027",
    "2028[ -]q1|q1[ -]2028|q1 of 2028", r"4\.2", "(6|six) satellite",
    "(12|twelve) year", "denver", "r-?410a",
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
    return _hit(CURRENT[key], text)


rk.check("score", "reward = max(0, current_hits - stale_hits)/12", weight=1.0)
for _k in CURRENT:
    rk.check(_k, f"current value recalled: {_k}", weight=0.0)
rk.check("no_stale", "no stale/intermediate values leaked", weight=0.0)

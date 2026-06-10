"""rewardkit grader for multistep-memory-conversational-03 / recall.

Graded recall under PRECISION pressure: 12 of MY facts, reward = recalled/12. Each
fact needs MY value(s) present in /app/answer.md AND the planted SIBLING absent.
One criterion per fact (exact has/no patterns of the prior bash grader).
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

FACTS = {
    "pet":         (["comet"],                                          ["waffles"]),
    "allergy":     (["shellfish"],                                      ["bee sting"]),
    "birthday":    (["june 22|june 22nd|6/22|06/22|june twenty"],       []),
    "profession":  (["structural engineer"],                           []),
    "movie":       (["blade runner 2049"],                             [r"\barrival\b"]),
    "hometown":    (["boise"],                                          ["reno"]),
    "car":         (["toyota", "tacoma", "red|2018"],                   ["corolla|black"]),
    "kids":        (["lena", "mira"],                                   []),
    "colour":      (["olive"],                                          ["maroon"]),
    "floor":       (["12th floor|floor 12|12th|twelfth"],              [r"3rd floor|floor 3\b|third floor"]),
    "coffee":      (["double espresso"],                                []),
    "gym_day":     (["saturday"],                                       ["sunday"]),
}


@lru_cache(maxsize=4)
def _answer(workspace_str: str) -> str:
    p = Path(workspace_str) / "answer.md"
    return p.read_text().lower() if p.exists() else ""


@rk.criterion(description="recalled: {key}")
def fact(workspace: Path, key: str) -> bool:
    text = _answer(str(workspace))
    present, absent = FACTS[key]
    if not all(re.search(p, text) for p in present):
        return False
    return not any(re.search(p, text) for p in absent)


for _key in FACTS:
    rk.fact(_key)

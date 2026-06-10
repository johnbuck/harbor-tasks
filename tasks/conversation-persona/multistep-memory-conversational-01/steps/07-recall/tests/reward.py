"""rewardkit grader for multistep-memory-conversational-01 / 07-recall.

Graded recall under PRECISION pressure: 12 of MY facts, reward = recalled/12. Each
fact earns a point only when /app/answer.md states MY value(s) AND does NOT contain
the planted SIBLING value (an agent that confuses the distractor, or hedges by
dumping both, forfeits that fact). One criterion per fact (preserves the exact
has/no grep patterns of the prior bash grader); weighted_mean = recalled/12.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

# key: (must-be-PRESENT patterns [all required], must-be-ABSENT patterns [sibling]).
FACTS = {
    "cats":        (["pixel", "byte"],                              ["mochi"]),
    "allergy":     (["peanut"],                                     ["shellfish"]),
    "birthday":    (["march 1?4|3/14|03/14|march fourteen"],        [r"march 4\b|march fourth|3/4\b|03/04"]),
    "profession":  (["marine biologist"],                          ["geologist"]),
    "book":        (["left hand of darkness"],                     [r"\bdune\b"]),
    "hometown":    (["asheville"],                                 ["portland"]),
    "car":         (["subaru", "outback", "blue|2019"],            [r"\bhonda\b"]),
    "sister":      (["robin"],                                     []),
    "colour":      (["teal"],                                      ["crimson"]),
    "coffee":      (["cortado"],                                   []),
    "gym_day":     (["tuesday"],                                   []),
    "anniversary": (["june 2|6/2|june second"],                    []),
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

"""rewardkit grader for recall-details-across-task-switching / recall.

Graded recall under PRECISION pressure: 12 of MY facts, reward = recalled/12. Each
fact needs MY value(s) present in /app/answer.md AND the planted SIBLING absent.
One criterion per fact (exact has/no patterns of the prior bash grader).
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

FACTS = {
    "food":        (["saffron", "pepper"],                              ["biscuit"]),
    "allergy":     (["penicillin"],                                     ["lactose"]),
    "birthday":    (["august 9|8/9|08/9|august ninth|august nine"],     ["november 12|11/12|november twelfth"]),
    "profession":  (["architect"],                                      []),
    "book":        (["cloud atlas"],                                    []),
    "hometown":    (["madison"],                                        ["denver"]),
    "car":         (["mazda", "cx-5|cx5|cx 5", "green|2021"],           [r"silver|mazda 3\b|mazda3"]),
    "sibling":     (["devan"],                                          []),
    "colour":      (["amber"],                                          []),
    "spice":       (["cardamom"],                                       []),
    "gym_day":     (["thursday"],                                       ["monday"]),
    "anniversary": (["october 5|10/5|10/05|october fifth"],             []),
}


@lru_cache(maxsize=4)
def _answer(workspace_str: str) -> str:
    p = Path(workspace_str) / "answer.md"
    return p.read_text(errors="replace").lower() if p.exists() else ""


@rk.criterion(description="recalled: {key}")
def fact(workspace: Path, key: str) -> bool:
    text = _answer(str(workspace))
    present, absent = FACTS[key]
    if not all(re.search(p, text) for p in present):
        return False
    return not any(re.search(p, text) for p in absent)


for _key in FACTS:
    rk.fact(_key)


# VOID-vs-wrong diagnostic (weight-0; never moves the FLAT reward -- FOOTGUNS #2).
@rk.criterion(description="{label}")
def present(workspace: Path, key: str, label: str):
    p = Path(workspace) / "answer.md"
    return p.exists() and bool(p.read_text(errors="replace").strip())


rk.present("answer_present", "answer persisted (VOID vs present-but-wrong)", weight=0.0)

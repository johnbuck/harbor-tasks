"""rewardkit grader for multistep-context-fill-03 / 19-recall.

Cross-talk trap: two projects (orion, lyra) each have 6 attributes with swapped
sibling values. Scoring is LINE-ANCHORED — for each (project, attribute) slot, the
correct value must appear on a line that mentions both the project and the
attribute (+1); the sibling's value on that line is -1. A distractor project
(nova/reykjavik/9.9) anywhere is -1. reward = max(0, net)/12. Same line()/on()
logic as the prior bash grader; net formula in a weight-1 `score` criterion,
per-slot correctness weight-0.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

# (key, project_pat, attribute_pat, correct_pat, sibling_pat)
SLOTS = [
    ("orion_lead",      "orion", "lead",                    "marsh",                    "crane"),
    ("lyra_lead",       "lyra",  "lead",                     "crane",                    "marsh"),
    ("orion_budget",    "orion", "budget",                   r"7\.4",                    r"3\.6"),
    ("lyra_budget",     "lyra",  "budget",                   r"3\.6",                    r"7\.4"),
    ("orion_site",      "orion", "site",                     "k9",                       "frankfurt"),
    ("lyra_site",       "lyra",  "site",                     "frankfurt",                "k9"),
    ("orion_vendor",    "orion", "vendor|partner",           "heliosat",                 "brightlink"),
    ("lyra_vendor",     "lyra",  "vendor|partner",           "brightlink",               "heliosat"),
    ("orion_headcount", "orion", "headcount|engineer",       r"\b38",                    r"\b52"),
    ("lyra_headcount",  "lyra",  "headcount|engineer",       r"\b52",                    r"\b38"),
    ("orion_golive",    "orion", "go-live|schedule|launch",  "2027[ -]?q2|q2[ -]?2027",  "2026[ -]?q4|q4[ -]?2026"),
    ("lyra_golive",     "lyra",  "go-live|schedule|launch",  "2026[ -]?q4|q4[ -]?2026",  "2027[ -]?q2|q2[ -]?2027"),
]
SLOT = {s[0]: s[1:] for s in SLOTS}
DISTRACTOR = r"nova|reykjavik|9\.9"
TOTAL = 12


@lru_cache(maxsize=4)
def _text(workspace_str: str) -> str:
    p = Path(workspace_str) / "answer.md"
    return p.read_text(errors="replace").lower() if p.exists() else ""


def _line(text: str, project: str, attr: str) -> str:
    """Lines mentioning BOTH the project and the attribute (grep p | grep attr)."""
    return "\n".join(l for l in text.splitlines()
                     if re.search(project, l) and re.search(attr, l))


def _slot_net(text: str, project: str, attr: str, correct: str, sibling: str) -> int:
    ln = _line(text, project, attr)
    return (1 if re.search(correct, ln) else 0) - (1 if re.search(sibling, ln) else 0)


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    text = _text(str(workspace))
    if key == "score":
        s = sum(_slot_net(text, *SLOT[k]) for k in SLOT)
        if re.search(DISTRACTOR, text):
            s -= 1
        return max(0, s) / TOTAL
    if key == "no_distractor":
        return re.search(DISTRACTOR, text) is None
    return _slot_net(text, *SLOT[key]) == 1   # slot cleanly correct (+1 net)


rk.check("score", "reward = max(0, net slot score - distractor)/12", weight=1.0)
for _k in SLOT:
    rk.check(_k, f"correct on its line: {_k}", weight=0.0)
rk.check("no_distractor", "no nova/reykjavik distractor leaked", weight=0.0)


# VOID-vs-wrong diagnostic (weight-0; never moves the FLAT reward -- FOOTGUNS #2).
@rk.criterion(description="{label}")
def present(workspace: Path, key: str, label: str):
    p = Path(workspace) / "answer.md"
    return p.exists() and bool(p.read_text(errors="replace").strip())


rk.present("answer_present", "answer persisted (VOID vs present-but-wrong)", weight=0.0)

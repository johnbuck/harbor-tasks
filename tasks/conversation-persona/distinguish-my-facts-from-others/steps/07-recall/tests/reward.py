"""rewardkit grader for distinguish-my-facts-from-others / 07-recall.

Graded recall under PRECISION pressure: 12 of MY facts, reward = recalled/12. Each
fact earns a point only when its answer line states MY value(s) AND does NOT leak the
planted SIBLING value as if it were the answer.

D5 anchoring (kills false-zeros): each question maps to ONE answer line (the
enumerated line `N.`, else the N-th non-preamble line — same `_cell_for` logic as
the context-rot grader). The accept + sibling-reject patterns run ONLY on that line,
so a sibling value mentioned for a DIFFERENT fact can never zero this one.

Same-line disambiguation rule: a sibling token is a leak only when it is NOT in a
negation/contrast context on that line. "peanuts (not shellfish)" / "March 14, not
March 4" PASS (correct value present, sibling explicitly negated); "peanuts and
shellfish" / a bare sibling FAIL (dump-both or confusion). weighted_mean = recalled/12;
answer_present rides along weight-0 (VOID vs present-but-wrong).
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

# key: (question number, must-be-PRESENT [all required], sibling must-be-ABSENT-unless-negated).
FACTS = {
    "cats":        (1,  ["pixel", "byte"],                       ["mochi"]),
    "allergy":     (2,  ["peanut"],                              ["shellfish"]),
    "birthday":    (3,  [r"march 14\b|3/14|03/14|march fourteen"], [r"march 4\b|march fourth|3/4\b|03/04"]),
    "profession":  (4,  ["marine biologist"],                   ["geologist"]),
    "book":        (5,  ["left hand of darkness"],              [r"\bdune\b"]),
    "hometown":    (6,  ["asheville"],                          ["portland"]),
    "car":         (7,  ["subaru", "outback", "blue|2019"],     [r"\bhonda\b"]),
    "sister":      (8,  ["robin"],                              []),
    "colour":      (9,  ["teal"],                               ["crimson"]),
    "coffee":      (10, ["cortado"],                            []),
    "gym_day":     (11, ["tuesday"],                            []),
    "anniversary": (12, ["june 2|6/2|june second"],            []),
}

# Negation / contrast / attribution cues that mark a sibling as deliberately
# excluded (not asserted as MY value). Checked on BOTH sides of the sibling token
# so a trailing disambiguator ("March 4 is my neighbor's") counts as well as a
# leading one ("not March 4").
NEG_CUE = re.compile(
    r"\bnot\b|n't|no longer|\bnever\b|rather than|instead of|as opposed to|"
    r"\bunlike\b|\bwas\b|\bwere\b|previously|formerly|used to|\bavoid|"
    r"neighbou?r|coworker|colleague|\bfriend|brother|sister|someone else|"
    r"\bhis\b|\bher\b|\btheir\b|belongs to"
)


@lru_cache(maxsize=4)
def _lines(workspace_str: str) -> tuple:
    p = Path(workspace_str) / "answer.md"
    return tuple((p.read_text() if p.exists() else "").split("\n"))


def _is_preamble(ln: str) -> bool:
    s = ln.strip()
    if s.startswith("#"):
        return True
    return bool(re.match(r"(?i)^(here|below|the following|answers?|my answers?)\b.*:\s*$", s))


def _strip_marks(s: str) -> str:
    s = re.sub(r"^\s*\d+\s*[.)\]:>-]\s*", "", s)
    s = re.sub(r"[*_`#>]", "", s)
    return s


def _cell_for(workspace_str: str, n: int) -> str:
    lines = _lines(workspace_str)
    enum = re.compile(rf"^\s*{n}\s*[.)\]:>-]")
    for ln in lines:
        if enum.match(ln):
            return _strip_marks(ln).lower()
    nonempty = [ln for ln in lines if ln.strip() and not _is_preamble(ln)]
    return _strip_marks(nonempty[n - 1]).lower() if n - 1 < len(nonempty) else ""


def _sibling_leaked(cell: str, pat: str) -> bool:
    """True if the sibling value is asserted (present and NOT explicitly negated).

    The disambiguator may sit before OR after the sibling token, so both windows
    are inspected ("not March 4" and "March 4 is my neighbor's" both clear it).
    """
    for m in re.finditer(pat, cell):
        pre = cell[max(0, m.start() - 28):m.start()]
        post = cell[m.end():m.end() + 28]
        if not (NEG_CUE.search(pre) or NEG_CUE.search(post)):
            return True
    return False


@rk.criterion(description="recalled: {key}")
def fact(workspace: Path, key: str) -> bool:
    qnum, present, absent = FACTS[key]
    cell = _cell_for(str(workspace), qnum)
    if not cell or not all(re.search(p, cell) for p in present):
        return False
    return not any(_sibling_leaked(cell, p) for p in absent)


@rk.criterion(description="{label}")
def meta(workspace: Path, key: str, label: str):
    if key == "answer_present":
        return any(ln.strip() and not _is_preamble(ln) for ln in _lines(str(workspace)))
    return 0.0


for _key in FACTS:
    rk.fact(_key)
rk.meta("answer_present", "answer persisted (VOID vs present-but-wrong)", weight=0.0)

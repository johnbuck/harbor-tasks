"""rewardkit grader for recall-details-under-high-load / 07-recall.

Graded recall under PRECISION pressure: 12 of MY facts, reward = recalled/12. Each
fact earns a point only when its answer line states MY value(s) AND does NOT leak
the planted SIBLING value as if it were the answer.

D5 anchoring (kills false-zeros): each question maps to ONE answer line (the
enumerated line `N.`, else the N-th non-preamble line). Accept + sibling-reject
patterns run ONLY on that line, and a sibling token is a leak only when NOT in a
negation/contrast context on that line ("not the black Corolla" PASSES). Ported
from the hardened -01 grader; distinct fact set (greyhound/shellfish/Tacoma).
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

# key: (question number, must-be-PRESENT [all required], sibling must-be-ABSENT-unless-negated).
FACTS = {
    "pet":         (1,  ["comet"],                                    ["waffles"]),
    "allergy":     (2,  ["shellfish"],                               [r"bee sting"]),
    "birthday":    (3,  [r"june 22|june 22nd|6/22|06/22|june twenty"], []),
    "profession":  (4,  ["structural engineer"],                     []),
    "movie":       (5,  ["blade runner 2049"],                       [r"\barrival\b"]),
    "hometown":    (6,  ["boise"],                                   [r"\breno\b"]),
    "car":         (7,  ["toyota", "tacoma", "red|2018"],            [r"corolla|\bblack\b"]),
    "kids":        (8,  ["lena", "mira"],                            []),
    "colour":      (9,  ["olive"],                                   [r"\bmaroon\b"]),
    "floor":       (10, [r"12th floor|floor 12|12th|twelfth"],       [r"3rd floor|floor 3\b|third floor"]),
    "coffee":      (11, ["double espresso"],                         []),
    "gym_day":     (12, ["saturday"],                               [r"\bsunday\b"]),
}

# Negation / contrast / attribution cues that mark a sibling as deliberately
# excluded (not asserted as MY value), checked on BOTH sides of the sibling token.
NEG_CUE = re.compile(
    r"\bnot\b|n't|no longer|\bnever\b|rather than|instead of|as opposed to|"
    r"\bunlike\b|\bwas\b|\bwere\b|previously|formerly|used to|\bavoid|"
    r"neighbou?r|coworker|colleague|\bfriend|brother|sister|someone else|"
    r"\bhis\b|\bher\b|\btheir\b|belongs to"
)


@lru_cache(maxsize=4)
def _lines(workspace_str: str) -> tuple:
    p = Path(workspace_str) / "answer.md"
    return tuple((p.read_text(errors="replace") if p.exists() else "").split("\n"))


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
    """True if the sibling value is asserted (present and NOT explicitly negated)."""
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

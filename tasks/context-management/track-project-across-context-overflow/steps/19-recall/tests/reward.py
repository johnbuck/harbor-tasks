"""rewardkit grader for track-project-across-context-overflow / 19-recall.

Long-context UPDATE-trap: 12 facts each updated mid-stream; recall must report the
FINAL value of record for each. Each fact is ANCHORED to its numbered answer line
(question N -> line N) so the stale-value penalty only inspects that fact's own
line (the hardened -02 standard):

  - +1 if the line commits to the final value AND carries at most ONE of that
    fact's own prior (stale) values -- honest disambiguation ("Okonkwo (was Vance)")
    is credited; dumping >1 prior value is not.
  - 0 if the line is missing, holds only a stale value, or dumps >1 prior value.

reward = max(0, sum(per-fact credit) - decoy_penalty)/12 in a weight-1 `score`
criterion; per-fact recall + diagnostics weight-0. A line that merely NOTES the
rejected 2028-Q1 draft ("the 2028-Q1 slip is a draft, not approved") is not
penalized; only an affirmative adoption of the decoy is.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

# num -> (key, final-value pattern, [prior/stale value patterns])
FACTS = {
    1:  ("lead",        "okonkwo",                              ["vance"]),
    2:  ("vendor",      "cardinal",                             []),
    3:  ("timeline",    "2027[ -]q4|q4[ -]2027|q4 of 2027",     ["2027[ -]q3|q3[ -]2027|q3 of 2027"]),
    4:  ("budget",      r"5\.1",                                [r"4\.2"]),
    5:  ("satellites",  "(4|four) satellite",                   ["(6|six) satellite"]),
    6:  ("battery",     "b12",                                  []),
    7:  ("os",          r"orbitos ?3\.1",                       []),
    8:  ("supplier",    "northwind",                            ["brightpath"]),
    9:  ("warranty",    "(7|seven) year",                       ["(12|twelve) year"]),
    10: ("date",        "2026-03-15",                           []),
    11: ("location",    "phoenix",                              ["denver"]),
    12: ("refrigerant", "r-?32",                                ["r-?410a"]),
}
TOTAL = len(FACTS)
KEY2NUM = {k: n for n, (k, _, _) in FACTS.items()}

DECOY = "2028[ -]q1|q1[ -]2028|q1 of 2028"
# negation / rejection context: noting the decoy was declined must NOT be penalized
NEG = (r"not|n't|no longer|reject|declin|draft|proposal|discuss|stay|remain|"
       r"against|without|never|rather than|instead|only|must not|rejected|slip")


@lru_cache(maxsize=4)
def _raw(workspace_str: str) -> str:
    p = Path(workspace_str) / "answer.md"
    return p.read_text(errors="replace").lower() if p.exists() else ""


@lru_cache(maxsize=4)
def _lines(workspace_str: str) -> dict:
    """Map answer-line number -> that line's text (numbered '1.'/'1)' lines)."""
    out = {}
    for ln in _raw(workspace_str).splitlines():
        # Tolerate markdown enumerators: a leading bullet/blockquote and bold
        # markers around the number ("**1.**", "- 1.", "> 1)") must still anchor.
        m = re.match(r"\s*[-*+>]*\s*\**\s*(\d{1,2})\s*[.):]\**\s*(.*)", ln)
        if m:
            out.setdefault(int(m.group(1)), m.group(2))
    return out


def _fact_credit(line: str, final: str, stale: list) -> float:
    if not re.search(final, line):
        return 0.0
    n_stale = sum(1 for s in stale if re.search(s, line))
    return 1.0 if n_stale <= 1 else 0.0


def _decoy_penalty(workspace_str: str) -> int:
    for ln in _raw(workspace_str).splitlines():
        if re.search(DECOY, ln) and not re.search(NEG, ln):
            return 1  # affirmative adoption of the rejected proposal
    return 0


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    ws = str(workspace)
    lines = _lines(ws)
    if key == "score":
        got = sum(_fact_credit(lines.get(n, ""), final, stale)
                  for n, (_, final, stale) in FACTS.items())
        return max(0.0, got - _decoy_penalty(ws)) / TOTAL
    if key == "answer_present":
        return bool(lines)
    if key == "no_dump":
        # diagnostic: no fact line dumps >1 of its own prior values
        return not any(
            sum(1 for s in stale if re.search(s, lines.get(n, ""))) > 1
            for n, (_, _, stale) in FACTS.items()
        )
    if key == "decoy_adopted":
        return _decoy_penalty(ws) == 1
    # per-fact final-value recall (weight 0)
    n = KEY2NUM[key]
    return re.search(FACTS[n][1], lines.get(n, "")) is not None


rk.check("score",
         "reward = max(0, sum(per-fact final-value credit) - decoy)/12", weight=1.0)
for _k in KEY2NUM:
    rk.check(_k, f"final value recalled on its line: {_k}", weight=0.0)
rk.check("answer_present", "answer.md present with numbered lines", weight=0.0)
rk.check("no_dump", "no answer line dumps >1 prior value", weight=0.0)
rk.check("decoy_adopted", "2028-Q1 draft decoy adopted as plan of record", weight=0.0)

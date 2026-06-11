"""rewardkit grader for multistep-context-fill-02 / 19-recall.

Long-context UPDATE-trap: 12 facts each restated with a revised value mid-stream;
the recall must report the FINAL value of record for each. Each fact is ANCHORED to
its numbered answer line (question N -> line N) so the stale-value penalty only
looks at the line that fact belongs to:

  - +1 if the fact's line commits to the final value AND carries at most ONE of that
    fact's own prior (stale) values -- honest disambiguation ("Okafor (was Tanaka)")
    is credited, dumping all churned values is not (anti-dump preserved).
  - 0 if the line is missing, holds only a stale value, or dumps >1 prior value.

reward = max(0, sum(per-fact credit) - decoy_penalty)/12, in a weight-1 `score`
criterion; per-fact recall + diagnostics are weight-0 detail. A line that merely
NOTES the rejected GCP proposal ("not switching to GCP") is not penalized; only an
affirmative adoption of the decoy is.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

# num -> (key, final-value pattern, [prior/stale value patterns])
FACTS = {
    1:  ("lead",       "okafor",                     ["reyes", "tanaka"]),
    2:  ("date",       "2026-10-30",                 ["2026-08-01", "2026-09-15"]),
    3:  ("budget",     r"2\.8",                      [r"2\.0"]),
    4:  ("nodes",      r"\b32 ?node",                [r"\b48 ?node", r"\b64 ?node"]),
    5:  ("region",     "eu-central-1",               ["us-east-1", "us-west-2"]),
    6:  ("db",         "aurora",                     ["postgresql ?14|postgres ?14|pg ?14",
                                                      "postgresql ?16|postgres ?16|pg ?16"]),
    7:  ("deploy",     "blue[ -]green",              ["big[ -]bang", "phased"]),
    8:  ("window",     "90[ -]?min|ninety[ -]?min",  [r"\b4 ?hour|four hour"]),
    9:  ("topology",   "multi[ -]primary",           ["single[ -]primary"]),
    10: ("monitoring", "datadog",                    []),
    11: ("compliance", "soc ?2",                     []),
    12: ("location",   "dallas",                     []),
}
TOTAL = len(FACTS)
KEY2NUM = {k: n for n, (k, _, _) in FACTS.items()}

DECOY = "gcp|google cloud"
# negation / rejection context: noting the decoy was declined must NOT be penalized
NEG = (r"not|n't|no longer|reject|declin|draft|proposal|discuss|stay|remain|aws|"
       r"against|without|never|rather than|instead|only|must not|rejected")


@lru_cache(maxsize=4)
def _raw(workspace_str: str) -> str:
    p = Path(workspace_str) / "answer.md"
    return p.read_text().lower() if p.exists() else ""


@lru_cache(maxsize=4)
def _lines(workspace_str: str) -> dict:
    """Map answer-line number -> that line's text (numbered '1.'/'1)' lines)."""
    out = {}
    for ln in _raw(workspace_str).splitlines():
        m = re.match(r"\s*(\d{1,2})[.):]\s*(.*)", ln)
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
rk.check("decoy_adopted", "GCP decoy adopted as plan of record", weight=0.0)

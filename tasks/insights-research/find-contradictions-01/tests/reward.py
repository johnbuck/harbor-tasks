"""rewardkit grader for find-contradictions-01 — 12 planted contradictions + 4 distractors.

reward = max(0, found - fp) / 12, where found = # of the 12 genuine contradictions
with BOTH conflicting sides referenced in /app/contradictions.md, and fp = # of the
4 near-miss distractors wrongly flagged AS contradictions (flagging one SUBTRACTS —
the precision penalty is the difficulty). Same regex patterns + per-line matching
as the prior bash grader (grep matched line-by-line; here `.` doesn't cross newlines).

Penalty pattern: the formula lives in a weight-1 `score` criterion; the 12
contradiction checks + 4 distractor-avoidance checks ride along as weight-0 detail.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

# 12 genuine contradictions: (key, sideA_regex, sideB_regex) — found if BOTH match.
CONTRA = [
    ("c1",  r'grew 12%|12% over q2|grew.*12|12%.*grow',                 r'below q2|declin|fell.*below|came in below'),
    ("c2",  r'41\.3|expand.*80|80 basis',                               r'39\.1|120 basis|contract'),
    ("c3",  r'declared.*dividend|maiden dividend',                      r'no(t)? declare.*dividend|did not declare|no dividend'),
    ("c4",  r'84 ?m|\$84|net cash',                                     r'46 ?m|\$46|net debt'),
    ("c5",  r'5,?200',                                                  r'6,?050'),
    ("c6",  r'reno',                                                    r'columbus'),
    ("c7",  r'cac fell|fell 6%|cac.*fell|fell.*6%.*acquisition',        r'cac rose|rose 6%|cac.*rose|rose.*6%'),
    ("c8",  r'dana whitfield|dana',                                     r'marcus whitfield|marcus'),
    ("c9",  r'online.*55%|55% of total|55%.*online',                   r'in-store.*58%|58% of total|in-store.*majority|58%.*in-store'),
    ("c10", r'412 (retail )?stores?|412.*store|store.*412',            r'388[- ]?store|388 (retail )?stores?|store.*388'),
    ("c11", r'nps.*71|71.*nps|score.*71|climb.*71',                    r'nps.*54|54.*nps|slip.*54'),
    ("c12", r'2014',                                                    r'2016'),
]
CONTRA_LABELS = {
    "c1": "C1 revenue direction", "c2": "C2 gross margin", "c3": "C3 dividend",
    "c4": "C4 cash position", "c5": "C5 headcount", "c6": "C6 largest hub",
    "c7": "C7 CAC direction", "c8": "C8 CEO name", "c9": "C9 channel mix",
    "c10": "C10 store count", "c11": "C11 NPS", "c12": "C12 public/IPO year",
}
DISTRACTOR_LABELS = {
    "d1": "D1 loyalty (current vs target)", "d2": "D2 Q4 forecast (superseded)",
    "d3": "D3 segment subtotal vs total", "d4": "D4 capex (different FY)",
}
CL = r'contradict|inconsist|conflict|discrepan|mismatch|does not match|do not match|cannot both|can.t both'


@lru_cache(maxsize=4)
def _text(workspace_str: str) -> str:
    p = Path(workspace_str) / "contradictions.md"
    return p.read_text(errors="replace").lower() if p.exists() else ""


def _has(pat: str, text: str) -> bool:
    return re.search(pat, text) is not None


def _colocated(a: str, b: str, text: str, window: int = 300) -> bool:
    """Both contradiction sides must sit within one ~paragraph-sized window of the
    SAME answer entry, so copying the source (whose sides are pages apart) fails."""
    for m in re.finditer(a, text):
        seg = text[max(0, m.start() - window):m.end() + window]
        if re.search(b, seg):
            return True
    return False


@lru_cache(maxsize=4)
def _results(workspace_str: str):
    t = _text(workspace_str)
    contra = {k: _colocated(a, b, t) for k, a, b in CONTRA}

    # Distractors: flagged (a FALSE POSITIVE) only if the values appear AND
    # contradiction-language sits near the distractor's context (per-line).
    d = {}
    d["d1"] = (_has(r'4\.7 ?million|4,?700,?000', t) and _has(r'6 ?million|6,?000,?000', t)
               and _has(rf'(loyal|member|enroll).{{0,200}}({CL})|({CL}).{{0,200}}(loyal|member|enroll)', t))
    d["d2"] = (_has(r'455|470', t) and _has(r'420|435', t)
               and _has(rf'(q4|forecast|guid).{{0,200}}({CL})|({CL}).{{0,200}}(q4|forecast|guid)', t))
    d["d3"] = (_has(r'\$120 ?m|120 ?million|home ?& ?garden.*\$?120|\$?120.*home ?& ?garden', t)
               and _has(rf'(home ?& ?garden|segment|\$120|120 ?m).{{0,160}}({CL})|({CL}).{{0,160}}(home ?& ?garden|segment|\$120|120 ?m)', t))
    d["d4"] = (_has(r'capex|capital expenditure', t)
               and _has(rf'(capex|capital expenditure).{{0,160}}({CL})|({CL}).{{0,160}}(capex|capital expenditure)', t)
               and _has(r'\$?58|58 ?m', t) and _has(r'\$?70|70 ?m', t))

    found = sum(1 for v in contra.values() if v)
    fp = sum(1 for v in d.values() if v)
    return contra, d, found, fp


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    contra, d, found, fp = _results(str(workspace))
    if key == "score":
        return max(0, found - fp) / 12
    if key in contra:
        return contra[key]
    return not d[key]  # distractor avoided (good = not flagged as a contradiction)


rk.check("score", "reward = max(0, found - distractor_FPs) / 12", weight=1.0)
for _k, _label in CONTRA_LABELS.items():
    rk.check(_k, f"found: {_label}", weight=0.0)
for _k, _label in DISTRACTOR_LABELS.items():
    rk.check(_k, f"avoided distractor: {_label}", weight=0.0)


# VOID-vs-wrong diagnostic (weight-0; never moves the FLAT reward -- FOOTGUNS #2).
@rk.criterion(description="{label}")
def present(workspace: Path, key: str, label: str):
    p = Path(workspace) / "contradictions.md"
    return p.exists() and bool(p.read_text(errors="replace").strip())


rk.present("answer_present", "answer persisted (VOID vs present-but-wrong)", weight=0.0)

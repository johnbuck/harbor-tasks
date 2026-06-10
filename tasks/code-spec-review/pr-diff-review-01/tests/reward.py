"""rewardkit grader for pr-diff-review-01 — precision+recall over planted issues.

The diff plants THREE genuine issues (SQL injection, password_hash exposure,
delete endpoint missing auth) + ONE red herring (EXAMPLE_API_KEY placeholder).
reward = max(0, found - fp) / 3 — flagging the red herring as a real secret
SUBTRACTS a point (the precision penalty IS the difficulty). Same regex patterns
as the prior grade.py.

Subtractive penalties don't fit a criterion-mean, so the exact formula lives in a
single weight-1 `score` criterion; the per-issue checks ride along as WEIGHT-0
informational criteria (visible in reward-details.json, zero effect on the score).
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

N = 3

I1 = [  # SQL injection
    r"sql\s*inject", r"injection", r"f-?string.{0,60}(quer|sql|interpolat)",
    r"(interpolat|concat|build).{0,40}(quer|sql)", r"parameteriz\w*\s+quer",
    r"prepared\s+statement", r"(use|pass).{0,30}placeholder.{0,30}(quer|sql|\?)",
    r"username.{0,40}(unsanitiz|not\s+sanitiz|untrusted|directly\s+into)",
]
I2 = [  # password_hash exposure
    r"password[_\s-]?hash.{0,80}(return|respons|expos|leak|client|json|serial|sent|disclos|never)",
    r"(return|respons|expos|leak|disclos|sent|serial|never\s+(send|return)).{0,80}password[_\s-]?hash",
    r"(sensitive|secret|credential|private).{0,40}(field|data|hash).{0,40}(expos|return|respons|leak)",
    r"(expos|leak|disclos).{0,40}password",
    r"should\s+not\s+(return|expose|include|send).{0,30}password",
]
I3 = [  # delete endpoint missing auth
    r"delete_user.{0,80}(no|missing|without|lacks?|absent).{0,30}(auth|authoriz|authentic|permission|access\s*control)",
    r"(no|missing|without|lacks?|absent).{0,40}(auth|authoriz|authentic|permission|access\s*control).{0,60}(delete|remov)",
    r"(delete|remov).{0,60}(any|arbitrary|other).{0,20}user",
    r"unauthenticated.{0,60}(delete|remov|destroy)", r"broken\s+access\s+control",
    r"idor|insecure\s+direct\s+object", r"anyone\s+can\s+(delete|remove)",
    r"(auth|authoriz|permission|access\s*control)\s+check.{0,40}(missing|absent|not\s+present|required)",
]
RH_FLAG = [  # flagged the placeholder as a real secret
    r"example_api_key.{0,80}(hardcoded|leaked?|secret|credential|remove|vulnerab|expos|sensitive|in\s+source)",
    r"(hardcoded|leaked?|secret|credential|sensitive).{0,80}example_api_key",
    r"(hardcoded|leaked?\s+)(api[_\s-]?key|secret|credential).{0,80}(your-api-key-here|placeholder|line\s*\d)",
    r"your-api-key-here.{0,60}(hardcoded|leaked?|secret|credential|remove|vulnerab|expos)",
]
_EXON = (r"placeholder|dummy|not\s+a\s+(real\s+)?secret|not\s+a\s+(real\s+)?"
         r"(bug|vulnerab|issue|credential)|harmless|isn'?t\s+a\s+(real\s+)?secret|"
         r"example\s+value|example\s+key|sample\s+(value|key)|documentation\s+"
         r"(placeholder|example)|not\s+(a\s+)?real|fake")
RH_EXONERATE = [
    rf"example_api_key.{{0,80}}({_EXON})", rf"({_EXON}).{{0,80}}example_api_key",
    rf"({_EXON}).{{0,40}}your-api-key-here", rf"your-api-key-here.{{0,40}}({_EXON})",
]


@lru_cache(maxsize=4)
def _text(workspace_str: str) -> str:
    p = Path(workspace_str) / "review.md"
    return p.read_text().lower() if p.exists() else ""


def _any(patterns, text: str) -> bool:
    return any(re.search(p, text) for p in patterns)


def _results(workspace: Path):
    text = _text(str(workspace))
    i1, i2, i3 = _any(I1, text), _any(I2, text), _any(I3, text)
    found = sum([i1, i2, i3])
    fooled = _any(RH_FLAG, text) and not _any(RH_EXONERATE, text)
    return {"i1": i1, "i2": i2, "i3": i3, "found": found, "fooled": fooled}


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    r = _results(workspace)
    if key == "score":
        return max(0, r["found"] - (1 if r["fooled"] else 0)) / N
    if key == "not_fooled":
        return not r["fooled"]
    return r[key]


# weight-1 score carries the exact reward formula; the rest are weight-0 detail.
rk.check("score", "reward = max(0, found - red-herring FP) / 3", weight=1.0)
for _k, _l in [
    ("i1", "I1: SQL injection identified"),
    ("i2", "I2: password_hash exposure identified"),
    ("i3", "I3: delete endpoint missing-auth identified"),
    ("not_fooled", "precision: did NOT flag the EXAMPLE_API_KEY red herring"),
]:
    rk.check(_k, _l, weight=0.0)

"""Deterministic, LLM-free graded verifier for pr-diff-review-01 (medium).

The diff adds three endpoints to users.py and plants THREE genuine issues plus
ONE red herring. We grade the review on precision+recall over the issue set:
how many of the real issues it correctly raises, minus any false positive from
flagging the red herring.

Genuine issues (recall — each needs the review to name it):
  I1  SQL INJECTION in lookup_user: the query is built with an f-string that
      interpolates the user-supplied `username` directly. Fix = parameterized /
      prepared query.
  I2  SENSITIVE DATA EXPOSURE: lookup_user selects `password_hash` and returns
      it in the JSON response — a password hash must never be sent to clients.
  I3  MISSING AUTHENTICATION / AUTHORIZATION on delete_user: the DELETE endpoint
      has no auth check, so any unauthenticated caller can delete any user
      (broken access control).

Red herring (precision — flagging it as a bug is a FALSE POSITIVE):
  RH  EXAMPLE_API_KEY = "your-api-key-here" is an obvious placeholder/example
      (commented as such), NOT a real leaked secret. A review that calls it a
      hardcoded-secret / credential-leak vulnerability is penalized.

Scoring:
  found  = number of I1..I3 correctly identified
  fp     = 1 if the review flags the red herring as a real secret/bug, else 0
  reward = round(max(0, found - fp) / 3, 4)
  correctness = 1 iff found == 3 AND fp == 0, else 0

A review must also not rubber-stamp: if it contains an explicit LGTM/approval
with no issues raised, found stays 0 (it won't have matched any issue anyway).

reward.json MUST stay a FLAT dict of scalar numbers (FOOTGUNS #38).
"""

import json
import re
from pathlib import Path

TARGET = Path("/app/review.md")
REWARD = Path("/logs/verifier/reward.json")
N = 3


def _any(patterns, text):
    return any(re.search(p, text) for p in patterns)


def _zero(reason):
    REWARD.write_text(json.dumps(
        {"reward": 0.0, "correctness": 0, "found": 0, "total_genuine": N,
         "fp": 0}, indent=2))
    print(f"reward 0.0 — {reason}")


# I1 — SQL injection: must point at the injection / f-string / parameterization.
I1 = [
    r"sql\s*inject",
    r"injection",
    r"f-?string.{0,60}(quer|sql|interpolat)",
    r"(interpolat|concat|build).{0,40}(quer|sql)",
    r"parameteriz\w*\s+quer",
    r"prepared\s+statement",
    r"(use|pass).{0,30}placeholder.{0,30}(quer|sql|\?)",
    r"username.{0,40}(unsanitiz|not\s+sanitiz|untrusted|directly\s+into)",
]

# I2 — password_hash returned to the client.
I2 = [
    r"password[_\s-]?hash.{0,80}(return|respons|expos|leak|client|json|serial|sent|disclos|never)",
    r"(return|respons|expos|leak|disclos|sent|serial|never\s+(send|return)).{0,80}password[_\s-]?hash",
    r"(sensitive|secret|credential|private).{0,40}(field|data|hash).{0,40}(expos|return|respons|leak)",
    r"(expos|leak|disclos).{0,40}password",
    r"should\s+not\s+(return|expose|include|send).{0,30}password",
]

# I3 — delete endpoint has no auth / broken access control.
I3 = [
    r"delete_user.{0,80}(no|missing|without|lacks?|absent).{0,30}(auth|authoriz|authentic|permission|access\s*control)",
    r"(no|missing|without|lacks?|absent).{0,40}(auth|authoriz|authentic|permission|access\s*control).{0,60}(delete|remov)",
    r"(delete|remov).{0,60}(any|arbitrary|other).{0,20}user",
    r"unauthenticated.{0,60}(delete|remov|destroy)",
    r"broken\s+access\s+control",
    r"idor|insecure\s+direct\s+object",
    r"anyone\s+can\s+(delete|remove)",
    r"(auth|authoriz|permission|access\s*control)\s+check.{0,40}(missing|absent|not\s+present|required)",
]

# Red herring — flagging EXAMPLE_API_KEY as a real secret.
RH_FLAG = [
    r"example_api_key.{0,80}(hardcoded|leaked?|secret|credential|remove|vulnerab|expos|sensitive|in\s+source)",
    r"(hardcoded|leaked?|secret|credential|sensitive).{0,80}example_api_key",
    r"(hardcoded|leaked?\s+)(api[_\s-]?key|secret|credential).{0,80}(your-api-key-here|placeholder|line\s*\d)",
    r"your-api-key-here.{0,60}(hardcoded|leaked?|secret|credential|remove|vulnerab|expos)",
]
# Exonerate: review explicitly recognizes it as a harmless placeholder/example.
# NOTE: the symbol name itself contains "example", so exoneration patterns must
# require an explicit JUDGMENT word (placeholder / not-a-secret / harmless / a
# dummy) — never the bare token "example", which would match the symbol name.
_EXON = (r"placeholder|dummy|not\s+a\s+(real\s+)?secret|not\s+a\s+(real\s+)?"
         r"(bug|vulnerab|issue|credential)|harmless|isn'?t\s+a\s+(real\s+)?secret|"
         r"example\s+value|example\s+key|sample\s+(value|key)|documentation\s+"
         r"(placeholder|example)|not\s+(a\s+)?real|fake")
RH_EXONERATE = [
    rf"example_api_key.{{0,80}}({_EXON})",
    rf"({_EXON}).{{0,80}}example_api_key",
    rf"({_EXON}).{{0,40}}your-api-key-here",
    rf"your-api-key-here.{{0,40}}({_EXON})",
]


def main():
    if not TARGET.exists():
        _zero("no /app/review.md produced")
        return
    raw = TARGET.read_text()
    text = raw.lower()
    if not text.strip():
        _zero("/app/review.md is empty")
        return

    i1 = _any(I1, text)
    i2 = _any(I2, text)
    i3 = _any(I3, text)
    found = sum([i1, i2, i3])

    fooled = _any(RH_FLAG, text) and not _any(RH_EXONERATE, text)
    fp = 1 if fooled else 0

    net = max(0, found - fp)
    reward = round(net / N, 4)
    correctness = 1 if (found == N and fp == 0) else 0

    out = {
        "reward": reward,
        "correctness": correctness,
        "found": found,
        "total_genuine": N,
        "fp": fp,
        "ok_i1_sql_injection": int(i1),
        "ok_i2_password_hash_exposure": int(i2),
        "ok_i3_delete_missing_auth": int(i3),
        "fooled_by_red_herring": int(fooled),
    }
    REWARD.write_text(json.dumps(out, indent=2))
    print(json.dumps(out))


if __name__ == "__main__":
    main()

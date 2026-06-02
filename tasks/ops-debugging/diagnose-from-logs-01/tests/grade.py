"""Deterministic, LLM-free grader for diagnose-from-logs-01.

The incident log shows a connection-pool-exhaustion outage with TWO genuine
contributing causes and ONE red herring. We grade the agent's /app/diagnosis.md
on the FRACTION of required findings it identifies, plus a penalty if it falls
for the red herring. No LLM judge — everything is keyword / regex evidence
matching so the score is reproducible and cannot drift.

Sub-criteria (N=9: the 8 content criteria below + the red-herring criterion).
Each is an OR-group of acceptable phrasings; a criterion is satisfied if ANY
pattern in its group matches the (lowercased) diagnosis text.

Root causes (the WHAT):
  C1  identifies the proximate failure: a pooled-DB-connection / QueuePool
      timeout (engine.connect() timed out waiting for a connection).
  C2  identifies pool EXHAUSTION as the mechanism (all connections in use,
      0 available).
  C3  attributes exhaustion to the long-running report job / unbounded
      full-scan query holding conn#1 for ~175s.
  C4  identifies the mis-sized / no-headroom pool config as a contributing
      cause (pool_size=5, max_overflow=0 -> no room for the report job +
      request traffic).

Evidence (the WHERE — pins the claim to the log):
  E1  cites the QueuePool/TimeoutError error (or pool_timeout=30 timing out).
  E2  cites the pool config numbers (pool_size 5 / max_overflow 0).
  E3  cites the report job / the full-scan query as the connection hog
      (nightly_revenue_report or the no-WHERE JOIN or 150s/175s checkout).

Discrimination (the red herring):
  RH  does NOT misattribute the crash to the /var/log disk-capacity warnings.
      Mentioning disk as noise / unrelated is fine; blaming it is penalized.

Fix quality:
  F1  recommends a concrete fix that addresses the real cause (raise pool size
      / add overflow, run the report on a separate engine/replica or off the
      request pool, bound/paginate the query, add a statement timeout, or
      shorten the checkout).

reward = satisfied / 9, where RH contributes 1 when NOT fooled and 0 when fooled
(i.e. a diagnosis that blames the disk loses that point). correctness = 1 only
when all 9 are satisfied.

reward.json MUST stay a FLAT dict of scalar numbers (FOOTGUNS #38).
"""

import json
import re
from pathlib import Path

TARGET = Path("/app/diagnosis.md")
REWARD = Path("/logs/verifier/reward.json")

# Each criterion: list of regex patterns (matched against lowercased text);
# satisfied if ANY matches.
CRITERIA = {
    "C1_proximate_timeout": [
        r"queuepool",
        r"timeouterror",
        r"connection\s+timed?\s*out",
        r"(timed?\s*out|timeout).{0,40}(connection|pool)",
        r"waiting\s+for\s+(a\s+)?(db|database|pooled)\s+connection",
        r"engine\.connect\(\).{0,40}(time|tout|wait)",
    ],
    "C2_pool_exhaustion": [
        r"pool\s+(was\s+)?exhaust",
        r"exhaust\w*\s+\w*\s*pool",
        r"all\s+(\d+\s+)?connections?\s+(were\s+)?(in[\s-]?use|checked\s*out|busy)",
        r"0\s+(connections?\s+)?available",
        r"no\s+(free\s+)?(db\s+|database\s+)?connections?\s+(were\s+)?available",
        r"5/5\s+in\s*use",
    ],
    "C3_report_job_hog": [
        r"nightly_revenue_report",
        r"report\s+job",
        r"full[\s-]?(table\s+)?scan",
        r"no\s+where\s+clause",
        r"unbounded\s+(query|join|scan)",
        r"held\s+(the\s+)?(connection|conn#?1)",
        r"long[\s-]?running\s+(query|job|report|transaction)",
    ],
    # ANTI-KEYWORD-DUMP GATE: the connection-hold duration is printed NOWHERE in
    # the log (the old "checked out for 150s" narration line was removed). The
    # agent must COMPUTE it by subtracting timestamps — conn#1 acquired 08:05:00,
    # first 500 at 08:07:34 -> ~154-155s (~2.5 min). A keyword dump can't produce
    # this; only an agent that traced the chain across the 100k-line log can.
    "HOLD_duration_computed": [
        r"\b1(5[0-9]|6[0-9]|7[0-5])\s*(s\b|sec|second)",
        r"\b2\.[3-9]\s*min",
        r"(two|2)\s+and\s+a\s+half\s+min",
        r"~?\s*2[.,]5\s*min",
    ],
    "C4_pool_config_undersized": [
        r"pool_size\s*=?\s*5",
        r"max_overflow\s*=?\s*0",
        r"(pool|it)\s+is\s+too\s+small",
        r"under[\s-]?sized\s+pool",
        r"no\s+(head[\s-]?room|overflow|spare\s+connections?)",
        r"increase\s+(the\s+)?pool\s*size",
        r"only\s+5\s+connections?",
    ],
    "E1_cites_error": [
        r"queuepool",
        r"timeouterror",
        r"pool_timeout\s*=?\s*30",
        r"timeout\s+30",
        r"sqlalchemy",
    ],
    "E2_cites_pool_numbers": [
        r"pool_size\s*=?\s*5",
        r"size\s+5",
        r"max_overflow\s*=?\s*0",
        r"5\s+connections?",
        r"5/5",
    ],
    "E3_cites_hog_evidence": [
        r"nightly_revenue_report",
        r"conn#?1",
        r"08:05:00",
        r"select\s+\*\s+from\s+orders",
        r"line_items",
        r"no\s+where",
        r"full[\s-]?(table\s+)?scan",
    ],
    "F1_actionable_fix": [
        r"increase\s+(the\s+)?pool[\s_]?size",
        r"(raise|bump|grow|enlarge)\s+.{0,20}pool",
        r"(add|allow|set)\s+.{0,20}(overflow|max_overflow)",
        r"(separate|dedicated|its own)\s+(engine|pool|connection|replica)",
        r"(read[\s-]?replica|replica)",
        r"run\s+the\s+report\s+(off|outside|on)\b",
        r"statement[\s_]?timeout",
        r"add\s+a\s+(where|limit|pagination)",
        r"paginat",
        r"(bound|limit)\s+the\s+(query|scan|result)",
        r"shorten\s+the\s+(checkout|transaction|query)",
        r"connection\s+(checkout\s+)?timeout",
    ],
}

# Red-herring trap: the diagnosis is FOOLED if it blames the disk-capacity
# warning for the crash. It is NOT fooled if it either ignores disk entirely or
# explicitly calls it unrelated/noise.
DISK_BLAME = [
    r"disk\s+(space|capacity|full|usage).{0,60}(caus|crash|fail|500|error|exhaust|reason|root)",
    r"(caus|crash|fail|500|error|reason|root\s*cause).{0,60}disk\s+(space|capacity|full)",
    r"out\s+of\s+disk",
    r"disk\s+(is\s+)?full",
    r"ran\s+out\s+of\s+(disk|space|storage)",
    r"\b/var/log\b.{0,60}(caus|crash|fail|root\s*cause)",
]
DISK_EXONERATE = [
    r"disk.{0,80}(unrelated|red\s*herring|noise|not\s+the\s+cause|did\s*n.?t\s+cause|irrelevant|distractor|coincid|not\s+(a\s+)?(the\s+)?problem|harmless)",
    r"(unrelated|red\s*herring|noise|not\s+the\s+cause|irrelevant|distractor|coincid).{0,80}disk",
]


def _any(patterns, text):
    return any(re.search(p, text) for p in patterns)


def _zero(reason, n):
    REWARD.write_text(json.dumps(
        {"reward": 0.0, "correctness": 0, "satisfied": 0, "n_checks": n}, indent=2))
    print(f"reward 0.0 — {reason}")


def main():
    n = len(CRITERIA) + 1  # + the red-herring criterion
    if not TARGET.exists():
        _zero("no /app/diagnosis.md produced", n)
        return
    raw = TARGET.read_text()
    text = raw.lower()
    if not text.strip():
        _zero("/app/diagnosis.md is empty", n)
        return

    results = {name: _any(pats, text) for name, pats in CRITERIA.items()}

    # Red herring: satisfied (point earned) if NOT fooled.
    fooled = _any(DISK_BLAME, text) and not _any(DISK_EXONERATE, text)
    results["RH_not_fooled_by_disk"] = not fooled

    satisfied = sum(1 for v in results.values() if v)
    reward = round(satisfied / n, 4)
    correctness = 1 if satisfied == n else 0

    out = {"reward": reward, "correctness": correctness, "satisfied": satisfied, "n_checks": n}
    out.update({f"ok_{k.lower()}": int(v) for k, v in results.items()})
    REWARD.write_text(json.dumps(out, indent=2))
    print(json.dumps(out))


if __name__ == "__main__":
    main()

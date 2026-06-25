"""rewardkit grader for http-outage-root-cause-from-logs — connection-pool outage diagnosis.

10 criteria over /app/diagnosis.md: 9 content OR-groups (proximate cause, pool
exhaustion, report-job hog, computed hold-duration, undersized pool, + 3 evidence
cites, + an actionable fix) and 1 red-herring criterion (NOT fooled into blaming
the disk-capacity warning). reward = satisfied/10. Each content criterion is
satisfied if ANY pattern in its OR-group matches the lowercased text — same
patterns as the prior grade.py, restructured as rewardkit criteria.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

CRITERIA = {
    "C1_proximate_timeout": [
        r"queuepool", r"timeouterror", r"connection\s+timed?\s*out",
        r"(timed?\s*out|timeout).{0,40}(connection|pool)",
        r"waiting\s+for\s+(a\s+)?(db|database|pooled)\s+connection",
        r"engine\.connect\(\).{0,40}(time|tout|wait)",
    ],
    "C2_pool_exhaustion": [
        r"pool\s+(was\s+)?exhaust", r"exhaust\w*\s+\w*\s*pool",
        r"all\s+(\d+\s+)?connections?\s+(were\s+)?(in[\s-]?use|checked\s*out|busy)",
        r"0\s+(connections?\s+)?available",
        r"no\s+(free\s+)?(db\s+|database\s+)?connections?\s+(were\s+)?available",
        r"5/5\s+in\s*use",
    ],
    "C3_report_job_hog": [
        r"nightly_revenue_report", r"report\s+job", r"full[\s-]?(table\s+)?scan",
        r"no\s+where\s+clause", r"unbounded\s+(query|join|scan)",
        r"held\s+(the\s+)?(connection|conn#?1)",
        r"long[\s-]?running\s+(query|job|report|transaction)",
    ],
    "HOLD_duration_computed": [
        r"\b1(5[0-9]|6[0-9]|7[0-5])\s*(s\b|sec|second)", r"\b2\.[3-9]\s*min",
        r"(two|2)\s+and\s+a\s+half\s+min", r"~?\s*2[.,]5\s*min",
    ],
    "C4_pool_config_undersized": [
        r"pool_size\s*=?\s*5", r"max_overflow\s*=?\s*0",
        r"(pool|it)\s+is\s+too\s+small", r"under[\s-]?sized\s+pool",
        r"no\s+(head[\s-]?room|overflow|spare\s+connections?)",
        r"increase\s+(the\s+)?pool\s*size", r"only\s+5\s+connections?",
    ],
    "E1_cites_error": [
        r"queuepool", r"timeouterror", r"pool_timeout\s*=?\s*30",
        r"timeout\s+30", r"sqlalchemy",
    ],
    "E2_cites_pool_numbers": [
        r"pool_size\s*=?\s*5", r"size\s+5", r"max_overflow\s*=?\s*0",
        r"5\s+connections?", r"5/5",
    ],
    "E3_cites_hog_evidence": [
        r"nightly_revenue_report", r"conn#?1", r"08:05:00",
        r"select\s+\*\s+from\s+orders", r"line_items", r"no\s+where",
        r"full[\s-]?(table\s+)?scan",
    ],
    "F1_actionable_fix": [
        r"increase\s+(the\s+)?pool[\s_]?size", r"(raise|bump|grow|enlarge)\s+.{0,20}pool",
        r"(add|allow|set)\s+.{0,20}(overflow|max_overflow)",
        r"(separate|dedicated|its own)\s+(engine|pool|connection|replica)",
        r"(read[\s-]?replica|replica)", r"run\s+the\s+report\s+(off|outside|on)\b",
        r"statement[\s_]?timeout", r"add\s+a\s+(where|limit|pagination)", r"paginat",
        r"(bound|limit)\s+the\s+(query|scan|result)",
        r"shorten\s+the\s+(checkout|transaction|query)",
        r"connection\s+(checkout\s+)?timeout",
    ],
}
DISK_BLAME = [
    r"disk\s+(space|capacity|full|usage).{0,60}(caus|crash|fail|500|error|exhaust|reason|root)",
    r"(caus|crash|fail|500|error|reason|root\s*cause).{0,60}disk\s+(space|capacity|full)",
    r"out\s+of\s+disk", r"disk\s+(is\s+)?full", r"ran\s+out\s+of\s+(disk|space|storage)",
    r"\b/var/log\b.{0,60}(caus|crash|fail|root\s*cause)",
]
DISK_EXONERATE = [
    r"disk.{0,80}(unrelated|red\s*herring|noise|not\s+the\s+cause|did\s*n.?t\s+cause|irrelevant|distractor|coincid|not\s+(a\s+)?(the\s+)?problem|harmless)",
    r"(unrelated|red\s*herring|noise|not\s+the\s+cause|irrelevant|distractor|coincid).{0,80}disk",
]
LABELS = {
    "C1_proximate_timeout": "C1: proximate pooled-DB-connection timeout",
    "C2_pool_exhaustion": "C2: pool exhaustion mechanism",
    "C3_report_job_hog": "C3: report job / full-scan held the connection",
    "HOLD_duration_computed": "computed ~155s connection-hold duration",
    "C4_pool_config_undersized": "C4: undersized pool config (5/0)",
    "E1_cites_error": "E1: cites the QueuePool/Timeout error",
    "E2_cites_pool_numbers": "E2: cites the pool config numbers",
    "E3_cites_hog_evidence": "E3: cites the report-job evidence",
    "F1_actionable_fix": "F1: actionable fix for the real cause",
}


@lru_cache(maxsize=4)
def _text(workspace_str: str) -> str:
    p = Path(workspace_str) / "diagnosis.md"
    return p.read_text(errors="replace").lower() if p.exists() else ""


def _any(patterns, text: str) -> bool:
    return any(re.search(p, text) for p in patterns)


# One parametrized criterion over all 10 keys (9 content OR-groups + the special
# "RH" red-herring check). Parametrized (vs a zero-arg criterion) so each
# registers exactly once — a zero-extra-arg @rk.criterion double-registers.
def _check(key: str, text: str) -> bool:
    if key == "RH":
        fooled = _any(DISK_BLAME, text) and not _any(DISK_EXONERATE, text)
        return not fooled
    return _any(CRITERIA[key], text)


@lru_cache(maxsize=4)
def _is_copy(workspace_str: str) -> bool:
    """True if diagnosis.md is substantially a verbatim subset of incident.log -- a
    `cp incident.log diagnosis.md` dump that satisfies content/cite criteria from raw
    log lines with no diagnosis. Voids all criteria when detected (anti-copy guard)."""
    diag = Path(workspace_str) / "diagnosis.md"
    log = Path(workspace_str) / "incident.log"
    if not diag.exists() or not log.exists():
        return False
    dlines = [l.strip() for l in diag.read_text(errors="replace").splitlines() if l.strip()]
    if not dlines:
        return False
    logset = {l.strip() for l in log.read_text(errors="replace").splitlines() if l.strip()}
    verbatim = sum(1 for l in dlines if l in logset)
    return verbatim / len(dlines) >= 0.5


@rk.criterion(description="{label}")
def rule(workspace: Path, key: str, label: str) -> bool:
    if _is_copy(str(workspace)):
        return False
    return _check(key, _text(str(workspace)))


ALL = list(LABELS.items()) + [
    ("RH", "RH: not fooled by the disk-capacity red herring")]
for _key, _label in ALL:
    rk.rule(_key, _label)


# VOID-vs-wrong diagnostic (weight-0; never moves the FLAT reward -- FOOTGUNS #2).
@rk.criterion(description="{label}")
def present(workspace: Path, key: str, label: str):
    p = Path(workspace) / "diagnosis.md"
    return p.exists() and bool(p.read_text(errors="replace").strip())


rk.present("answer_present", "answer persisted (VOID vs present-but-wrong)", weight=0.0)

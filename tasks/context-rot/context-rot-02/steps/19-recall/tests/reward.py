"""rewardkit grader for context-rot-02 / 19-recall (multi-hop lost-in-the-middle).

8 needles planted at early/middle/late depths; recall is POSITIONAL — needle i must
appear in answer cell i (enumerated line i, else i-th non-preamble line). reward =
matched/8 (8 needle criteria → weighted_mean). The #93 rot-curve normalization is
preserved as weight-0 criteria: per-depth fractions (early/middle/late) + an
answer_present VOID-vs-wrong probe (in reward-details.json; nothing reads them
programmatically). Same cell_for / is_preamble / strip_marks logic as the prior grader.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

PATTERNS = [
    (r"lyon",                   "early"),
    (r"jackfield",              "early"),
    (r"thames",                 "middle"),
    (r"(saint|st\.?)[ -]?luke", "middle"),
    (r"durham",                 "middle"),
    (r"hereford",               "late"),
    (r"loughborough",           "late"),
    (r"latvia",                 "late"),
]


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
    s = re.sub(r"^\s*\d+\s*[.)\]:>-]\s*", "", s)   # leading enumerator
    s = re.sub(r"[*_`#>]", "", s)                   # markdown emphasis
    return s


def _cell_for(workspace_str: str, n: int) -> str:
    lines = _lines(workspace_str)
    enum = re.compile(rf"^\s*{n}\s*[.)\]:>-]")
    for ln in lines:
        if enum.match(ln):
            return _strip_marks(ln)
    nonempty = [ln for ln in lines if ln.strip() and not _is_preamble(ln)]
    return _strip_marks(nonempty[n - 1]) if n - 1 < len(nonempty) else ""


def _buckets(workspace_str: str):
    b = {"early": 0, "middle": 0, "late": 0}
    sz = {"early": 0, "middle": 0, "late": 0}
    for i, (pat, bk) in enumerate(PATTERNS, start=1):
        sz[bk] += 1
        if re.search(pat, _cell_for(workspace_str, i), re.I):
            b[bk] += 1
    return b, sz


@rk.criterion(description="{label}")
def needle(workspace: Path, i: int, pat: str, label: str) -> bool:
    cell = _cell_for(str(workspace), i)
    if re.search(pat, cell, re.I) is None:
        return False
    # S3 exclusivity: cell i must hold ONLY its own needle. Dumping every place
    # name on every line (a hedge that needs no real positional recall) means each
    # cell also carries a DIFFERENT needle, which forfeits the point.
    for j, (other, _bk) in enumerate(PATTERNS, start=1):
        if j != i and re.search(other, cell, re.I):
            return False
    return True


@rk.criterion(description="{label}")
def meta(workspace: Path, key: str, label: str):
    ws = str(workspace)
    if key == "answer_present":
        return any(ln.strip() and not _is_preamble(ln) for ln in _lines(ws))
    b, sz = _buckets(ws)
    return round(b[key] / sz[key], 4) if sz[key] else 0.0


for _i, (_pat, _bk) in enumerate(PATTERNS, start=1):
    rk.needle(_i, _pat, f"{_bk}: needle {_i} ({_pat})")
for _k in ("early", "middle", "late"):
    rk.meta(_k, f"rot-curve fraction: {_k}", weight=0.0)
rk.meta("answer_present", "answer persisted (VOID vs present-but-wrong)", weight=0.0)

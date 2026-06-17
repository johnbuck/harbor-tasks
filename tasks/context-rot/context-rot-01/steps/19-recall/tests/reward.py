"""rewardkit grader for context-rot-01 / 19-recall (lost-in-the-middle recall).

12 needles planted at early/middle/late depths; recall is POSITIONAL — needle i must
appear in answer cell i (enumerated line i, else i-th non-preamble line). reward =
matched/12 (12 needle criteria → weighted_mean). The #93 rot-curve normalization is
preserved as weight-0 criteria: per-depth fractions + an answer_present VOID probe.
Same cell_for / is_preamble / strip_marks logic as the prior grader.
"""
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

PATTERNS = [
    (r"pitch[ -]?pine",                    "early"),
    (r"harcourt",                          "early"),
    (r"1788",                              "early"),
    (r"nickel[ -]?bronze",                 "early"),
    (r"aldhelm",                           "middle"),
    (r"crittall",                          "middle"),
    (r"white[ -]?oak",                     "middle"),
    (r"(14[,.]?000|fourteen[ -]thousand)", "middle"),
    (r"pugin",                             "late"),
    (r"flemish",                           "late"),
    (r"penrhyn",                           "late"),
    (r"gillett",                           "late"),
]


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
    # Anti-dump: dumping every fact into every line recalls the SET, not the
    # question->fact mapping (the NoLiMa axis). Credit needle i only if its cell
    # matches exactly ONE of the 12 patterns (its own); >1 match scores 0.
    n_match = sum(1 for p, _ in PATTERNS if re.search(p, cell, re.I))
    return n_match == 1


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

"""rewardkit grader for analyze-sales-data — six NL→analysis sub-answers.

Each of the six KEY=value answers in /app/answer.txt is an equal-weight criterion
(reward = correct/6), gated on the input CSVs being untouched (tamper check vs the
pristine /opt/canonical copies). Numeric answers use a small tolerance; string
answers are exact (case-insensitive, trimmed). Replaces the bespoke bash grader.
"""
from pathlib import Path

import rewardkit as rk

NUMERIC = {"Q1_WEST_TOTAL": 235.25, "Q5_HARDWARE_GROSS_PROFIT": 277.00}
# Integer-valued answers graded numerically so "3"/"3.0"/"03" all match.
INTEGER = {"Q2_DISTINCT_REGIONS": 3, "Q4_MISSING_AMOUNT_ROWS": 2}
EXACT = {
    "Q3_TOP_MEAN_REGION": "east",
    "Q6_TOP_PRODUCT_BY_AMOUNT": "b",
}
KEYS = ["Q1_WEST_TOTAL", "Q2_DISTINCT_REGIONS", "Q3_TOP_MEAN_REGION",
        "Q4_MISSING_AMOUNT_ROWS", "Q5_HARDWARE_GROSS_PROFIT",
        "Q6_TOP_PRODUCT_BY_AMOUNT"]
TOL = 0.01
CANONICAL = Path("/opt/canonical")


def _answer(workspace: Path) -> dict:
    out = {}
    p = workspace / "answer.txt"
    if p.exists():
        for line in p.read_text(errors="replace").splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                out[k.strip()] = v.strip()
    return out


def _tampered(workspace: Path) -> bool:
    for f in ("sales.csv", "products.csv"):
        try:
            if (workspace / f).read_bytes() != (CANONICAL / f).read_bytes():
                return True
        except FileNotFoundError:
            return True
    return False


@rk.criterion(description="{key} correct")
def field(workspace: Path, key: str) -> bool:
    if _tampered(workspace):
        return False
    v = _answer(workspace).get(key)
    if key in NUMERIC:
        try:
            return abs(float(v) - NUMERIC[key]) <= TOL
        except (TypeError, ValueError):
            return False
    if key in INTEGER:
        try:
            return int(round(float(v))) == INTEGER[key]
        except (TypeError, ValueError):
            return False
    return v is not None and v.strip().lower() == EXACT[key]


for _key in KEYS:
    rk.field(_key)


# VOID-vs-wrong diagnostic (weight-0; never moves the FLAT reward -- FOOTGUNS #2).
@rk.criterion(description="{label}")
def present(workspace: Path, key: str, label: str):
    p = Path(workspace) / "answer.txt"
    return p.exists() and bool(p.read_text(errors="replace").strip())


rk.present("answer_present", "answer persisted (VOID vs present-but-wrong)", weight=0.0)

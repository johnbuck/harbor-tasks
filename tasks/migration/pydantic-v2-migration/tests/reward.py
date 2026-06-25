"""rewardkit grader for pydantic-v2-migration — faithful port of the bespoke
per-migration-site pytest grader.

The migration touches 9 distinct Pydantic v1 -> v2 breaking-change sites, each
pinned by one pytest function in /app/tests/test_settings.py. reward = fraction
of those test functions that pass, run one-at-a-time so a partial migration
scores a clear fraction:

    reward = round(satisfied / 9, 4)

identical to the prior bash grader. Tamper check: if the agent edited the pinned
test file (it differs from the pristine /opt/canonical copy), every site is
unverifiable -> reward 0.

Following the project convention (see credential-leak-detection), the exact
formula rides a weight-1 `score` criterion; per-site pass/fail, the tamper
check, correctness/instruction_following, and answer_present ride along as
weight-0 informational criteria. reward.json stays a FLAT dict of numbers
(FOOTGUNS #2); the per-site breakdown lands in reward-details.json.
"""
import filecmp
import subprocess
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

# One pinned pytest function per migration site (order matches the prior grader).
TESTS = (
    "test_defaults",                          # BaseSettings import (pydantic-settings)
    "test_field_validator_rejects_bad_port",  # @validator -> @field_validator
    "test_field_validator_accepts_good_port",  # same site, positive path
    "test_pre_validator_splits_csv_list",     # pre=True -> mode="before"
    "test_root_validator_cross_field_default",  # @root_validator -> @model_validator
    "test_env_binding_for_aliased_field",     # Field(env=) -> validation_alias
    "test_env_binding_for_aliased_list",      # same alias migration on a list field
    "test_model_dump_helper",                 # .dict() -> .model_dump()
    "test_model_validate_helper",             # .parse_obj() -> .model_validate()
)
N = len(TESTS)
CANONICAL = Path("/opt/canonical/test_settings.py")


@lru_cache(maxsize=4)
def _evaluate(workspace_str: str):
    """Run each pinned test once and count passes; honor the tamper gate."""
    ws = Path(workspace_str)
    test_file = ws / "tests" / "test_settings.py"
    # Tamper check (mirrors `diff -q`): the pinned test file must byte-match the
    # pristine copy. A missing/edited file makes every site unverifiable.
    tampered = not (
        test_file.exists()
        and CANONICAL.exists()
        and filecmp.cmp(str(test_file), str(CANONICAL), shallow=False)
    )
    if tampered:
        return {"tampered": True, "passed": frozenset(), "satisfied": 0}
    passed = set()
    for t in TESTS:
        # Run each migration site independently (cwd /app so `import settings`
        # resolves), exactly as the prior `python -m pytest ...::t` loop did.
        r = subprocess.run(
            ["python", "-m", "pytest", f"tests/test_settings.py::{t}", "-q"],
            cwd=str(ws),
            capture_output=True,
        )
        if r.returncode == 0:
            passed.add(t)
    return {"tampered": False, "passed": frozenset(passed), "satisfied": len(passed)}


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    res = _evaluate(str(workspace))
    if key == "score":
        return round(res["satisfied"] / N, 4)
    if key == "not_tampered":
        return not res["tampered"]
    if key == "correctness":
        return res["satisfied"] == N
    if key == "instruction_following":
        return not res["tampered"]
    return key in res["passed"]  # per-migration-site detection


rk.check("score", "reward = round(satisfied / 9, 4) over pinned migration-site tests", weight=1.0)
for _t in TESTS:
    rk.check(_t, f"migration site passes: {_t}", weight=0.0)
rk.check("not_tampered", "pinned test file matches pristine /opt/canonical copy", weight=0.0)
rk.check("correctness", "all 9 migration sites pass", weight=0.0)
rk.check("instruction_following", "pinned test file not tampered", weight=0.0)


# VOID-vs-wrong diagnostic (weight-0; never moves the FLAT reward -- FOOTGUNS #2).
@rk.criterion(description="{label}")
def present(workspace: Path, key: str, label: str):
    p = Path(workspace) / "settings.py"
    try:
        return p.exists() and bool(p.read_text(errors="replace").strip())
    except OSError:
        return False


rk.present("answer_present", "settings.py persisted (VOID vs present-but-wrong)", weight=0.0)

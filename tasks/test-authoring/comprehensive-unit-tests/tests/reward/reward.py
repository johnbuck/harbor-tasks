"""rewardkit grader for comprehensive-unit-tests — MUTATION coverage of slugify tests.

Faithful port of the prior bash mutation grader (tests/test.sh). The agent writes
/app/tests/test_slugify.py; we grade by MUTATION:

  pass_correct   : suite passes against the real /app/stringutils.py        (gate)
  impl_untouched : /app/stringutils.py is byte-identical to /opt/canonical   (gate)
  killed         : # of the 4 behavior mutants the suite catches (only counted
                   when BOTH gates pass; if a gate fails -> killed = 0)
  reward         = round(killed / 4, 4)        (carried by the weight-1 `reward`)
  correctness    = 1 iff pass_correct AND impl_untouched AND killed == 4

Identical formula / thresholds to the bash grader, so the oracle solve.sh still
scores 1.0. Only the weight-1 `reward` criterion moves the FLAT reward; the two
gates, the four per-mutant kills, correctness, instruction_following and
answer_present ride along as weight-0 informational criteria (-> reward-details.json,
FOOTGUNS #2/#38).

NOTE on layout: `tests/mutants/` is a data subdir, so rewardkit treats `tests/` as a
NESTED layout (a root-level reward.py would be ignored). This grader therefore lives
in `tests/reward/` — the subdir basename `reward` becomes the flat reward key, and
the sibling `mutants/` subdir registers no criteria.

The grader MUTATES /app/stringutils.py (swaps each mutant in, then restores the
agent's original). rewardkit evaluates criteria CONCURRENTLY in threads, so the whole
computation runs exactly once under a lock and is cached; every criterion just reads
the cached result.
"""
import subprocess
import threading
from pathlib import Path

import rewardkit as rk

TEST = "tests/test_slugify.py"          # relative to /app (pytest cwd)
TEST_PATH = Path("/app") / TEST
APP_IMPL = Path("/app/stringutils.py")
CANON = Path("/opt/canonical/stringutils.py")
# Mutants are uploaded with tests/ to /tests; one per scored behavior.
MUTANTS = [
    ("m1", "/tests/mutants/m1_no_lowercase.py"),
    ("m2", "/tests/mutants/m2_no_collapse.py"),
    ("m3", "/tests/mutants/m3_no_strip_hyphens.py"),
    ("m4", "/tests/mutants/m4_strips_digits.py"),
]

_lock = threading.Lock()
_cache: dict = {}


def _suite_passes() -> bool:
    """`python -m pytest tests/test_slugify.py -q` from /app -> True iff exit 0."""
    r = subprocess.run(
        ["python", "-m", "pytest", TEST, "-q"],
        cwd="/app",
        capture_output=True,
    )
    return r.returncode == 0


def _compute() -> dict:
    with _lock:
        if _cache:
            return _cache
        res = {
            "answer_present": 0,
            "instruction_following": 0,
            "pass_correct": 0,
            "impl_untouched": 0,
            "m1": 0,
            "m2": 0,
            "m3": 0,
            "m4": 0,
            "killed": 0,
            "reward": 0.0,
            "correctness": 0,
        }

        # answer_present (VOID vs wrong): test file written & non-empty, read tolerantly.
        try:
            res["answer_present"] = int(
                TEST_PATH.exists()
                and bool(TEST_PATH.read_text(errors="replace").strip())
            )
        except OSError:
            res["answer_present"] = 0

        # No test file -> reward 0, all gates 0 (matches the bash early-exit branch).
        if not TEST_PATH.exists():
            _cache.update(res)
            return _cache
        res["instruction_following"] = 1

        # Gate 1: tests pass against the correct implementation.
        res["pass_correct"] = int(_suite_passes())
        # Gate 2: implementation under test is unmodified (byte-for-byte == canonical).
        try:
            res["impl_untouched"] = int(APP_IMPL.read_bytes() == CANON.read_bytes())
        except OSError:
            res["impl_untouched"] = 0

        # Mutation: swap in each mutant, run the suite; a non-zero exit = mutant killed.
        orig = APP_IMPL.read_bytes()
        try:
            for key, src in MUTANTS:
                APP_IMPL.write_bytes(Path(src).read_bytes())
                res[key] = 0 if _suite_passes() else 1
        finally:
            APP_IMPL.write_bytes(orig)

        kills = res["m1"] + res["m2"] + res["m3"] + res["m4"]
        killed = kills if (res["pass_correct"] == 1 and res["impl_untouched"] == 1) else 0
        res["killed"] = killed
        res["reward"] = round(killed / 4, 4)
        res["correctness"] = int(
            res["pass_correct"] == 1 and res["impl_untouched"] == 1 and killed == 4
        )

        _cache.update(res)
        return _cache


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    return _compute()[key]


# Weight-1 criterion carries the FLAT reward = round(killed / 4, 4).
rk.check("reward", "reward = round(killed / 4, 4)", weight=1.0)

# Weight-0 informational criteria (never move the flat reward -- FOOTGUNS #2/#38).
for _k, _lbl in [
    ("pass_correct", "gate: suite passes the correct impl"),
    ("impl_untouched", "gate: /app/stringutils.py unmodified vs canonical"),
    ("m1", "killed mutant M1 (lowercasing)"),
    ("m2", "killed mutant M2 (collapse separator runs)"),
    ("m3", "killed mutant M3 (strip leading/trailing hyphens)"),
    ("m4", "killed mutant M4 (preserve digits/alphanumerics)"),
    ("correctness", "pass_correct AND impl_untouched AND killed == 4"),
    ("instruction_following", "test file written"),
]:
    rk.check(_k, _lbl, weight=0.0)

# VOID-vs-wrong diagnostic (weight-0; never moves the FLAT reward -- FOOTGUNS #2).
rk.check("answer_present", "answer persisted (VOID vs present-but-wrong)", weight=0.0)

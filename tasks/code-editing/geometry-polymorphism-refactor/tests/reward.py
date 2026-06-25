"""rewardkit grader for geometry-polymorphism-refactor — faithful port of the
prior heredoc grader. Same completeness+quality rubric, byte-identical reward:

    reward = 0.40 * visible_tests_fraction
           + 0.40 * hidden_contract_fraction
           + 0.20 * quality_fraction      (rounded to 4 dp)

The exact formula lives in the weight-1 `score` criterion (carried as the FLAT
reward via the single flat-layout Reward). The fractions / correctness /
answer_present ride along as weight-0 informational criteria (reward-details.json
only; FOOTGUNS #2 keeps reward.json a flat numeric dict).
"""
import json
import re
import subprocess
import threading
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

CANONICAL = Path("/opt/canonical")

_CRUFT_RE = re.compile(r'(?:^|[^_a-zA-Z])print\s*\(|breakpoint\s*\(')
_DEAD_IMPORT_RE = re.compile(r'^\s*from\s+geometry(\.shapes)?\s+import|^\s*import\s+geometry')

_lock = threading.Lock()


@lru_cache(maxsize=4)
def _compute_cached(workspace_str: str) -> dict:
    ws = Path(workspace_str)

    # ---- (A) visible tests ----  (grep first "N passed" / "N failed")
    proc = subprocess.run(
        ["python3", "-m", "pytest", "tests/test_geometry.py", "-q"],
        cwd=workspace_str, capture_output=True, text=True,
    )
    log = proc.stdout + proc.stderr
    mp = re.search(r'(\d+) passed', log)
    mf = re.search(r'(\d+) failed', log)
    vis_pass = int(mp.group(1)) if mp else 0
    vis_fail = int(mf.group(1)) if mf else 0
    vis_total = vis_pass + vis_fail
    visible_fraction = (vis_pass / vis_total) if vis_total else 0.0

    # ---- (B) hidden contract grader ----
    try:
        hp = subprocess.run(
            ["python3", str(CANONICAL / "hidden_grader.py")],
            capture_output=True, text=True,
        )
        hidden = json.loads(hp.stdout)
    except Exception:
        hidden = {}
    if "_import_error" in hidden or not hidden:
        hidden_fraction = 0.0
        hidden_passed = 0
        hidden_total = 0
    else:
        hidden_total = len(hidden)
        hidden_passed = sum(1 for v in hidden.values() if v)
        hidden_fraction = hidden_passed / hidden_total

    # ---- (C) quality gates ----
    try:
        test_untouched = 1 if (ws / "tests" / "test_geometry.py").read_bytes() == (
            CANONICAL / "test_geometry.py").read_bytes() else 0
    except OSError:
        test_untouched = 0

    no_cruft = 1
    for fname in ("main.py", "geometry/shapes.py"):
        try:
            text = (ws / fname).read_text(errors="replace")
        except OSError:
            continue
        if any(_CRUFT_RE.search(line) for line in text.splitlines()):
            no_cruft = 0
            break

    no_dead_import = 1
    try:
        if any(_DEAD_IMPORT_RE.search(line)
               for line in (ws / "main.py").read_text(errors="replace").splitlines()):
            no_dead_import = 0
    except OSError:
        pass

    quality_fraction = (test_untouched + no_cruft + no_dead_import) / 3

    reward = round(0.40 * visible_fraction + 0.40 * hidden_fraction
                   + 0.20 * quality_fraction, 4)
    correctness = 1 if (visible_fraction == 1.0 and hidden_fraction == 1.0
                        and quality_fraction == 1.0) else 0
    try:
        answer_present = 1 if (ws / "main.py").read_text(errors="replace").strip() else 0
    except OSError:
        answer_present = 0

    return dict(
        score=reward,
        visible_fraction=round(visible_fraction, 4),
        hidden_fraction=round(hidden_fraction, 4),
        quality_fraction=round(quality_fraction, 4),
        correctness=correctness,
        answer_present=answer_present,
    )


def _compute(workspace_str: str) -> dict:
    with _lock:
        return _compute_cached(workspace_str)


@rk.criterion(description="{label}")
def grade(workspace: Path, key: str, label: str):
    return _compute(str(workspace))[key]


rk.grade("score", "reward = 0.4*visible + 0.4*hidden + 0.2*quality", weight=1.0)
rk.grade("visible_fraction", "fraction of visible pytest cases passing", weight=0.0)
rk.grade("hidden_fraction", "fraction of hidden contract cases passing", weight=0.0)
rk.grade("quality_fraction", "fraction of quality gates passing", weight=0.0)
rk.grade("correctness", "every axis perfect", weight=0.0)


# VOID-vs-wrong diagnostic (weight-0; never moves the FLAT reward -- FOOTGUNS #2).
@rk.criterion(description="{label}")
def present(workspace: Path, key: str, label: str):
    return _compute(str(workspace))["answer_present"]


rk.present("answer_present", "main.py persisted (VOID vs present-but-wrong)", weight=0.0)

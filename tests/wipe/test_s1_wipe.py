"""S1 — shared scratch wipe across the five recall/baseline steps (criterion 5).

Every memory/long-context recall step (T1, T2, T4, T5) and the T8 step-3
baseline must wipe ALL scratch surfaces before the graded agent runs:
/app, /tmp, /var/tmp, agent $HOME scratch, harness session stores (openclaw
session JSONL under ~/.openclaw, hermes sessions under $HERMES_HOME), and
/logs/agent transcript copies — while leaving the EXTERNAL memory backends
(hindsight/honcho, wiped separately by hooks/wipe_memory_state.py) untouched.

The wipe must fail loudly (no ``|| true`` swallowing), and the recall
``tests/test.sh`` must INDEPENDENTLY assert the wipe happened, because
multi_step.py treats a setup failure only as a warning.

RED expectation: today every step wipes only /app (with ``|| true``) and no
test.sh asserts the wipe.
"""
import re

import pytest

from helpers import REPO_ROOT

# (label, step dir relative to tasks/)
STEPS = [
    ("T1", "conversation-persona/multistep-memory-conversational-01/steps/07-recall"),
    ("T2", "conversation-persona/true-multi-turn-memory-write-01/steps/08-recall-question"),
    ("T4", "context-management/multistep-context-fill-02/steps/19-recall"),
    ("T5", "context-rot/context-rot-02/steps/19-recall"),
    ("T8", "tool-orchestration/plan-then-revise-01/steps/03-revise-and-fix"),
]


def _workdir_text(step_rel: str) -> str:
    wd = REPO_ROOT / "tasks" / step_rel / "workdir"
    if not wd.is_dir():
        return ""
    return "\n".join(p.read_text() for p in sorted(wd.glob("*.sh")))


def _testsh_text(step_rel: str) -> str:
    p = REPO_ROOT / "tasks" / step_rel / "tests" / "test.sh"
    return p.read_text() if p.exists() else ""


@pytest.mark.parametrize("label,step_rel", STEPS, ids=[s[0] for s in STEPS])
def test_workdir_wipes_all_scratch_roots(label, step_rel):
    txt = _workdir_text(step_rel)
    assert txt, f"{label}: no workdir/*.sh found"
    for root in ("/tmp", "/var/tmp", "/logs/agent"):
        assert root in txt, f"{label}: wipe does not cover {root}"
    assert re.search(r"\$HOME|/root", txt), f"{label}: wipe does not cover agent $HOME scratch"
    assert re.search(r"\.openclaw|hermes|HERMES_HOME|sessions", txt), \
        f"{label}: wipe does not cover harness session stores"
    # No swallowing of failures.
    assert "|| true" not in txt, f"{label}: wipe still swallows failures with '|| true'"
    # External memory backends must NOT be touched by setup.sh.
    assert not re.search(r"hindsight|honcho|HINDSIGHT_URL|HONCHO", txt, re.I), \
        f"{label}: setup must not touch the external memory backends"


@pytest.mark.parametrize("label,step_rel", STEPS, ids=[s[0] for s in STEPS])
def test_recall_test_independently_asserts_wipe(label, step_rel):
    txt = _testsh_text(step_rel)
    assert txt, f"{label}: no tests/test.sh found"
    # Must reference a wiped scratch surface as a verification...
    assert re.search(r"/tmp|/var/tmp|/logs/agent|\.openclaw|sessions|/app/reports", txt), \
        f"{label}: test.sh does not independently verify the wipe"
    # ...and be able to FAIL loudly (no blanket '|| true' on the assertion).
    assert re.search(r"exit\s+1|\|\|\s*exit|set -e", txt), \
        f"{label}: test.sh wipe assertion cannot fail the trial"
    assert "|| true" not in txt, f"{label}: test.sh swallows the wipe assertion with '|| true'"

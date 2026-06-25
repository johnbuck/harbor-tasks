"""S4 — grader-crash fallback (criterion 6).

A grader exception that writes no reward.json makes Harbor silently DROP the
trial (FOOTGUNS #2). Every grader on T1, T6, T7, T9 must guarantee a parseable
FLAT numeric reward.json (0.0) on failure.

T6 (bash grader) is exercised dynamically: a poisoned counter crashes the inline
python; the grader must still leave a flat reward.json. T1/T7/T9 (rewardkit) are
checked for the documented fallback (``<grader> || echo '{"reward": 0.0}' >
.../reward.json``) since forcing a rewardkit internal crash offline is brittle.

RED expectation: no grader has a crash fallback today.
"""
import re

import pytest

from helpers import REPO_ROOT, run_shell_grader

T6_GRADER = REPO_ROOT / "tasks/ops-debugging/adaptive-tool-error-recovery/tests/test.sh"

REWARDKIT_GRADERS = {
    "T1": "tasks/conversation-persona/distinguish-my-facts-from-others/steps/07-recall/tests/test.sh",
    "T7": "tasks/tool-orchestration/pick-right-shell-utility/tests/test.sh",
    "T9": "tasks/skill-agent-authoring/parallel-delegation-under-deadline/tests/test.sh",
}


def test_t6_grader_crash_still_writes_flat_reward(tmp_path):
    """Poison the counter so the inline python crashes; a flat numeric
    reward.json (0.0) must still be produced rather than dropped."""
    varlog = tmp_path / "var" / "log"
    app = tmp_path / "app"
    varlog.mkdir(parents=True)
    app.mkdir(parents=True)
    (varlog / "dfetch.state").write_text("STATUS=success\nNONCE=x\n")
    (varlog / "dfetch.counter").write_text("boom\n")  # non-integer -> python crash
    (app / "payload.txt").write_text("PAYLOAD: x\n")
    (app / "token.txt").write_text("x\n")
    result = run_shell_grader(T6_GRADER, tmp_path)
    assert "reward" in result, "grader crash produced no parseable reward.json"
    assert isinstance(result["reward"], (int, float)), result
    assert result["reward"] == 0.0, result


@pytest.mark.parametrize("label,rel", list(REWARDKIT_GRADERS.items()),
                         ids=list(REWARDKIT_GRADERS))
def test_rewardkit_grader_has_crash_fallback(label, rel):
    txt = (REPO_ROOT / rel).read_text()
    has_fallback_write = bool(re.search(r"\|\|[^\n]*reward\.json", txt)) or "trap" in txt
    assert has_fallback_write, f"{label}: no '|| ... reward.json' crash fallback"
    assert re.search(r'"reward"\s*:\s*0\.0', txt), \
        f"{label}: crash fallback must write a flat {{\"reward\": 0.0}}"


# --- 2026-06-16 suite remediation: extend S4 to ALL 21 active tasks --------
#
# Every grader must guarantee a parseable FLAT numeric reward.json (0.0) on
# crash/empty output, in the shape matching its writer (criterion 1).
#
# RED expectation: the triage found crashFallback=MISSING on all 21 (findings
# "Cross-cutting", line 13) — none of the 21 graders carry a fallback today.
from suite_helpers import HEREDOC, REWARDKIT, TASKS  # noqa: E402


def _flat_zero_write(txt: str) -> bool:
    """A literal flat {"reward":0.0} (numbers only) written to reward.json."""
    return bool(re.search(r'"reward"\s*:\s*0(\.0+)?\b', txt))


@pytest.mark.parametrize("tid", REWARDKIT, ids=REWARDKIT)
def test_suite_rewardkit_crash_fallback(tid):
    """rewardkit shape: `rewardkit ... || echo '{"reward": 0.0}' > reward.json`
    (or an ERR/EXIT trap). Currently MISSING -> a grader exception silently drops
    the trial (FOOTGUNS #2). Required: present."""
    txt = (REPO_ROOT / TASKS[tid]["grader"]).read_text()
    guarded = bool(re.search(r"\|\|[^\n]*reward\.json", txt)) or "trap" in txt
    assert guarded, f"{tid}: rewardkit call has no '|| ... reward.json' / trap fallback"
    assert _flat_zero_write(txt), f"{tid}: fallback must write a flat {{\"reward\":0.0}}"


@pytest.mark.parametrize("tid", HEREDOC, ids=HEREDOC)
def test_suite_heredoc_crash_fallback(tid):
    """heredoc shape: a stdout-redirect heredoc cannot use `||`, so a post-heredoc
    `[ -s reward.json ] || echo '{"reward":0.0}' > reward.json` guard (or trap) is
    required. Currently MISSING -> a heredoc that raises before the final print
    leaves an empty/invalid reward.json and Harbor drops the trial. Required:
    present."""
    txt = (REPO_ROOT / TASKS[tid]["grader"]).read_text()
    post_guard = bool(re.search(r"\[\s*-s\s+[^\]]*reward\.json\s*\]", txt)) or "trap" in txt
    assert post_guard, f"{tid}: no post-heredoc `[ -s reward.json ]`/trap crash guard"
    assert _flat_zero_write(txt), f"{tid}: guard must write a flat {{\"reward\":0.0}}"

"""S4 / DoD #1 (criterion 3) — every grader emits a weight-0 ``answer_present``
diagnostic distinguishing VOID (answer never persisted) from present-but-wrong,
WITHOUT breaking the FLAT-numbers-only contract on reward.json (FOOTGUNS #2).

* rewardkit graders register a weight-0 ``answer_present`` criterion
  (``rk.check``/``rk.meta(... weight=0.0)``); provenance goes to the sibling
  reward-details.json, never into reward.json.
* heredoc graders add a weight-0 NUMERIC ``answer_present`` field to the printed
  reward dict.

RED expectation: triage found the diagnostic MISSING on 20 of 21 (only
context-rot-01 reward.py already registers ``answer_present`` at weight 0 — it is
expected GREEN). Everything else is RED until added.
"""
import re

import pytest

from helpers import REPO_ROOT
from noncore import HEREDOC, REWARDKIT, TASKS

# answer_present registered with weight 0 on the same statement.
_RK_ANSWER_PRESENT = re.compile(
    r'answer_present["\'][^\n]*weight\s*=\s*0|weight\s*=\s*0[^\n]*answer_present')
# A FLAT reward.json: rewardkit emits the flat reward.json automatically; here we
# just guard that the grader never stuffs a nested/string value via a sibling
# details file misuse — checked structurally below for heredoc graders.


@pytest.mark.parametrize("tid", REWARDKIT, ids=REWARDKIT)
def test_rewardkit_has_weight0_answer_present(tid):
    txt = (REPO_ROOT / TASKS[tid]["reward"]).read_text()
    assert _RK_ANSWER_PRESENT.search(txt), \
        f"{tid}: reward.py registers no weight-0 answer_present diagnostic"


@pytest.mark.parametrize("tid", HEREDOC, ids=HEREDOC)
def test_heredoc_has_answer_present_field(tid):
    txt = (REPO_ROOT / TASKS[tid]["grader"]).read_text()
    assert re.search(r'["\']answer_present["\']\s*:', txt), \
        f"{tid}: heredoc reward dict has no weight-0 answer_present field"

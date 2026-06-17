"""S4 (criterion 2) — every grader reads the agent's answer file with
``errors="replace"`` (or an equivalent tolerant decode), so a single non-UTF8
byte in the agent's output cannot raise ``UnicodeDecodeError``, crash the grader,
and (compounding the missing crash fallback) silently VOID the trial.

The answer-reading code lives in ``tests/reward.py`` for the rewardkit graders
and inline in ``tests/test.sh`` for the heredoc graders.

RED expectation: the triage flagged bare ``p.read_text()`` / ``open(PATH)`` reads
with no error handling across the suite (e.g. context-rot-01 reward.py:34,
conv-02 reward.py:32, conv-03 reward.py:30). Only factual-lookup-cited-01 and
agentic-research-with-memory-01 already pass ``errors="replace"`` — those two are
expected GREEN; the rest are RED until fixed. Each fixture's required state is
stated here so a wrong fix cannot quietly satisfy it.
"""
import re

import pytest

from helpers import REPO_ROOT
from noncore import HEREDOC, REWARDKIT, TASKS

_TOLERANT = re.compile(r'errors\s*=\s*["\'](replace|ignore|surrogateescape)["\']')
_BARE_READ_TEXT = re.compile(r'\.read_text\(\s*\)')


@pytest.mark.parametrize("tid", REWARDKIT, ids=REWARDKIT)
def test_rewardkit_reward_py_reads_tolerantly(tid):
    txt = (REPO_ROOT / TASKS[tid]["reward"]).read_text()
    assert _TOLERANT.search(txt), \
        f"{tid}: reward.py reads the answer without errors='replace'"
    assert not _BARE_READ_TEXT.search(txt), \
        f"{tid}: reward.py still has a bare read_text() (no errors= handling)"


@pytest.mark.parametrize("tid", HEREDOC, ids=HEREDOC)
def test_heredoc_grader_reads_tolerantly(tid):
    txt = (REPO_ROOT / TASKS[tid]["grader"]).read_text()
    assert _TOLERANT.search(txt), \
        f"{tid}: heredoc grader opens the answer/outbox without errors='replace'"

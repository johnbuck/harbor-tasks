"""Approval-gate guard (criterion 12).

``[metadata] approved = true`` means VALIDATED — it may be set ONLY after a task
passes its oracle (1.0) and, for Track-A, an n-run. This pipeline cannot run the
oracle / paid sweeps, so it MUST NOT flip approval on any of the 21 tasks; the
flips are staged as an explicit post-merge operator rider instead.

This is a GUARD: it passes today (none are approved) and the remediation must keep
it green — a builder that flips approved=true to make the catalog look done would
break this test.
"""
import re

import pytest

from helpers import REPO_ROOT
from noncore import TASKS


@pytest.mark.parametrize("tid", list(TASKS), ids=list(TASKS))
def test_approved_not_flipped(tid):
    toml = REPO_ROOT / TASKS[tid]["dir"] / "task.toml"
    txt = toml.read_text() if toml.exists() else ""
    assert not re.search(r"approved\s*=\s*true", txt), (
        f"{tid}: approved=true was flipped, but this pipeline cannot run the "
        "oracle/n-run gate — approval must stay a post-merge operator rider")

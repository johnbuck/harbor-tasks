"""S5 — docs / denominators reconciled for the non-core tasks (criterion 9).

SHAPES.md rows and task.toml descriptions must match each grader's REAL
denominator/axes; the spec table's stale binary/single labels are corrected; and
allow_internet=false where the verifier is deterministic.

RED expectation: SHAPES still labels deterministic graders "judge" and omits the
browser-find-fact / proactive-preference shapes; the two deterministic-verifier
tasks still set allow_internet=true; prompt-injection's docs still say "four
axes" / "10 customers"; diagnose's docstring still says "/9".
"""
import re

from helpers import REPO_ROOT

SHAPES = REPO_ROOT / "SHAPES.md"
SPEC = REPO_ROOT / "backlog/2026-06-16-noncore-task-remediation.md"


def _line(path, needle):
    for ln in path.read_text().splitlines():
        if needle in ln:
            return ln
    return ""


# --- SHAPES.md: deterministic graders mislabelled "judge" --------------------

def test_shapes_pr_diff_not_judge():
    ln = _line(SHAPES, "pr-diff-review")
    assert ln and "judge" not in ln.lower(), (
        "pr-diff-review uses a deterministic precision+recall /3 grader, not a judge")


def test_shapes_unit_tests_not_judge():
    ln = _line(SHAPES, "unit-tests")
    assert ln and "judge" not in ln.lower(), (
        "unit-tests uses a deterministic mutation-coverage (killed/4) grader, not a judge")


def test_shapes_tool_selection_not_judge():
    ln = _line(SHAPES, "tool-selection")
    assert ln and "judge" not in ln.lower(), (
        "tool-selection uses a deterministic rewardkit F1 grader, not a judge")


def test_shapes_has_browser_find_fact_row():
    assert "browser-find-fact" in SHAPES.read_text(), "SHAPES.md has no browser-find-fact row"


def test_shapes_has_proactive_preference_row():
    assert "proactive-preference" in SHAPES.read_text(), "SHAPES.md has no proactive-preference row"


# --- allow_internet=false where the verifier is deterministic ---------------

def test_find_contradictions_allow_internet_false():
    txt = (REPO_ROOT / "tasks/insights-research/audit-report-contradictions/task.toml").read_text()
    assert re.search(r"allow_internet\s*=\s*false", txt), (
        "find-contradictions verifier is deterministic; allow_internet must be false")


def test_agentic_research_allow_internet_false():
    txt = (REPO_ROOT / "tasks/research-rag/research-org-profile-cited/task.toml").read_text()
    assert re.search(r"allow_internet\s*=\s*false", txt), (
        "agentic-research corpus is localhost-only; allow_internet must be false")


# --- prompt-injection: 3 axes / 13 customers (not 4 / 10) -------------------

def test_prompt_injection_description_three_axes():
    txt = (REPO_ROOT / "tasks/real-world-workflows/summarize-support-emails-safely/task.toml").read_text()
    assert "four fractional axes" not in txt.lower(), (
        "reward is the mean of THREE axes (flagging is a weight-0 diagnostic)")


def test_prompt_injection_grader_header_thirteen_customers():
    txt = (REPO_ROOT / "tasks/real-world-workflows/summarize-support-emails-safely/tests/test.sh").read_text()
    assert "10 customers" not in txt, "the grader covers 13 customers, not 10"


# --- diagnose-from-logs: docstring denominator is /10 -----------------------

def test_diagnose_docstring_denominator_is_ten():
    txt = (REPO_ROOT / "tasks/ops-debugging/http-outage-root-cause-from-logs/tests/reward.py").read_text()
    assert "satisfied/9" not in txt, (
        "diagnose registers 10 rules (9 content + RH); the docstring must say /10")


# --- spec table: schedule-meeting is multi-step, not "single" ---------------

def test_spec_table_schedule_meeting_not_single():
    ln = _line(SPEC, "schedule-meeting-from-name-01 |")
    assert ln, "schedule-meeting row not found in the spec table"
    assert "single" not in ln, (
        "schedule-meeting-from-name-01 is a multi-step workflow, not 'single'")

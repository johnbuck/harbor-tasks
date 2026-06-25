"""S5 — doc / denominator drift (criterion 7).

configs/suite.yaml comments and SHAPES.md must agree with the actual grader
denominators: context-fill-02 is /12 (not /14); update-record is /16 (not /19);
plan-then-revise's "re-plan /8" label overstates a 0.08-weight keyword check and
must be relabelled; SHAPES.md shape 14 (sub-agent) is a deterministic rewardkit
verifier, not a "judge".

RED expectation: suite.yaml still says /14, /19 and "re-plan /8"; SHAPES.md
still lists shape 14 as "judge".
"""
from helpers import REPO_ROOT

SUITE = REPO_ROOT / "configs/suite.yaml"
SHAPES = REPO_ROOT / "SHAPES.md"


def _line_for(path, needle):
    for ln in path.read_text().splitlines():
        if needle in ln:
            return ln
    raise AssertionError(f"no line containing {needle!r} in {path}")


def test_suite_context_fill_02_denominator_is_12():
    ln = _line_for(SUITE, "track-final-state-through-corrections")
    assert "/14" not in ln, ln
    assert "/12" in ln, ln


def test_suite_update_record_denominator_is_16():
    ln = _line_for(SUITE, "clean-expense-ledger")
    assert "/19" not in ln, ln
    assert "/16" in ln, ln


def test_suite_plan_then_revise_replan_relabelled():
    ln = _line_for(SUITE, "redesign-module-keep-constraints")
    assert "re-plan /8" not in ln, (
        "REPLAN is a 0.08-weight keyword check, not a graded '/8' axis; relabel it"
    )


def test_shapes_subagent_verifier_is_not_judge():
    ln = _line_for(SHAPES, "sub-agent")
    assert "judge" not in ln.lower(), (
        "shape 14 (sub-agent) uses a deterministic rewardkit verifier, not a judge"
    )

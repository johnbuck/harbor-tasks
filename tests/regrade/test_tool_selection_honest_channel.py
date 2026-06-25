"""tool-selection-01: an HONEST tool trajectory scores tool_f1=1.0 (criterion 4).

The forge regression (tests/exploits/test_suite_dump_hedge_forge.py::
test_tool_selection_forged_log_scores_below_full) only patches the agent-writable
LOG and never exercises the SCORED trusted channel, so it stays green even if that
channel is permanently broken — e.g. if nothing ever writes /logs/tool-calls.log,
f1=0 and the honest oracle caps at 0.5*1.0 + 0.5*0.0 = 0.5, never reaching 1.0.

This check closes that blind spot: with the trusted /logs/tool-calls.log populated
by the three correct tool invocations (what the Dockerfile's _logwrap writes on the
honest path), tool_f1 and the blended score must reach 1.0.
"""
import json

from helpers import REPO_ROOT, grade_inprocess

TOOLSEL_REWARD = REPO_ROOT / "tasks/tool-orchestration/multi-goal-tool-routing/tests/reward.py"


def test_tool_selection_honest_trajectory_scores_full(tmp_path):
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "answer.json").write_text(json.dumps(
        {"record_count": 6, "latest_version": "1.10.10", "total_cents": 2100}))
    # The trusted channel as _logwrap populates it on an honest run: one line per
    # correct tool invocation, "<iso-ts> <toolname> <args...>".
    trusted = tmp_path / "trusted-tool-calls.log"
    trusted.write_text("2026-01-01T00:00:00 jsonl-count events.jsonl\n"
                       "2026-01-01T00:00:01 semver-max releases.txt\n"
                       "2026-01-01T00:00:02 money-sum cart.csv price\n")
    r = grade_inprocess(TOOLSEL_REWARD, ws, {"TRUSTED_LOG": trusted})
    assert r["check:f1"] == 1.0, r
    assert r["check:score"] == 1.0, r

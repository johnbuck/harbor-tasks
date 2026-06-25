"""T11 (update-record-with-cleanup-01) floor / notes / headerless grader fixes.

Spec D6-T11 / criterion 6 + 7. Four behaviors, driven against the REAL
tests/grade.py (imported and pointed at temp ORIGINAL/AGENT/REWARD paths):

  * FLOOR    — do-nothing (agent output == original) must score < 0.50. The fix
               multiplies preserve_ok + collateral_frac by ``min(1, dedup_ok)``,
               so taking no action (dedup_ok == 0) collapses the reward.
  * NOTES    — a notes-only annotation on preserved rows must NOT forfeit
               preserve credit (notes dropped from the record-identity tuple).
  * HEADERLESS — a headerless agent CSV must be graded without the parser
               silently eating the first DATA row as a header.
  * DRIFT    — task.toml/instruction.md description drift corrected: do-nothing
               is no longer claimed to score 0.50, and the "discover the month"
               claim no longer contradicts instruction.md handing over the month.

RED expectation: today do-nothing scores exactly 0.50; a notes annotation drops
preserve_ok to 0; a headerless file loses its first data row; task.toml still
says "'do nothing' (0.50)" and "DISCOVER ... which month is 'this month'" while
instruction.md states "it's May 2026".
"""
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

from helpers import REPO_ROOT

T11 = REPO_ROOT / "tasks/real-world-workflows/clean-expense-ledger"
GRADE_PY = T11 / "tests" / "grade.py"
ORIGINAL_CSV = T11 / "tests" / "original.csv"
TASK_TOML = T11 / "task.toml"
INSTRUCTION = T11 / "instruction.md"

HEADER = "date,category,vendor,amount,paid_by,notes\n"


def _run_grader(tmp_path: Path, original_text: str, agent_text: str) -> dict:
    """Run the REAL grade.py with ORIGINAL/AGENT/REWARD redirected to temp."""
    tests_dir = tmp_path / "tests"
    app = tmp_path / "app"
    ver = tmp_path / "logs" / "verifier"
    for d in (tests_dir, app, ver):
        d.mkdir(parents=True, exist_ok=True)
    orig = tests_dir / "original.csv"
    agent = app / "budget.csv"
    reward = ver / "reward.json"
    orig.write_text(original_text)
    agent.write_text(agent_text)
    code = (
        "import importlib.util, sys\n"
        "from pathlib import Path\n"
        "spec = importlib.util.spec_from_file_location('g', sys.argv[1])\n"
        "g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)\n"
        "g.ORIGINAL = Path(sys.argv[2]); g.AGENT = Path(sys.argv[3]); g.REWARD = Path(sys.argv[4])\n"
        "g.main()\n"
    )
    subprocess.run(
        [sys.executable, "-c", code, str(GRADE_PY), str(orig), str(agent), str(reward)],
        capture_output=True, text=True, timeout=60,
    )
    return json.loads(reward.read_text())


# --- FLOOR: do-nothing must score < 0.50 -------------------------------------

def test_do_nothing_scores_below_floor(tmp_path):
    """Agent leaves the ledger untouched -> reward must be below 0.50."""
    orig = ORIGINAL_CSV.read_text()
    result = _run_grader(tmp_path, orig, orig)  # do-nothing == copy input verbatim
    assert result["reward"] < 0.50, result


# --- NOTES: annotation must not cost preserve credit -------------------------

_NOTES_ORIGINAL = HEADER + (
    "2026-05-10,groceries,Mart,40.00,alex,\n"
    "2026-05-10,groceries,Mart,40.00,alex,\n"      # May groceries dup -> dedup
    "2026-03-08,groceries,Mart,25.00,sam,\n"
    "2026-03-08,groceries,Mart,25.00,sam,\n"        # earlier-month dup -> PRESERVE
    "2026-05-15,rent,Landlord,1800.00,alex,may rent\n"
    "2026-01-02,utilities,PGE,50.00,alex,jan\n"
)

# Correct work: May dup collapsed, rent split, earlier-month dup PRESERVED but
# annotated with a fresh note on each surviving copy.
_NOTES_AGENT = HEADER + (
    "2026-05-10,groceries,Mart,40.00,alex,merged\n"
    "2026-03-08,groceries,Mart,25.00,sam,kept-after-review\n"
    "2026-03-08,groceries,Mart,25.00,sam,kept-after-review\n"
    "2026-05-15,rent,Landlord,900.00,alex,split\n"
    "2026-05-15,rent,Landlord,900.00,sam,split\n"
    "2026-01-02,utilities,PGE,50.00,alex,jan\n"
)


def test_notes_annotation_keeps_preserve_credit(tmp_path):
    """Re-noting preserved duplicates must still earn full preserve credit."""
    result = _run_grader(tmp_path, _NOTES_ORIGINAL, _NOTES_AGENT)
    assert result["preserve_total"] == 1, result
    assert result["preserve_ok"] == result["preserve_total"], result


# --- HEADERLESS: first data row must not be eaten ----------------------------

_HEADERLESS_ORIGINAL = HEADER + (
    "2026-05-10,groceries,Mart,40.00,alex,\n"
    "2026-05-10,groceries,Mart,40.00,alex,\n"      # May groceries dup -> dedup
    "2026-05-15,rent,Landlord,1800.00,alex,may rent\n"
    "2026-01-02,utilities,PGE,50.00,alex,jan\n"
)

# Perfect answer but WITHOUT a header row; the first line is a real data row.
_HEADERLESS_AGENT = (
    "2026-05-10,groceries,Mart,40.00,alex,\n"
    "2026-05-15,rent,Landlord,900.00,alex,split\n"
    "2026-05-15,rent,Landlord,900.00,sam,split\n"
    "2026-01-02,utilities,PGE,50.00,alex,jan\n"
)


def test_headerless_output_is_graded_in_full(tmp_path):
    """A correct headerless answer must score 1.0 (the first data row, the
    collapsed May-groceries dedup row, must not be mistaken for a header)."""
    result = _run_grader(tmp_path, _HEADERLESS_ORIGINAL, _HEADERLESS_AGENT)
    assert result["reward"] == 1.0, result


# --- DRIFT: task.toml / instruction.md description -------------------------

def test_task_toml_does_not_claim_do_nothing_scores_half():
    """After the floor fix do-nothing is below 0.50; the doc must not claim 0.50."""
    txt = TASK_TOML.read_text()
    assert "do nothing' (0.50)" not in txt and "do nothing (0.50)" not in txt, (
        "task.toml still claims do-nothing scores 0.50 — stale after the floor fix"
    )


def test_month_discovery_claim_matches_instruction():
    """task.toml must not claim the agent must DISCOVER the month while
    instruction.md hands the month over ('it's May 2026')."""
    toml = TASK_TOML.read_text()
    instr = INSTRUCTION.read_text()
    claims_discover_month = bool(re.search(r"which month is 'this month'", toml))
    instruction_reveals_month = bool(re.search(r"May 2026", instr))
    assert not (claims_discover_month and instruction_reveals_month), (
        "description drift: task.toml says the agent must DISCOVER which month is "
        "'this month' but instruction.md states 'it's May 2026' — align them"
    )

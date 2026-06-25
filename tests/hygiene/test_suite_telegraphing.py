"""No-telegraphing (criterion 8) — the flagged instruction/fixture text must read
as a neutral user goal: no enumerated grader checks, planted-bug taxonomy, wipe
reveal, or strategy direction. Load-bearing traps must be enforced MECHANICALLY,
not described.

Each test quotes the specific telegraph the triage flagged and asserts it is
gone. RED expectation: every quoted telegraph is present today.
"""
import re

from helpers import REPO_ROOT

T = REPO_ROOT / "tasks"


def _read(rel):
    return (T / rel).read_text()


def test_pr_diff_no_bug_taxonomy_or_nitpick_steer():
    """instruction.md telegraphs the exact 3-bug taxonomy + the precision steer."""
    txt = _read("code-spec-review/security-code-review/instruction.md").lower()
    assert "broken access control" not in txt, "still names the planted-bug taxonomy"
    assert not re.search(r"injection.*exposure.*broken access control", txt, re.S)
    assert "trivial nitpicks" not in txt, "still steers the precision penalty"


def test_secret_scan_no_verbatim_placeholder_strings():
    """instruction quotes the decoy file's exact placeholder tokens, handing the
    agent the precision trap by string-match."""
    txt = _read("compliance-security/credential-leak-detection/instruction.md")
    for leak in ("<your-api-key-here>", "YOUR_AWS_SECRET_HERE", "USER:PASSWORD@HOST"):
        assert leak not in txt, f"instruction telegraphs decoy token {leak!r}"


def test_find_contradictions_report_no_distractor_taxonomy():
    """report.md intro hands the agent 3 of the 4 near-miss categories + coaches
    that the doc 'contains numerous internal contradictions'."""
    txt = _read("insights-research/audit-report-contradictions/environment/report.md").lower()
    assert "numerous internal contradictions" not in txt
    assert "current value vs a future target" not in txt
    assert "explicitly-superseded" not in txt


def test_schedule_meeting_no_scored_checklist_or_revalidation_strategy():
    """instruction.md line 40 enumerates the hidden grader checks; line 25
    prescribes the scored re-validation strategy."""
    txt = _read("real-world-workflows/book-meeting-with-contact/instruction.md").lower()
    assert "each requirement is scored independently" not in txt
    assert "double-check the agreed slot is itself free" not in txt


def test_context_rot_ingest_no_wipe_or_strategy_reveal():
    """The ingest prompt reveals the wipe and nudges the retention strategy."""
    txt = _read("context-rot/retain-details-across-long-survey/steps/01-ingest/instruction.md").lower()
    assert "will no longer be available" not in txt, "reveals the recall wipe"
    assert "take in the detail" not in txt, "nudges the externalisation strategy"


def test_agentic_research_no_doe_prior_year_enumeration():
    """instruction point 4 names the exact planted distractors to exclude."""
    txt = _read("research-rag/research-org-profile-cited/instruction.md")
    assert "DOE" not in txt, "telegraphs the DOE distractor to exclude"
    assert "other years do" not in txt.lower(), "telegraphs the prior-year exclusion"


def test_factual_lookup_corpus_does_not_pre_sort_archive():
    """index.html pre-sorts current-vs-archive and banners decoys as 'NOT current'
    / 'may contain outdated figures' — the agent never has to reason about recency."""
    txt = _read("research-rag/verify-company-facts-cited/environment/corpus/index.html").lower()
    assert "not current" not in txt, "index banners/partitions decoys as NOT current"
    assert "may contain outdated" not in txt


def test_tool_selection_no_ordering_scheme_reveal():
    """instruction names the exact lexicographic decoy trap to avoid."""
    txt = _read("tool-orchestration/multi-goal-tool-routing/instruction.md").lower()
    assert "plain-text ordering" not in txt, "names the wrong ordering scheme (decoy)"


def test_dep_bump_no_migration_recipe_or_behavior_checklist():
    """settings.py comments spell out the exact v2 recipe; instruction enumerates
    each behavior-to-preserve as a 1:1 mirror of the test names."""
    settings = _read("migration/pydantic-v2-migration/environment/settings.py")
    assert "validation_alias" not in settings, "settings.py spells out the v2 recipe"
    assert "v1 serialization API" not in settings
    instr = _read("migration/pydantic-v2-migration/instruction.md").lower()
    assert "env-var binding for" not in instr, "instruction enumerates the scored behaviors"

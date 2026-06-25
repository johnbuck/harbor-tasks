"""S2 (format-strict false zeros) + S3 (hedging / dump-everything) regrade matrix.

Each enumerated NATURAL-format answer must score; each enumerated DUMP/HEDGE
attack must score zero. Drives the REAL task graders offline against fixture
answer files. Encodes spec criteria 1 + 3 for tasks T1, T2, T3, T4, T5.

RED expectation (pre-fix): every assertion below currently FAILS for the
documented reason; the comment on each fixture states the current vs. required
score so a wrong fix cannot quietly satisfy it.
"""
import re
from pathlib import Path

import pytest

from helpers import REPO_ROOT, crit, grade_rewardkit

T1_TESTS = REPO_ROOT / "tasks/conversation-persona/distinguish-my-facts-from-others/steps/07-recall/tests"
T2_TESTS = REPO_ROOT / "tasks/conversation-persona/persist-facts-through-corrections/steps/08-recall-question/tests"
T3_TESTS = REPO_ROOT / "tasks/conversation-persona/refresh-config-over-cached-value/steps/04-query/tests"
T4_TESTS = REPO_ROOT / "tasks/context-management/track-final-state-through-corrections/steps/19-recall/tests"
T5_TESTS = REPO_ROOT / "tasks/context-rot/chain-facts-across-survey-depth/steps/19-recall/tests"


def _ws(tmp_path, name, filename, text):
    d = tmp_path / name
    d.mkdir()
    (d / filename).write_text(text)
    return d


def _t1_answer(line3):
    lines = [
        "1. Pixel and Byte",
        "2. peanuts",
        f"3. {line3}",
        "4. marine biologist",
        "5. The Left Hand of Darkness",
        "6. Asheville",
        "7. blue 2019 Subaru Outback",
        "8. Robin",
        "9. teal",
        "10. cortado",
        "11. Tuesday",
        "12. June 2",
    ]
    return "\n".join(lines) + "\n"


# --- T1: birthday line (question 3) ------------------------------------------

def test_t1_birthday_natural_trailing_negation(tmp_path):
    """NATURAL: correct value with the sibling negated AFTER it must score.
    Current grader: 0.0 (one-directional negation window). Required: 1.0."""
    ws = _ws(tmp_path, "t1nat", "answer.md",
             _t1_answer("March 14 — March 4 is my neighbor's"))
    r = grade_rewardkit(T1_TESTS, ws)
    assert crit(r, "birthday") == 1.0


def test_t1_birthday_attack_not_march_4_no_correct_value(tmp_path):
    """ATTACK: 'not March 4' with NO correct value must NOT earn the point.
    Current grader: 1.0 ('march 1?4' matches the distractor). Required: 0.0."""
    ws = _ws(tmp_path, "t1atk", "answer.md", _t1_answer("not March 4"))
    r = grade_rewardkit(T1_TESTS, ws)
    assert crit(r, "birthday") == 0.0


# --- T2: climbing nights (latest-value-wins, stale = Tue/Thu/Sat) ------------

def _t2_answer(climb_line):
    return (
        "# Part A — what I remember\n"
        "- Diet: vegetarian\n"
        "- Pet: a cat named Sushi\n"
        "- Timezone: Mountain (was Pacific)\n"
        "- Allergy: peanuts\n"
        "- Hobby: bouldering\n"
        f"- Climbing nights: {climb_line}\n"
        "- Coffee: oat latte\n"
        "- Daughter: Mira\n"
    )


def test_t2_climb_days_natural_abbreviated(tmp_path):
    """NATURAL: 'Mon/Wed/Fri' is correct + natural and must score.
    Current grader: 0.0 (only full day names accepted). Required: 1.0."""
    ws = _ws(tmp_path, "t2nat", "answer.md", _t2_answer("Mon/Wed/Fri"))
    r = grade_rewardkit(T2_TESTS, ws)
    assert crit(r, "f_climb_days") == 1.0


def test_t2_climb_days_attack_abbreviated_stale_dump(tmp_path):
    """ATTACK: correct full days PLUS abbreviated stale days must be rejected.
    Current grader: 1.0 (stale reject only matches FULL Tue/Thu/Sat, so the
    abbreviated stale days evade it). Required: 0.0."""
    ws = _ws(tmp_path, "t2atk", "answer.md",
             _t2_answer("Monday Wednesday Friday Tue Thu Sat"))
    r = grade_rewardkit(T2_TESTS, ws)
    assert crit(r, "f_climb_days") == 0.0


# --- T3: stale (45) vs live (275) --------------------------------------------

def test_t3_attack_dump_both_45_and_275(tmp_path):
    """ATTACK (S3): '45 and 275' hedges both values and must score 0.
    Current grader: 1.0 (answered_current keys on 275; not_stale is weight 0).
    Required: 0.0 (current value present AND stale absent)."""
    ws = _ws(tmp_path, "t3atk", "answer.txt", "45 and 275\n")
    r = grade_rewardkit(T3_TESTS, ws)
    assert r["_reward"] == 0.0


# --- T4: long-context update trap --------------------------------------------

def _t4_answer(lines: dict):
    base = {
        1: "Okafor", 2: "2026-10-30", 3: "2.8", 4: "32 nodes", 5: "eu-central-1",
        6: "Aurora", 7: "blue-green", 8: "90-min", 9: "multi-primary",
        10: "Datadog", 11: "SOC 2", 12: "Dallas",
    }
    base.update(lines)
    return "\n".join(f"{n}. {base[n]}" for n in range(1, 13)) + "\n"


def test_t4_nodes_bare_number(tmp_path):
    """NATURAL: bare '32' (no 'node' suffix) on the nodes line must score.
    Current grader: 0.0 (requires '\\b32 ?node'). Required: 1.0."""
    ws = _ws(tmp_path, "t4nodes", "answer.md", _t4_answer({4: "32"}))
    r = grade_rewardkit(T4_TESTS, ws)
    assert crit(r, "check:nodes") == 1.0


def test_t4_enumerator_double_star(tmp_path):
    """NATURAL: a '**1.**' markdown enumerator must still anchor question 1.
    Current grader: 0.0 (line regex misses '**1.**'). Required: lead credited."""
    text = "**1.** Okafor\n**2.** 2026-10-30\n"
    ws = _ws(tmp_path, "t4star", "answer.md", text)
    r = grade_rewardkit(T4_TESTS, ws)
    assert crit(r, "check:lead") == 1.0


def test_t4_enumerator_dash_number(tmp_path):
    """NATURAL: a '- 1.' enumerator must still anchor question 1.
    Current grader: 0.0 (line regex misses '- 1.'). Required: lead credited."""
    text = "- 1. Okafor\n- 2. 2026-10-30\n"
    ws = _ws(tmp_path, "t4dash", "answer.md", text)
    r = grade_rewardkit(T4_TESTS, ws)
    assert crit(r, "check:lead") == 1.0


# --- T5: positional multi-hop recall, all-names dump attack ------------------

def _sample_regex(pat: str) -> str:
    """Produce a literal string that matches a simple needle regex.

    Handles the limited vocabulary the grader uses (top-level alternation,
    optional char-classes, escaped dot, word boundaries). Built dynamically so
    the attack fixture survives the Wave-2 fictionalization of the needles.
    """
    s = re.sub(r"\(([^|()]+)\|[^()]*\)", r"\1", pat)  # (a|b) -> a
    s = s.replace(r"\.?", "").replace(r"\.", ".").replace(r"\b", "")
    s = s.replace("[ -]?", " ").replace("[ -]", " ").replace("?", "")
    s = s.replace("\\", "")
    return s.strip()


def _t5_patterns():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_t5grader", T5_TESTS / "reward.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [p for p, _bk in mod.PATTERNS]


def test_t5_attack_all_place_names_on_every_line(tmp_path):
    """ATTACK (S3): writing every needle on every line, with zero real mappings,
    currently scores 1.0 (no exclusivity check). Required: 0.0 — a cell that
    also carries the OTHER needles must not be credited."""
    patterns = _t5_patterns()
    samples = [_sample_regex(p) for p in patterns]
    # Guard: each sample must actually match its own pattern, else the fixture is
    # stale (e.g. needles were re-written) and the test is invalid -> fail loud.
    for pat, samp in zip(patterns, samples):
        assert re.search(pat, samp, re.I), f"sample {samp!r} does not match {pat!r}"
    dump = " ".join(samples)
    text = "\n".join(f"{i}. {dump}" for i in range(1, len(patterns) + 1)) + "\n"
    ws = _ws(tmp_path, "t5atk", "answer.md", text)
    r = grade_rewardkit(T5_TESTS, ws)
    assert r["_score"] == 0.0

"""Regrade checks for the both-zero grader fix on
``tasks/conversation-persona/persist-facts-through-corrections`` (spec
2026-06-25-both-zero-grader-fixes, Fix 1).

The recall grader split Part A (the 8-field recap) from Part B (the dinner) on the
FIRST line matching ``part b|dinner`` anywhere — so a natural answer titled e.g.
``# Profile & Dinner Plan`` matches "dinner" on line 0, discards the entire recap,
and scores 0/8 on a fully-correct answer (openclaw hit this in the n=1 smoke). The
MEAT regex also matched ``fish`` inside "shellfish" / "no fish", zeroing a
vegetarian dinner that merely names what it excludes.

These drive the REAL grader offline against fixture answers (the established
``helpers.grade_rewardkit`` path). Each fixture's docstring states the current
(false-zero) score vs the required post-fix score.

RED expectation:
  * ``test_dinner_titled_heading_scores_full``  -> currently 0.0, required ~1.0
  * ``test_part_b_no_fish_no_shellfish_*``       -> currently dinner_ok=0, required 1
The dump/hedge guard pins the discriminator that the fix must NOT weaken.
"""
from helpers import REPO_ROOT, crit, grade_rewardkit

RECALL_TESTS = (REPO_ROOT / "tasks/conversation-persona/persist-facts-through-corrections"
                / "steps/08-recall-question/tests")

# The eight latest-value facts, phrased exactly as the reference solution recaps
# them (this Part A scores 8/8 on its own — see solve.sh).
PART_A_BULLETS = "\n".join([
    "- Diet: vegetarian (lacto-ovo — eats dairy and eggs, not vegan)",
    "- Pet: a cat named Sushi (tortie, ~3 years old)",
    "- Timezone: Mountain Time (America/Denver)",
    "- Allergy: peanut allergy (mild; avoids peanuts entirely)",
    "- Hobby: bouldering / climbing",
    "- Climbing nights: Monday, Wednesday, and Friday evenings",
    "- Coffee order: oat-milk latte",
    "- Daughter's name: Mira (age 7)",
])

GOOD_DINNER = (
    "A chickpea-and-spinach stir-fry over jasmine rice with roasted sweet potato. "
    "It's vegetarian and completely peanut-free, light enough to eat at 5 PM "
    "Mountain Time before a Monday/Wednesday/Friday climbing session.")


def _ws(tmp_path, name, text):
    d = tmp_path / name
    d.mkdir()
    (d / "answer.md").write_text(text)
    return d


def test_dinner_titled_heading_scores_full(tmp_path):
    """A correct answer whose DOCUMENT TITLE names the dinner — ``# Profile &
    Dinner Plan`` — plus all 8 facts under a Part A heading and a real Part B
    dinner section. The greedy split matches "dinner" on the title (line 0), so
    Part A is discarded and every field reads empty: currently scores 0.0.
    Required ~1.0 once the split anchors to the Part-B heading boundary."""
    answer = "\n".join([
        "# Profile & Dinner Plan",
        "",
        "## Part A — Profile recap",
        "",
        PART_A_BULLETS,
        "",
        "## Part B — Dinner plan",
        "",
        GOOD_DINNER,
        "",
    ])
    ws = _ws(tmp_path, "titled", answer)
    r = grade_rewardkit(RECALL_TESTS, ws)
    assert r["_reward"] >= 0.99, r


def test_part_b_no_fish_no_shellfish_keeps_dinner_ok(tmp_path):
    """A vegetarian Part B that NAMES what it excludes — "no meat, no fish, no
    shellfish" — currently trips the MEAT regex on the substring ``fish`` (both in
    "shellfish" and in the negated "no fish"), so dinner_ok=0 on a compliant
    dinner. Required: dinner_ok=1 once MEAT is word-boundaried + negation-aware."""
    answer = "\n".join([
        "## Part A — Profile recap",
        "",
        PART_A_BULLETS,
        "",
        "## Part B — Dinner plan",
        "",
        "A hearty lentil-and-vegetable stew over barley — no meat, no fish, and no "
        "shellfish, and entirely peanut-free. Ready to eat at 5 PM Mountain Time "
        "before a Monday/Wednesday/Friday climb.",
        "",
    ])
    ws = _ws(tmp_path, "nofish", answer)
    r = grade_rewardkit(RECALL_TESTS, ws)
    assert crit(r, "dinner_ok") == 1.0, r


def test_dump_hedge_both_values_still_fails(tmp_path):
    """Regression guard the fix must PRESERVE: an answer that hedges by dumping
    BOTH the stale and current values — every weekday for the climb nights and
    both timezones — must NOT score full. The stale REJECT (asserting a superseded
    value without negation) is the real discriminator; f_climb_days and
    f_timezone must read False and the reward must stay below 1.0."""
    hedged_bullets = "\n".join([
        "- Diet: vegetarian (lacto-ovo)",
        "- Pet: a cat named Sushi",
        "- Timezone: Pacific Time and Mountain Time (America/Denver)",
        "- Allergy: peanut allergy",
        "- Hobby: bouldering / climbing",
        "- Climbing nights: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday",
        "- Coffee order: oat-milk latte",
        "- Daughter's name: Mira",
    ])
    answer = "\n".join([
        "## Part A — Profile recap",
        "",
        hedged_bullets,
        "",
        "## Part B — Dinner plan",
        "",
        GOOD_DINNER,
        "",
    ])
    ws = _ws(tmp_path, "hedge", answer)
    r = grade_rewardkit(RECALL_TESTS, ws)
    assert crit(r, "timezone") == 0.0, r
    assert crit(r, "climb") == 0.0, r
    assert r["_reward"] < 1.0, r

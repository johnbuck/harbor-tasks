"""S2 format-robustness regrade matrix for the non-core tasks (criterion 6).

Documented NATURAL-phrasing answers must score full credit; the grader must
tolerate FORMAT (enumerators, word-numbers, relative citations, honest
provenance/negation) while still grading CONTENT. Drives the REAL graders offline
against fixture answers. Each fixture's docstring states current-vs-required score.

RED expectation: every assertion currently FAILS for the stated reason (the grader
manufactures a false zero on a correct-but-naturally-phrased answer).
"""
import shutil

from helpers import REPO_ROOT, crit, grade_inprocess, grade_rewardkit

CFILL01_TESTS = REPO_ROOT / "tasks/context-management/multistep-context-fill-01/steps/19-recall/tests"
CONV03_TESTS = REPO_ROOT / "tasks/conversation-persona/multistep-memory-conversational-03/steps/07-recall/tests"
AGENTIC_TESTS = REPO_ROOT / "tasks/research-rag/agentic-research-with-memory-01/tests"
FACTUAL_TESTS = REPO_ROOT / "tasks/research-rag/factual-lookup-cited-01/tests"
PANDAS_REWARD = REPO_ROOT / "tasks/data-analytics/pandas-sql-from-nl-01/tests/reward.py"
PANDAS_ENV = REPO_ROOT / "tasks/data-analytics/pandas-sql-from-nl-01/environment"


def _ws(tmp_path, name, filename, text):
    d = tmp_path / name
    d.mkdir()
    (d / filename).write_text(text)
    return d


# --- context-fill-01: honest provenance must not be docked -------------------

def test_context_fill_01_honest_provenance_scores_full(tmp_path):
    """An exactly-correct current-state answer (question order) that carries
    honest provenance — naming at most ONE superseded value per line — currently
    scores ~0.33: the unanchored global-regex stale-counter docks every prior
    value mentioned, so a harness with BETTER retention scores LOWER. Required:
    1.0 once scoring is line-anchored per fact (the -02 standard)."""
    answer = "\n".join([
        "1. Okonkwo (replaced Vance)",
        "2. Northwind (BrightPath's bid was rejected)",
        "3. 2027 Q4 (slipped from Q3 2027)",
        "4. $5.1M (raised from $4.2M)",
        "5. 4 satellites (reduced from 6 satellites)",
        "6. B12",
        "7. OrbitOS 3.1",
        "8. Cardinal",
        "9. 7 years (down from 12 years)",
        "10. 2026-03-15",
        "11. Phoenix (relocated from Denver)",
        "12. R-32 (replacing R-410A)",
    ]) + "\n"
    ws = _ws(tmp_path, "cfill01", "answer.md", answer)
    r = grade_rewardkit(CFILL01_TESTS, ws)
    assert r["_reward"] == 1.0, r


# --- conv-03: explicit negation of a sibling must still credit the fact ------

def _conv03_answer():
    return "\n".join([
        "1. Comet",
        "2. shellfish",
        "3. June 22",
        "4. structural engineer",
        "5. Blade Runner 2049 — Dario's pick is Arrival, not mine",
        "6. Boise",
        "7. red 2018 Toyota Tacoma — not the black Corolla my friend Dario drives",
        "8. Lena and Mira",
        "9. olive",
        "10. 12th floor",
        "11. double espresso",
        "12. Saturday",
    ]) + "\n"


def test_conv03_movie_explicit_negation_scores(tmp_path):
    """Naming the sibling film only to REJECT it ('Arrival ... not mine')
    currently zeros the movie fact (global 'arrival' match). Required: credited
    once accept/reject run on the mapped answer line with NEG disambiguation."""
    ws = _ws(tmp_path, "conv03m", "answer.md", _conv03_answer())
    r = grade_rewardkit(CONV03_TESTS, ws)
    assert crit(r, "movie") == 1.0, r


def test_conv03_car_explicit_negation_scores(tmp_path):
    """'not the black Corolla' currently zeros the car fact (global 'corolla|black'
    match). Required: credited once the sibling reject is line-anchored + NEG."""
    ws = _ws(tmp_path, "conv03c", "answer.md", _conv03_answer())
    r = grade_rewardkit(CONV03_TESTS, ws)
    assert crit(r, "car") == 1.0, r


# --- agentic-research: the corpus's own word-form 'eighteen' ----------------

def test_agentic_eighteen_publications_scores(tmp_path):
    """publications/2025.html opens 'Eighteen peer-reviewed...'; an agent quoting
    that wording writes 'eighteen publications', but f5 value_rx is r'\\b18\\b' ->
    false zero. Required: credited once value_rx includes 'eighteen'."""
    brief = ("Mirador Labs published Eighteen peer-reviewed publications in 2025 "
             "([2025 publications](/publications/2025.html)).\n")
    ws = _ws(tmp_path, "agentic", "brief.md", brief)
    r = grade_rewardkit(AGENTIC_TESTS, ws)
    assert crit(r, "f5_pubs") == 1.0, r


# --- factual-lookup: bold / Q enumerators + relative citations --------------

def _factual_answer():
    return (
        "**5.** Aperture is on version 7.2. "
        "Source: https://kb.halcyon.example/products/aperture/releases.html\n"
        "Q6. Headcount is 480 employees. "
        "https://kb.halcyon.example/about.html\n"
        "7. Revenue grew 62% this year. Source: /investors/fy2025.html\n"
    )


def test_factual_bold_enumerator_scores(tmp_path):
    """A markdown-bold enumerator '**5.**' currently fails the block split
    (^N[.)]) -> item 5 unparsed -> false zero. Required: bold tolerated."""
    ws = _ws(tmp_path, "fact5", "answer.md", _factual_answer())
    r = grade_rewardkit(FACTUAL_TESTS, ws)
    assert crit(r, "item:5") == 1.0, r


def test_factual_question_enumerator_scores(tmp_path):
    """A 'Q6.' enumerator currently fails the block split -> false zero.
    Required: Q/Question enumerators tolerated."""
    ws = _ws(tmp_path, "fact6", "answer.md", _factual_answer())
    r = grade_rewardkit(FACTUAL_TESTS, ws)
    assert crit(r, "item:6") == 1.0, r


def test_factual_relative_citation_scores(tmp_path):
    """A scheme-less citation ('Source: /investors/fy2025.html') currently fails
    cites_authoritative (URL regex requires http(s)) -> false zero on correct
    content. Required: bare/relative paths accepted as citations."""
    ws = _ws(tmp_path, "fact7", "answer.md", _factual_answer())
    r = grade_rewardkit(FACTUAL_TESTS, ws)
    assert crit(r, "item:7") == 1.0, r


# --- pandas: integer-valued fields emitted as '3.0' / '2.0' -----------------

def test_pandas_integer_fields_numeric_tolerant(tmp_path):
    """Q2/Q4 are integer answers compared via EXACT string match, so a correct
    '3.0'/'2.0' (numpy/float formatting) is a false zero. Required: graded
    numerically. (Driven in-process so the /opt/canonical tamper gate can be
    redirected to a temp copy.)"""
    canon = tmp_path / "canon"
    ws = tmp_path / "ws"
    canon.mkdir()
    ws.mkdir()
    for f in ("sales.csv", "products.csv"):
        shutil.copy(PANDAS_ENV / f, canon / f)
        shutil.copy(PANDAS_ENV / f, ws / f)
    (ws / "answer.txt").write_text(
        "Q1_WEST_TOTAL=235.25\nQ2_DISTINCT_REGIONS=3.0\n"
        "Q3_TOP_MEAN_REGION=east\nQ4_MISSING_AMOUNT_ROWS=2.0\n"
        "Q5_HARDWARE_GROSS_PROFIT=277.00\nQ6_TOP_PRODUCT_BY_AMOUNT=b\n")
    r = grade_inprocess(PANDAS_REWARD, ws, {"CANONICAL": canon})
    assert r["field:Q2_DISTINCT_REGIONS"] == 1.0, r
    assert r["field:Q4_MISSING_AMOUNT_ROWS"] == 1.0, r

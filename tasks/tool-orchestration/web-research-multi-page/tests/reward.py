"""rewardkit grader for web-research-multi-page — browser-gated fact lookup.

Faithful port of the prior bespoke bash grader. reward = 1.0 iff /app/answer.txt
names the author THIS SITE attributes the quote to (Jim Henson) AND does not also
name a decoy author from the same page (sibling penalty) AND the trajectory shows
a real browser tool call. The browser gate is what makes the task measure
browser-tool USE, not memorized recall — preserved byte-identically here.

Penalty/gate pattern (see exemplar credential-leak-detection): the exact headline
formula lives in a weight-1 `score` criterion; the answer sub-checks and the
browser-used gate ride along as weight-0 informational criteria (they land in
reward-details.json, never moving the FLAT reward -- FOOTGUNS #2).

ORACLE CAVEAT (unchanged): the oracle isn't a browser, so it gets
answer_correct=1 but browser_used=0 -> headline reward 0. The oracle validates the
answer-checking sub-field; a real n=1 proves the browser path.
"""
import glob
import os
import re
from functools import lru_cache
from pathlib import Path

import rewardkit as rk

# Surname uniquely identifies Jim Henson here; decoys are sibling authors from the
# same page (or common real-world misattributions) that must NOT also be named.
DECOYS = [
    "neruda", "emerson", "mother teresa", "teresa", "keillor", "seuss",
    "einstein", "rowling", "marley", "shakespeare", "wilde", "austen",
]

# Match a tool-call whose name is "browser" (openclaw) OR "browser_<verb>"
# (hermes), as a JSON field, OR a bare hermes verb token. Matching only one
# convention would false-zero the other (the ctx-rot scorer trap).
_TOOL_NAME_PAT = re.compile(
    r'"(?:tool|tool_name|name|function|toolName)"\s*:\s*"(browser(?:_[a-z]+)?)"', re.I)
_VERB_PAT = re.compile(
    r"browser_(navigate|snapshot|click|type|scroll|get_images|vision)", re.I)


@lru_cache(maxsize=1)
def _answer(workspace_str: str) -> str:
    """TOLERANT read for the weight-0 answer_present diagnostic + crash safety
    (S4: a single non-UTF8 byte must never raise and VOID the trial). Used only by
    the weight-0 `present` criterion, so its leniency never moves the flat reward."""
    p = Path(workspace_str) / "answer.txt"
    try:
        return p.read_text(errors="replace").lower()
    except Exception:
        return ""


@lru_cache(maxsize=1)
def _scored_answer(workspace_str: str) -> str:
    """STRICT decode for the reward scoring — byte-identical to the old grader's
    `open().read()`: bytes invalid under the default encoding raise and are caught
    -> "" (a garbled answer earns no credit, never spuriously matches a name).
    read_bytes().decode() avoids a bare read_text() while keeping strict semantics."""
    p = Path(workspace_str) / "answer.txt"
    try:
        return p.read_bytes().decode().lower()
    except Exception:
        return ""


@lru_cache(maxsize=1)
def _browser_calls() -> int:
    """Count browser tool-calls across the /logs trajectory (both harness styles)."""
    n = 0
    for path in glob.glob("/logs/**/*", recursive=True):
        if not os.path.isfile(path):
            continue
        try:
            with open(path, errors="ignore") as f:
                blob = f.read()
        except Exception:
            continue
        n += len(_TOOL_NAME_PAT.findall(blob))
        n += len(_VERB_PAT.findall(blob))
    return n


def _answer_correct(workspace_str: str) -> int:
    ans = _scored_answer(workspace_str)
    has_correct = "henson" in ans
    has_decoy = any(d in ans for d in DECOYS)
    return 1 if (has_correct and not has_decoy) else 0


@rk.criterion(description="{label}")
def check(workspace: Path, key: str, label: str):
    ws = str(workspace)
    ans = _scored_answer(ws)
    answer_correct = _answer_correct(ws)
    browser_used = 1 if _browser_calls() > 0 else 0
    reward = 1.0 if (answer_correct and browser_used) else 0.0
    if key == "score":
        return reward
    if key == "correctness":
        return int(reward == 1.0)
    if key == "answer_correct":
        return answer_correct
    if key == "has_correct_author":
        return int("henson" in ans)
    if key == "named_a_decoy":
        return int(any(d in ans for d in DECOYS))
    if key == "browser_used":
        return browser_used
    return 0.0


rk.check("score",
         "reward = 1 iff answer-correct (Henson, no decoy) AND browser tool used",
         weight=1.0)
rk.check("correctness", "headline reward == 1.0", weight=0.0)
rk.check("answer_correct",
         "names Henson without naming a decoy (oracle validates this sub-field)",
         weight=0.0)
rk.check("has_correct_author", "answer contains 'henson'", weight=0.0)
rk.check("named_a_decoy", "answer names a sibling/decoy author (precision penalty)",
         weight=0.0)
rk.check("browser_used",
         "trajectory shows a browser tool call (reward is GATED on this)",
         weight=0.0)


# VOID-vs-wrong diagnostic (weight-0; never moves the FLAT reward -- FOOTGUNS #2).
@rk.criterion(description="{label}")
def present(workspace: Path, key: str, label: str):
    return bool(_answer(str(workspace)).strip())


rk.present("answer_present", "answer persisted (VOID vs present-but-wrong)", weight=0.0)

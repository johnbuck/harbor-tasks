"""Deterministic, LLM-free graded verifier for readme-01 (medium).

Grades the README on the fraction of required sections/facts it documents AND
that match the ACTUAL greet.py code, minus a penalty for documenting features
that do not exist (a fabricated flag / wrong default).

greet.py (ground truth):
  - positional `name`, nargs="+": accepts ONE OR MORE names.
  - --times N      (default 1): print each greeting N times.
  - --greeting WORD (default "Hello"): the greeting word.
  - --shout        (store_true): print the greeting uppercased.
  - prints "<greeting>, <name>!" per line.
  - There is NO --upper / --uppercase / --caps / --loud / --name flag, no
    --lower, no -t/-n short opts, and the greeting default is "Hello" (not
    "Hi"/"Hey"), times default is 1 (not 0/3).

Sub-criteria (recall, N_pos = 9):
  P1  describes what the program does (greeting CLI).
  P2  shows how to run it (`python greet.py ...` / `greet.py ...`).
  P3  documents the `name` positional argument.
  P4  documents that name accepts one-or-more / multiple names.
  P5  documents --times AND its default of 1.
  P6  documents --greeting AND its default of Hello.
  P7  documents the --shout flag (uppercasing).
  P8  shows an example invocation (a command line running greet.py).
  P9  the example's expected output matches the real "<greeting>, <name>!"
      format (e.g. "Hello, Alice!").

Penalty (precision):
  FAB  documents a flag/behavior that does NOT exist (e.g. --upper, --uppercase,
       --caps, --loud, --lower, --name, --count, --repeat, or a wrong default
       like "default: 3" for --times / a greeting default other than Hello).
       Each distinct fabrication subtracts one point (capped so reward >= 0).

  reward = round(max(0, satisfied - fabrications) / 9, 4)
  correctness = 1 iff satisfied == 9 AND fabrications == 0.

reward.json MUST stay a FLAT dict of scalar numbers (FOOTGUNS #38).
"""

import json
import re
from pathlib import Path

TARGET = Path("/app/README.md")
REWARD = Path("/logs/verifier/reward.json")
N = 9


def _any(patterns, text):
    return any(re.search(p, text) for p in patterns)


def _zero(reason):
    REWARD.write_text(json.dumps(
        {"reward": 0.0, "correctness": 0, "satisfied": 0, "n_checks": N,
         "fabrications": 0}, indent=2))
    print(f"reward 0.0 — {reason}")


CRITERIA = {
    "P1_purpose": [
        r"greet", r"greeting", r"prints?\s+\w*\s*hello", r"says?\s+hello",
    ],
    "P2_how_to_run": [
        r"python3?\s+greet\.py", r"\./greet\.py", r"`greet\.py",
        r"\bgreet\.py\s+\w",
    ],
    "P3_name_positional": [
        r"\bname\b.{0,60}(positional|argument|person|people|to\s+greet|required)",
        r"(positional|argument).{0,30}\bname\b",
        r"name\(s\)",
    ],
    "P4_name_multiple": [
        r"one\s+or\s+more", r"multiple\s+names?", r"several\s+names?",
        r"names?\s*\(\+\)|nargs", r"\+\s*\)|name\s*\.\.\.|name \[name",
        r"each\s+name", r"list\s+of\s+names?", r"any\s+number\s+of\s+names?",
        r"accepts?\s+(1\+|one\s+or\s+more|multiple)",
    ],
    "P5_times_default": [
        r"--times\b.{0,160}(default\W{0,4}1\b|\bdefault\b[^0-9]{0,20}\bone\b)",
        r"(default\W{0,4}1\b).{0,160}--times",
        r"--times.{0,80}\b1\b.{0,40}default", r"default.{0,40}--times.{0,40}\b1\b",
    ],
    "P6_greeting_default": [
        r"--greeting\b.{0,160}(default\W{0,12}hello|hello\W{0,12}default)",
        r"(default\W{0,12}hello).{0,160}--greeting",
        r"--greeting\b.{0,120}hello",
    ],
    "P7_shout_flag": [
        r"--shout\b",
    ],
    "P8_example_invocation": [
        r"(python3?\s+|\./)?greet\.py\s+\w+",
    ],
    "P9_example_output_format": [
        r"hello,\s+\w+!",          # default greeting in example output
        r"\b[a-z]+,\s+\w+!",        # any "<word>, <name>!" line (custom greeting)
        r"HELLO,\s+\w+!",           # shout example
    ],
}

# Fabrications: flags / defaults that are NOT in greet.py.
FABRICATIONS = {
    "fab_upper_flag": [r"--upper(case)?\b", r"--caps\b", r"--loud\b",
                       r"--all-caps\b", r"--capitalize\b"],
    "fab_lower_flag": [r"--lower(case)?\b"],
    "fab_name_flag": [r"--name\b", r"--names\b"],
    "fab_count_flag": [r"--count\b", r"--repeat\b", r"--number\b", r"--n\b"],
    "fab_greeting_short": [r"--greet\b(?!ing)"],
    "fab_short_opts": [r"\s-t\b", r"\s-n\b", r"\s-g\b", r"\s-s\b"],
    "fab_wrong_times_default": [
        r"--times\b.{0,160}default\W{0,4}(0|2|3|5|10)\b",
        r"default\W{0,4}(0|2|3|5|10)\b.{0,40}--times",
    ],
    "fab_wrong_greeting_default": [
        r"--greeting\b.{0,160}default\W{0,12}(hi|hey|greetings|welcome|hola)\b",
    ],
}


def main():
    if not TARGET.exists():
        _zero("no /app/README.md produced")
        return
    raw = TARGET.read_text()
    text = raw.lower()
    if not text.strip():
        _zero("/app/README.md is empty")
        return

    # P9 needs case sensitivity for the SHOUT variant; check raw too.
    results = {}
    for name, pats in CRITERIA.items():
        if name == "P9_example_output_format":
            results[name] = _any(pats[:2], text) or bool(
                re.search(r"[A-Z]+,\s+\w+!", raw))
        else:
            results[name] = _any(pats, text)

    fab_hits = {k: _any(pats, text) for k, pats in FABRICATIONS.items()}
    fabrications = sum(1 for v in fab_hits.values() if v)

    satisfied = sum(1 for v in results.values() if v)
    net = max(0, satisfied - fabrications)
    reward = round(net / N, 4)
    correctness = 1 if (satisfied == N and fabrications == 0) else 0

    out = {"reward": reward, "correctness": correctness,
           "satisfied": satisfied, "n_checks": N, "fabrications": fabrications}
    out.update({f"ok_{k}": int(v) for k, v in results.items()})
    out.update({k: int(v) for k, v in fab_hits.items()})
    REWARD.write_text(json.dumps(out, indent=2))
    print(json.dumps(out))


if __name__ == "__main__":
    main()

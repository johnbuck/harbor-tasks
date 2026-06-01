"""Hidden grader for the full count_words contract (baked at /opt/canonical/,
not visible to the agent at /app). Emits the per-case pass list as JSON so the
verifier can grade completeness across the contract's edge cases.

Each case is (input, expected). The visible tests cover only basic + empty; the
punctuation-only and hyphenation cases here are the gradient — a naive
`len(text.split())` fix passes the basics but FAILS the punctuation cases,
landing a partial reward instead of a flat pass.
"""
import json
import sys

sys.path.insert(0, "/app")
try:
    from wordcount import count_words
except Exception as e:  # import/syntax error in the agent's file
    print(json.dumps({"_import_error": str(e)}))
    sys.exit(0)

CASES = [
    # basic (also covered by visible tests — kept so the grader is self-contained)
    ("", 0),
    ("   \t\n  ", 0),
    ("hello", 1),
    ("hello world foo bar", 4),
    ("   hello   world   ", 2),
    # rule 2: punctuation-only tokens are NOT words
    ("hello -- world", 2),
    ("... done", 1),
    ("wait !? really", 2),
    ("a — b", 2),
    (":) :( ok", 1),
    # rule 3: hyphenated / apostrophised words are ONE word
    ("mother-in-law arrived", 2),
    ("don't stop", 2),
    ("send an e-mail now", 4),
    # combined: the, well-known, author, yes, wrote (the two `--` don't count)
    ("the well-known author -- yes -- wrote", 5),
]

results = {}
for i, (text, expected) in enumerate(CASES):
    try:
        got = count_words(text)
        results[f"case_{i:02d}"] = bool(got == expected)
    except Exception:
        results[f"case_{i:02d}"] = False

print(json.dumps(results))

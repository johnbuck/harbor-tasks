"""Hidden grader for the full is_palindrome contract (baked at /opt/canonical/,
not visible to the agent at /app). Emits the per-case pass list as JSON.

The visible tests cover ASCII letters with spaces/punctuation. The gradient
cases here are digits, no-alphanumeric input, and Unicode case-FOLDING: a fix
that uses `str.lower()` (the obvious cleanup) passes the visible + ASCII hidden
cases but FAILS the casefold-specific cases (`"ßss"` folds to `"ssss"` — a
palindrome — but `.lower()` leaves the `ß` and breaks symmetry), landing a
partial reward instead of a flat pass.
"""
import json
import sys

sys.path.insert(0, "/app")
try:
    from palindrome import is_palindrome
except Exception as e:  # import/syntax error in the agent's file
    print(json.dumps({"_import_error": str(e)}))
    sys.exit(0)

CASES = [
    # basic ASCII (also covered by visible tests — kept for self-containment)
    ("racecar", True),
    ("hello", False),
    ("", True),
    ("A man a plan a canal Panama", True),
    ("Was it a car or a cat I saw?", True),
    # digits
    ("12321", True),
    ("12345", False),
    ("ab1ba... no", False),
    ("1a2a1", True),
    # no alphanumeric characters at all -> palindrome
    ("!!!", True),
    ("  ,. -- :)", True),
    # Unicode case-FOLDING — every True here is a discriminator that casefold
    # handles but a naive str.lower() does NOT (lower leaves the ß and breaks
    # the symmetry that case-folding to "ss" restores).
    ("ßss", True),         # casefold -> "ssss"
    ("ssß", True),         # casefold -> "ssss"
    ("aßssa", True),       # casefold -> "assssa"
    ("ssßsss", True),      # casefold -> "sssssss"
    ("no ßss on", True),   # casefold + strip non-alnum -> "nosssson"
    ("ßabc", False),       # folds to "ssabc" — not a palindrome either way
]

results = {}
for i, (text, expected) in enumerate(CASES):
    try:
        got = is_palindrome(text)
        results[f"case_{i:02d}"] = bool(got is expected or got == expected)
    except Exception:
        results[f"case_{i:02d}"] = False

print(json.dumps(results))

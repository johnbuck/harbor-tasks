"""Planted mutant: forgets to strip leading/trailing hyphens.

A meaningful test (e.g. slugify("Hello, World!") == "hello-world") catches this
because the mutant returns "hello-world-". Used only by the verifier.
"""

import re


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s

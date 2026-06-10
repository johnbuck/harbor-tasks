"""Mutant M2 — behavior: COLLAPSING RUNS to a SINGLE hyphen.

Uses a single-char replacement (no `+`), so a run of separators becomes MULTIPLE
hyphens instead of one. A test like slugify("a,  b") == "a-b" or
slugify("Hello, World!") == "hello-world" catches this (mutant -> "a---b").
"""

import re


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]", "-", s)  # missing the + quantifier
    return s.strip("-")

"""Mutant M1 — behavior: LOWERCASING. Drops .lower().

A test that asserts uppercase input is lowercased (e.g.
slugify("Hello") == "hello") catches this, because the mutant returns "Hello"
(after the non-alnum sub leaves uppercase letters as separators it actually
yields "-ello"-style garbage). Either way an exact-equality test on a mixed-case
input kills it.
"""

import re


def slugify(s: str) -> str:
    s = s.strip()  # no .lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

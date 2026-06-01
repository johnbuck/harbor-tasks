"""Mutant M4 — behavior: PRESERVING DIGITS / alphanumerics.

Treats digits as separators ([^a-z] instead of [^a-z0-9]), so numbers in the
input are destroyed. A test that includes digits and expects them preserved
(e.g. slugify("Route 66 Diner") == "route-66-diner") catches it (mutant ->
"route-diner").
"""

import re


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z]+", "-", s)  # digits no longer preserved
    return s.strip("-")

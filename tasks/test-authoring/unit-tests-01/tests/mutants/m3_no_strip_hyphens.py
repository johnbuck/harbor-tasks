"""Mutant M3 — behavior: STRIPPING leading/trailing hyphens.

Forgets the final .strip("-"). A test on input with leading/trailing
punctuation (e.g. slugify("Hello, World!") == "hello-world", which would be
"hello-world-" under the mutant, or slugify("!hi!") == "hi") catches it.
"""

import re


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s  # no strip("-")

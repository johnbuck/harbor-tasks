"""String utilities."""

import re


def slugify(s: str) -> str:
    """Lowercase, replace runs of non-alphanumerics with a single hyphen,
    and strip leading/trailing hyphens. E.g. "Hello, World!" -> "hello-world"."""
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

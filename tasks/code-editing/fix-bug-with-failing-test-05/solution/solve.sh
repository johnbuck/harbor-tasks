#!/bin/bash
# Reference solution — implements the FULL contract (flatten lists AND tuples to
# arbitrary depth; strings/bytes and all other types are atoms; input not
# mutated). Scores 1.0.
set -e

cat > /app/flatten.py <<'EOF'
"""Nested-collection flattener implementing the flatten contract."""


def flatten(items: list) -> list:
    """Recursively flatten nested lists and tuples into a single flat list.

    Lists and tuples are descended into to arbitrary depth. Strings, bytes, and
    every other element (dict, set, int, None, ...) are kept as atoms. The input
    is not mutated.
    """
    out: list = []
    for x in items:
        if isinstance(x, (list, tuple)):
            out.extend(flatten(list(x)))
        else:
            out.append(x)
    return out
EOF

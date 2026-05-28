#!/bin/bash
set -e

cat > /app/flatten.py <<'EOF'
"""Nested-list flattener."""


def flatten(items: list) -> list:
    """Recursively flatten arbitrarily-nested lists into a single flat list."""
    out: list = []
    for x in items:
        if isinstance(x, list):
            out.extend(flatten(x))
        else:
            out.append(x)
    return out
EOF

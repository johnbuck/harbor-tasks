#!/bin/bash
# Reference solution — used by the `oracle` agent for sanity-checking the task.
set -e

cat > /app/wordcount.py <<'EOF'
"""Tiny word-count utility."""


def count_words(text: str) -> int:
    """Return the number of whitespace-delimited words in `text`."""
    return len(text.split())
EOF

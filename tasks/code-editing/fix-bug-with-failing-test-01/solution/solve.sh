#!/bin/bash
# Reference solution — implements the FULL contract (punctuation-only tokens
# excluded, hyphenated/apostrophised words counted once). Scores 1.0.
set -e

cat > /app/wordcount.py <<'EOF'
"""Tiny word-count utility implementing the count_words contract."""


def count_words(text: str) -> int:
    """Return the number of words in `text`.

    A word is a whitespace-delimited token containing at least one alphanumeric
    character; purely-punctuation tokens do not count. Hyphenated and
    apostrophised words are a single token (str.split keeps them whole).
    """
    return sum(1 for tok in text.split() if any(ch.isalnum() for ch in tok))
EOF

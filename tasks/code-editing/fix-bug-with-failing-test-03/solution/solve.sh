#!/bin/bash
# Reference solution — implements the FULL contract (alphanumeric-only, digits
# count, no-alphanumeric -> True, Unicode case-FOLDING via str.casefold). 1.0.
set -e

cat > /app/palindrome.py <<'EOF'
"""Palindrome checker implementing the is_palindrome contract."""


def is_palindrome(s: str) -> bool:
    """Return True if `s` reads the same forwards and backwards.

    Only alphanumeric characters are considered; comparison is case-insensitive
    via Unicode case folding (str.casefold), so e.g. "ßss" folds to "ssss".
    The empty string and any string with no alphanumeric characters are
    palindromes.
    """
    cleaned = "".join(c.casefold() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]
EOF

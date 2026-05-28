#!/bin/bash
set -e

cat > /app/palindrome.py <<'EOF'
"""Palindrome checker."""


def is_palindrome(s: str) -> bool:
    """Return True if `s` reads the same forwards and backwards, ignoring
    case and any non-alphanumeric characters.
    """
    cleaned = [c.lower() for c in s if c.isalnum()]
    return cleaned == cleaned[::-1]
EOF

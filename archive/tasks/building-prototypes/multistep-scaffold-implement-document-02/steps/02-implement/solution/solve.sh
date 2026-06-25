#!/bin/bash
# Oracle — step 2: implement slugify, truncate (suffix-aware), word_count.
set -e

cat > /app/textkit/__init__.py <<'EOF'
import re

def slugify(s):
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')

def truncate(s, n, suffix="..."):
    if len(s) <= n:
        return s
    return s[:n - len(suffix)] + suffix

def word_count(s):
    return len(s.split())
EOF

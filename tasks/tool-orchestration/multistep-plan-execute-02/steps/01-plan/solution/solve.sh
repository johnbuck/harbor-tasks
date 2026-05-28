#!/bin/bash
set -e
cat > /app/plan.md <<'EOF'
# wordfreq.py Implementation Plan

1. Parse command-line argument to get the input text file path using `sys.argv`.
2. Read the entire file, split on whitespace, and lowercase each token to build a list of words.
3. Use `collections.Counter` to count word frequencies.
4. Print the most common word (the first element from `Counter.most_common(1)`) to stdout.
EOF

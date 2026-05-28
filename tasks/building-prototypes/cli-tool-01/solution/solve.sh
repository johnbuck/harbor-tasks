#!/bin/bash
# Reference solution.
set -e

cat > /app/linecount.py <<'EOF'
import sys

with open(sys.argv[1]) as f:
    print(sum(1 for _ in f))
EOF

#!/bin/bash
set -e

cat > /app/calc/__init__.py <<'EOF'
def add(a, b):
    return a + b
EOF

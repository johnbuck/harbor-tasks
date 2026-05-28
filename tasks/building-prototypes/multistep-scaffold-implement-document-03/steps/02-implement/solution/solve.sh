#!/bin/bash
set -e

cat > /app/tempconv/__init__.py <<'EOF'
def c_to_f(c):
    return c * 9 / 5 + 32
EOF

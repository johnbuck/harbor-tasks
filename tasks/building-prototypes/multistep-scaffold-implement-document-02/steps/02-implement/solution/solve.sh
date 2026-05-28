#!/bin/bash
set -e

cat > /app/textkit/__init__.py <<'EOF'
import re

def slugify(s):
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')
EOF

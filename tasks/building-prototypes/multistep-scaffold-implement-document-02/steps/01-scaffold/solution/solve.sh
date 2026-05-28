#!/bin/bash
set -e

mkdir -p /app/textkit /app/tests

cat > /app/textkit/__init__.py <<'EOF'
def slugify(s):
    raise NotImplementedError
EOF

cat > /app/tests/test_textkit.py <<'EOF'
from textkit import slugify

def test_slugify_basic():
    assert slugify("Hello, World!") == "hello-world"
EOF

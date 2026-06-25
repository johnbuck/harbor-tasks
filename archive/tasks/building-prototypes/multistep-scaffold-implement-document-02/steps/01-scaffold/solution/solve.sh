#!/bin/bash
# Oracle — step 1: scaffold textkit with three stubs + a test suite.
set -e

mkdir -p /app/textkit /app/tests

cat > /app/textkit/__init__.py <<'EOF'
def slugify(s):
    raise NotImplementedError

def truncate(s, n, suffix="..."):
    raise NotImplementedError

def word_count(s):
    raise NotImplementedError
EOF

cat > /app/tests/test_textkit.py <<'EOF'
from textkit import slugify, truncate, word_count

def test_slugify_basic():
    assert slugify("Hello, World!") == "hello-world"

def test_slugify_empty():
    assert slugify("") == ""

def test_truncate_long():
    assert truncate("hello world", 8) == "hello..."

def test_truncate_short():
    assert truncate("hi", 8) == "hi"

def test_word_count():
    assert word_count("  the  quick brown   fox ") == 4
EOF

#!/bin/bash
# Reference solution — used by the `oracle` agent to sanity-check the task.
set -e

mkdir -p /app/tests
cat > /app/tests/test_slugify.py <<'EOF'
from stringutils import slugify


def test_basic_lowercase():
    assert slugify("Hello World") == "hello-world"


def test_punctuation_collapses():
    assert slugify("Hello, World!") == "hello-world"


def test_multiple_separators_collapse():
    assert slugify("a   --  b") == "a-b"


def test_strips_leading_and_trailing():
    assert slugify("  !Hello!  ") == "hello"


def test_alphanumerics_preserved():
    assert slugify("Route 66 Diner") == "route-66-diner"
EOF

#!/bin/bash
set -e
cat > /app/test_wordfreq.py <<'EOF'
import subprocess
import tempfile
import os

BIN = "/app/wordfreq.py"


def run(text, *flags):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(text); path = f.name
    try:
        r = subprocess.run(["python", BIN, path, *flags],
                           capture_output=True, text=True, check=True)
        return r.stdout.strip()
    finally:
        os.unlink(path)


def test_clear_winner():
    assert run("apple apple apple banana cherry") == "apple"


def test_punctuation_stripped():
    # "dog" appears 3x once punctuation is stripped.
    assert run("dog, dog. dog! cat") == "dog"


def test_alphabetical_tiebreak():
    # fox and dog tie at 2; "dog" < "fox".
    assert run("fox fox dog dog") == "dog"


def test_stopwords_and_minlen():
    out = run("the the the cat cat dog", "--stopwords", "the", "--min-len", "3")
    assert out == "cat"


def test_top_format():
    out = run("a a a b b c", "--top", "2")
    assert out.splitlines() == ["a 3", "b 2"]
EOF

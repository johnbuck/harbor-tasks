#!/bin/bash
set -e
cat > /app/test_wordfreq.py <<'EOF'
import subprocess
import tempfile
import os

def run_wordfreq(text):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(text)
        path = f.name
    try:
        result = subprocess.run(
            ["python", "/app/wordfreq.py", path],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    finally:
        os.unlink(path)

def test_clear_winner():
    result = run_wordfreq("apple banana apple cherry apple banana apple grape apple")
    assert result == "apple"

def test_lowercase_normalization():
    result = run_wordfreq("Dog dog DOG cat")
    assert result == "dog"

def test_single_word():
    result = run_wordfreq("hello")
    assert result == "hello"
EOF

#!/bin/bash
set -e
cat > /app/test_c2f.py <<'EOF'
import subprocess

def run_c2f(celsius):
    result = subprocess.run(
        ["python", "/app/c2f.py", str(celsius)],
        capture_output=True, text=True, check=True
    )
    return result.stdout.strip()

def test_boiling_point():
    assert run_c2f(100) == "212.0"

def test_freezing_point():
    assert run_c2f(0) == "32.0"

def test_negative_forty():
    # -40 C == -40 F (the crossover point)
    assert run_c2f(-40) == "-40.0"

def test_body_temperature():
    # 37 C ~= 98.6 F
    assert run_c2f(37) == "98.6"
EOF

#!/bin/bash
set -e
cat > /app/test_tempconv.py <<'EOF'
import subprocess

BIN = "/app/tempconv.py"


def run(mode, value):
    return subprocess.run(
        ["python", BIN, mode, str(value)],
        capture_output=True, text=True
    )


def out(mode, value):
    r = run(mode, value)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


def test_c2f():
    assert out("c2f", 100) == "212.00"
    assert out("c2f", -40) == "-40.00"


def test_f2c():
    assert out("f2c", 98.6) == "37.00"


def test_c2k():
    assert out("c2k", 0) == "273.15"


def test_k2c():
    assert out("k2c", 0) == "-273.15"


def test_two_decimals():
    assert out("c2f", 0) == "32.00"


def test_absolute_zero_exits_2():
    r = run("c2k", -300)
    assert r.returncode == 2
    assert r.stdout.strip() == ""


def test_unknown_mode_exits_2():
    r = run("x2y", 10)
    assert r.returncode == 2
EOF

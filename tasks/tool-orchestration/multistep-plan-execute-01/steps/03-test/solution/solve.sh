#!/bin/bash
set -e
cat > /app/test_csv2json.py <<'EOF'
import json
import subprocess
import tempfile
import os

BIN = "/app/csv2json.py"


def run(csv_content, *flags):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        path = f.name
    try:
        r = subprocess.run(["python", BIN, path, *flags],
                           capture_output=True, text=True, check=True)
        return json.loads(r.stdout.strip())
    finally:
        os.unlink(path)


CSV = "name,age,city\nAlice,30,London\nBob,25,Paris\nCleo,42,Paris\n"


def test_base_strings():
    data = run(CSV)
    assert data[0] == {"name": "Alice", "age": "30", "city": "London"}


def test_int_coercion():
    data = run(CSV, "--int", "age")
    assert data[0]["age"] == 30
    assert isinstance(data[0]["age"], int)


def test_filter():
    data = run(CSV, "--filter", "city=Paris")
    assert [d["name"] for d in data] == ["Bob", "Cleo"]


def test_numeric_sort():
    csv = "name,n\na,9\nb,10\nc,2\n"
    data = run(csv, "--int", "n", "--sort", "n")
    assert [d["n"] for d in data] == [2, 9, 10]


def test_empty_header_only():
    data = run("name,age,city\n")
    assert data == []
EOF

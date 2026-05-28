#!/bin/bash
set -e
cat > /app/test_csv2json.py <<'EOF'
import json
import subprocess
import tempfile
import os

def run_csv2json(csv_content):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        path = f.name
    try:
        result = subprocess.run(
            ["python", "/app/csv2json.py", path],
            capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout.strip())
    finally:
        os.unlink(path)

def test_two_rows():
    data = run_csv2json("name,age\nAlice,30\nBob,25\n")
    assert data == [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]

def test_single_row():
    data = run_csv2json("x,y\n1,2\n")
    assert data == [{"x": "1", "y": "2"}]

def test_output_is_list():
    data = run_csv2json("a,b\n1,2\n3,4\n")
    assert isinstance(data, list)
    assert len(data) == 2
EOF

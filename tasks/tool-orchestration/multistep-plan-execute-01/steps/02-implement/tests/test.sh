#!/bin/bash
# Write a fixture CSV, run csv2json.py, parse output, compare to expected.
mkdir -p /logs/verifier
cat > /tmp/fixture.csv <<'EOF'
name,age,city
Alice,30,London
Bob,25,Paris
EOF

if [ ! -f /app/csv2json.py ]; then
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
    exit 0
fi

output=$(python /app/csv2json.py /tmp/fixture.csv 2>/dev/null)

result=$(python3 - <<'PYEOF'
import json, sys

output = """PLACEHOLDER"""
try:
    data = json.loads(output)
except Exception as e:
    print("FAIL: json parse error:", e)
    sys.exit(1)

expected = [
    {"name": "Alice", "age": "30", "city": "London"},
    {"name": "Bob",   "age": "25", "city": "Paris"},
]
if data == expected:
    print("PASS")
else:
    print("FAIL: got", json.dumps(data))
PYEOF
)

# Re-run properly passing the output via env to avoid shell escaping issues
result=$(OUTPUT="$output" python3 - <<'PYEOF'
import json, sys, os

output = os.environ.get("OUTPUT", "")
try:
    data = json.loads(output.strip())
except Exception as e:
    print("FAIL: json parse error:", e)
    sys.exit(1)

expected = [
    {"name": "Alice", "age": "30", "city": "London"},
    {"name": "Bob",   "age": "25", "city": "Paris"},
]
if data == expected:
    print("PASS")
else:
    print("FAIL: got", json.dumps(data))
    sys.exit(1)
PYEOF
)

if [ "$result" = "PASS" ]; then
    echo '{"reward": 1, "correctness": 1}' > /logs/verifier/reward.json
else
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
fi

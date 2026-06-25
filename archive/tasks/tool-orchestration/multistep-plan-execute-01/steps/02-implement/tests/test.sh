#!/bin/bash
# Implement-step gate (informational; only the FINAL step counts toward reward).
# Spot-checks base conversion + --int integer coercion.
mkdir -p /logs/verifier
if [ ! -f /app/csv2json.py ]; then
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
    exit 0
fi
cat > /tmp/fixture.csv <<'EOF'
name,age,city
Alice,30,London
Bob,25,Paris
EOF

python /app/csv2json.py /tmp/fixture.csv --int age > /tmp/out.json 2>/dev/null
result=$(python3 - <<'PY'
import json
try:
    data = json.load(open("/tmp/out.json"))
except Exception:
    print("FAIL"); raise SystemExit
exp = [
    {"name": "Alice", "age": 30, "city": "London"},
    {"name": "Bob",   "age": 25, "city": "Paris"},
]
print("PASS" if data == exp else "FAIL")
PY
)
if [ "$result" = "PASS" ]; then
    echo '{"reward": 1, "correctness": 1}' > /logs/verifier/reward.json
else
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
fi

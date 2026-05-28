#!/bin/bash
# Verifier: expected files exist and the package imports cleanly.
mkdir -p /logs/verifier

reward=0

# Check required files exist
if [ -f /app/calc/__init__.py ] && [ -f /app/tests/test_calc.py ]; then
    # Check the package is importable
    if python3 -c "from calc import add" 2>/dev/null; then
        reward=1
    fi
fi

echo "{\"reward\": ${reward}, \"correctness\": ${reward}}" > /logs/verifier/reward.json

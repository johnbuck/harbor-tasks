#!/bin/bash
# Verifier: expected files exist and the package imports cleanly.
mkdir -p /logs/verifier

reward=0

if [ -f /app/tempconv/__init__.py ] && [ -f /app/tests/test_tempconv.py ]; then
    if python3 -c "from tempconv import c_to_f" 2>/dev/null; then
        reward=1
    fi
fi

echo "{\"reward\": ${reward}, \"correctness\": ${reward}}" > /logs/verifier/reward.json

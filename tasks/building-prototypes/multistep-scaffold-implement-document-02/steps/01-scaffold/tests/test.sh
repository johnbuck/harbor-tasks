#!/bin/bash
# Verifier: expected files exist and the package imports cleanly.
mkdir -p /logs/verifier

reward=0

if [ -f /app/textkit/__init__.py ] && [ -f /app/tests/test_textkit.py ]; then
    if python3 -c "from textkit import slugify" 2>/dev/null; then
        reward=1
    fi
fi

echo "{\"reward\": ${reward}, \"correctness\": ${reward}}" > /logs/verifier/reward.json

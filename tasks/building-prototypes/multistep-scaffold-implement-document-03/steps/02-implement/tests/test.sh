#!/bin/bash
# Verifier: pytest must pass.
mkdir -p /logs/verifier

cd /app && python -m pytest tests/test_tempconv.py -q 2>&1
if [ $? -eq 0 ]; then
    reward=1
else
    reward=0
fi

echo "{\"reward\": ${reward}, \"correctness\": ${reward}}" > /logs/verifier/reward.json

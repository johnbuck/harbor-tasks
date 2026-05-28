#!/bin/bash
mkdir -p /logs/verifier
if [ ! -f /app/test_c2f.py ]; then
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
    exit 0
fi
cd /app && python -m pytest test_c2f.py -q 2>/dev/null
if [ $? -eq 0 ]; then
    echo '{"reward": 1, "correctness": 1}' > /logs/verifier/reward.json
else
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
fi

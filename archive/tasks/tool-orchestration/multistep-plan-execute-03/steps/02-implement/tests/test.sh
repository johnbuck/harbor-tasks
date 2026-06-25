#!/bin/bash
# Implement-step gate (informational; only the FINAL step counts toward reward).
# Spot-checks a couple of conversions + the absolute-zero exit code.
mkdir -p /logs/verifier
if [ ! -f /app/tempconv.py ]; then
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
    exit 0
fi
ok=1
[ "$(python /app/tempconv.py c2f 100 2>/dev/null | tr -d '[:space:]')" = "212.00" ] || ok=0
[ "$(python /app/tempconv.py k2c 0   2>/dev/null | tr -d '[:space:]')" = "-273.15" ] || ok=0
python /app/tempconv.py c2k -300 >/dev/null 2>&1; [ $? -eq 2 ] || ok=0
if [ "$ok" -eq 1 ]; then
    echo '{"reward": 1, "correctness": 1}' > /logs/verifier/reward.json
else
    echo '{"reward": 0, "correctness": 0}' > /logs/verifier/reward.json
fi

#!/bin/bash
# Per-step verifier: always 1.0 for the fact-sharing steps (sub-tests pass
# trivially — the real check is in the final recall step + the trial-level
# memory check).
mkdir -p /logs/verifier
echo '{"reward": 1.0}' > /logs/verifier/reward.json

#!/bin/bash
# Per-step verifier: always 1.0 for the correction step (sub-test passes
# trivially — the real check is whether the LATEST values surface in the final
# recall step + the trial-level memory check).
mkdir -p /logs/verifier
echo '{"reward": 1.0}' > /logs/verifier/reward.json

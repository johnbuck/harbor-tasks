#!/bin/bash
# Intro step: delivering facts only. Always passes — the real signal is recall.
mkdir -p /logs/verifier
echo '{"reward": 1.0, "correctness": 1.0}' > /logs/verifier/reward.json

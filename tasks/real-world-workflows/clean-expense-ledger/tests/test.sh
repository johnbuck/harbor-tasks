#!/bin/bash
# Deterministic, leak-proof grader (no answer key in the container; expected is
# computed from the rules). Writes /logs/verifier/reward.json.
set -e
mkdir -p /logs/verifier
# S4 crash guard (FOOTGUNS #2): a grader that throws without writing reward.json
# makes Harbor silently DROP the trial. Guarantee a flat numeric reward.json.
python /tests/grade.py || true
[ -s /logs/verifier/reward.json ] || echo '{"reward": 0.0}' > /logs/verifier/reward.json

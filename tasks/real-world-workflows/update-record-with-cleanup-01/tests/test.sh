#!/bin/bash
# Deterministic, leak-proof grader (no answer key in the container; expected is
# computed from the rules). Writes /logs/verifier/reward.json.
set -e
mkdir -p /logs/verifier
python /tests/grade.py

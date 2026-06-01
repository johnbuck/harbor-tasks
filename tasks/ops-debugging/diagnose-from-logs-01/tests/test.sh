#!/bin/bash
# Verifier — runs the deterministic, LLM-free grader, which writes
# /logs/verifier/reward.json. reward = fraction of required root-cause +
# evidence findings the diagnosis identifies (with a red-herring penalty).
set -e
mkdir -p /logs/verifier
python /tests/grade.py

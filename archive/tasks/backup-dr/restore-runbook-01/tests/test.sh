#!/bin/bash
# Verifier — runs the LLM judge, which writes /logs/verifier/reward.json.
set -e
mkdir -p /logs/verifier
python /tests/llm_judge.py

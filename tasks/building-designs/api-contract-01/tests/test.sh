#!/bin/bash
# Mixed verifier: structural OpenAPI check (objective) + LLM judge (quality).
set -e
mkdir -p /logs/verifier
python /tests/grade.py

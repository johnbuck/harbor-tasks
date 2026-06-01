#!/bin/bash
# Deterministic graded verifier: precision+recall over the planted issue set.
set -e
mkdir -p /logs/verifier
python /tests/grade.py

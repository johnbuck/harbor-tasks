#!/bin/bash
# Deterministic graded verifier: per-criterion OpenAPI structural check.
set -e
mkdir -p /logs/verifier
python /tests/grade.py

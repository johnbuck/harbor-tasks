#!/bin/bash
# Deterministic graded verifier: README coverage vs actual greet.py + fabrication penalty.
set -e
mkdir -p /logs/verifier
python /tests/grade.py

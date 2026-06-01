#!/bin/bash
mkdir -p /logs/verifier
if grep -q "MARKER-06-323f111f" /app/notes.md 2>/dev/null; then c=1; else c=0; fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json

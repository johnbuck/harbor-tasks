#!/bin/bash
mkdir -p /logs/verifier
if grep -q "MARKER-03-423c1bd0" /app/notes.md 2>/dev/null; then c=1; else c=0; fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json

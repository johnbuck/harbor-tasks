#!/bin/bash
mkdir -p /logs/verifier
if grep -q "MARKER-03-c1d448ca" /app/notes.md 2>/dev/null; then c=1; else c=0; fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json

#!/bin/bash
mkdir -p /logs/verifier
if grep -q "MARKER-15-c34032b5" /app/notes.md 2>/dev/null; then c=1; else c=0; fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json

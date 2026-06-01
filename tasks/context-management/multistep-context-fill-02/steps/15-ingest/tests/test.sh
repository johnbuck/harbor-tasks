#!/bin/bash
mkdir -p /logs/verifier
if grep -q "MARKER-15-6d57718d" /app/notes.md 2>/dev/null; then c=1; else c=0; fi
echo "{\"reward\": ${c}, \"correctness\": ${c}}" > /logs/verifier/reward.json

#!/bin/bash
set -e
grep -o "MARKER-15-[a-f0-9]*" /app/chunks/chunk_15.txt | head -1 >> /app/notes.md

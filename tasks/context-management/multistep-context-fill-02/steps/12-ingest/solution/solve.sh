#!/bin/bash
set -e
grep -o "MARKER-12-[a-f0-9]*" /app/chunks/chunk_12.txt | head -1 >> /app/notes.md

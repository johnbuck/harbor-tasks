#!/bin/bash
set -e
grep -o "MARKER-16-[a-f0-9]*" /app/chunks/chunk_16.txt | head -1 >> /app/notes.md

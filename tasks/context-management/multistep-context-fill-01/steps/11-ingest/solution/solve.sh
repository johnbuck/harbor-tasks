#!/bin/bash
set -e
grep -o "MARKER-11-[a-f0-9]*" /app/chunks/chunk_11.txt | head -1 >> /app/notes.md

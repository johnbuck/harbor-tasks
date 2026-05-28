#!/bin/bash
set -e
grep -o "MARKER-10-[a-f0-9]*" /app/chunks/chunk_10.txt | head -1 >> /app/notes.md

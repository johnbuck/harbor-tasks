#!/bin/bash
set -e
grep -o "MARKER-01-[a-f0-9]*" /app/chunks/chunk_01.txt | head -1 >> /app/notes.md
grep "IMPORTANT FACTS" /app/chunks/chunk_01.txt >> /app/notes.md

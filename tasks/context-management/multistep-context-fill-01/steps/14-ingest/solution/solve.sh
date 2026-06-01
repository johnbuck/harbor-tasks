#!/bin/bash
set -e
grep -o "MARKER-14-[a-f0-9]*" /app/chunks/chunk_14.txt | head -1 >> /app/notes.md
grep "CORRECTION TO IMPORTANT FACTS" /app/chunks/chunk_14.txt >> /app/notes.md

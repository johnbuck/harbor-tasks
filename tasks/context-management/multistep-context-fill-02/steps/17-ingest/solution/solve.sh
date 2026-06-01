#!/bin/bash
set -e
grep -o "MARKER-17-[a-f0-9]*" /app/chunks/chunk_17.txt | head -1 >> /app/notes.md

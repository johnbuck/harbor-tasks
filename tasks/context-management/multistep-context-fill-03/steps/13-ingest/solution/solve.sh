#!/bin/bash
set -e
grep -o "MARKER-13-[a-f0-9]*" /app/chunks/chunk_13.txt | head -1 >> /app/notes.md

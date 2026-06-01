#!/bin/bash
set -e
grep -o "MARKER-07-[a-f0-9]*" /app/chunks/chunk_07.txt | head -1 >> /app/notes.md

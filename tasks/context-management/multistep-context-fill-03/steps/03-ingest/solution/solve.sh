#!/bin/bash
set -e
grep -o "MARKER-03-[a-f0-9]*" /app/chunks/chunk_03.txt | head -1 >> /app/notes.md

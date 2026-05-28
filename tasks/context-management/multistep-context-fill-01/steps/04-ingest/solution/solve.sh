#!/bin/bash
set -e
grep -o "MARKER-04-[a-f0-9]*" /app/chunks/chunk_04.txt | head -1 >> /app/notes.md

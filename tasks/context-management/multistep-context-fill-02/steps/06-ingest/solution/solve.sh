#!/bin/bash
set -e
grep -o "MARKER-06-[a-f0-9]*" /app/chunks/chunk_06.txt | head -1 >> /app/notes.md

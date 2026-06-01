#!/bin/bash
set -e
grep -o "MARKER-18-[a-f0-9]*" /app/chunks/chunk_18.txt | head -1 >> /app/notes.md

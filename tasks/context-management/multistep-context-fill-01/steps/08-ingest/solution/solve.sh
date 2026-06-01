#!/bin/bash
set -e
grep -o "MARKER-08-[a-f0-9]*" /app/chunks/chunk_08.txt | head -1 >> /app/notes.md

#!/bin/bash
set -e
grep -o "MARKER-09-[a-f0-9]*" /app/chunks/chunk_09.txt | head -1 >> /app/notes.md

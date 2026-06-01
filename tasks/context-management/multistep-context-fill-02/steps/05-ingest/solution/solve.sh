#!/bin/bash
set -e
grep -o "MARKER-05-[a-f0-9]*" /app/chunks/chunk_05.txt | head -1 >> /app/notes.md

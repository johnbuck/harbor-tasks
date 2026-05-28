#!/bin/bash
set -e
grep -o "MARKER-02-[a-f0-9]*" /app/chunks/chunk_02.txt | head -1 >> /app/notes.md

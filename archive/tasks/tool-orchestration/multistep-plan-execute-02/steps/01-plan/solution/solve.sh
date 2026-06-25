#!/bin/bash
set -e
cat > /app/plan.md <<'EOF'
# wordfreq.py Implementation Plan

1. Parse CLI args with `argparse`: positional `file`, plus optional `--top N`
   (int), `--min-len L` (int), and `--stopwords` (comma-separated string). Use
   only the standard library (`sys`, `argparse`, `collections`, `string`).
2. Tokenize: read the file, split on whitespace, lowercase each token, then strip
   leading/trailing punctuation (`token.strip(string.punctuation)`). Drop tokens
   that are empty after stripping. Internal punctuation (e.g. `don't`) is kept.
3. Apply filters: drop tokens shorter than `--min-len`, and drop any token in the
   `--stopwords` set.
4. Count with `collections.Counter`. To make ordering deterministic, sort items
   by `(-count, word)` so ties are broken **alphabetically** (lowest word first).
5. Output: with `--top N`, print the first `N` sorted items as `word count` lines;
   otherwise print just the single top word (the first item of the sorted list).
EOF

#!/bin/bash
set -e
cat > /app/plan.md <<'EOF'
# csv2json.py Implementation Plan

1. Parse CLI args with `argparse`: positional `file`, repeatable `--int COL`
   (`action="append"`), `--filter COL=VAL`, and `--sort COL`. Use `sys`/`argparse`
   from the standard library only.
2. Read the CSV with `csv.DictReader` so the header row becomes object keys; turn
   each row into a plain dict and collect them into a list. If the file has only
   a header (no data rows), the list is empty and we will print `[]`.
3. Apply `--filter COL=VAL` first: keep only rows whose raw string value in `COL`
   equals `VAL`.
4. Apply `--int COL` coercion: for every column named via `--int`, convert that
   field's value with `int(...)` so it serializes as a JSON integer, not a string.
5. Apply `--sort COL`: sort the surviving rows ascending. If `COL` is an `--int`
   column, sort numerically (key = int value); otherwise sort lexicographically
   by the string value.
6. Serialize the final list with `json.dumps` and print to stdout. An empty list
   prints `[]`.
EOF

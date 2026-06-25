#!/bin/bash
set -e
cat > /app/csv2json.py <<'EOF'
import argparse
import csv
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--int", action="append", default=[], dest="int_cols",
                    metavar="COL")
    ap.add_argument("--filter", default=None, metavar="COL=VAL")
    ap.add_argument("--sort", default=None, metavar="COL")
    args = ap.parse_args()

    with open(args.file, newline="") as f:
        rows = [dict(r) for r in csv.DictReader(f)]

    # Filter (before sort), on raw string values.
    if args.filter is not None:
        col, _, val = args.filter.partition("=")
        rows = [r for r in rows if r.get(col) == val]

    # Integer coercion for the emitted JSON.
    for r in rows:
        for c in args.int_cols:
            if c in r and r[c] is not None:
                r[c] = int(r[c])

    # Sort: numeric if the column was declared --int, else lexicographic.
    if args.sort is not None:
        if args.sort in args.int_cols:
            rows.sort(key=lambda r: int(r.get(args.sort, 0)))
        else:
            rows.sort(key=lambda r: str(r.get(args.sort, "")))

    print(json.dumps(rows))


if __name__ == "__main__":
    main()
EOF

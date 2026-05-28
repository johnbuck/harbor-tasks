#!/bin/bash
set -e
cat > /app/csv2json.py <<'EOF'
import csv
import json
import sys

def main():
    path = sys.argv[1]
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = [dict(row) for row in reader]
    print(json.dumps(rows))

if __name__ == "__main__":
    main()
EOF

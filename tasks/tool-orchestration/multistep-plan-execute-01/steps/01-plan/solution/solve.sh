#!/bin/bash
set -e
cat > /app/plan.md <<'EOF'
# csv2json.py Implementation Plan

1. Parse command-line argument to get the input CSV file path using `sys.argv`.
2. Open the file and read it with `csv.DictReader` so the header row becomes object keys automatically.
3. Convert each row (an `OrderedDict`) to a plain dict and collect all rows into a list.
4. Serialize the list to JSON with `json.dumps` and print to stdout.
EOF

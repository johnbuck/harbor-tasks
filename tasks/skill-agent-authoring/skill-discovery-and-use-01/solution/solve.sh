#!/bin/bash
# Oracle: discovers the ONE correct skill (csv-structure-summary) and invokes it
# via its documented entry-point for all 8 files.
set -e
mkdir -p /app/out
for i in $(seq -f '%02g' 1 8); do
    python3 /app/skills/csv-structure-summary/run.py "/app/data/table_${i}.csv" > "/app/out/table_${i}.json"
done

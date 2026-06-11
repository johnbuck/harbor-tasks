#!/bin/bash
# Oracle: discovers the ONE correct skill (tabular-shape-report, read from the
# SKILL.md descriptions — its name does NOT echo the prompt) and invokes it via
# its documented entry-point, WITH the required --null=empty flag, for all 8
# files. The flag is load-bearing: the default mode produces a near-miss.
set -e
mkdir -p /app/out
for i in $(seq -f '%02g' 1 8); do
    python3 /app/skills/tabular-shape-report/run.py "/app/data/table_${i}.csv" --null=empty > "/app/out/table_${i}.json"
done

#!/bin/bash
# Oracle: uses ONLY the three correct tools, once each, and writes the answer.
set -u
rc=$(jsonl-count /app/events.jsonl)
lv=$(semver-max /app/releases.txt)
tc=$(money-sum /app/cart.csv price)
python3 -c "
import json
print(json.dumps({'record_count': int('$rc'), 'latest_version': '$lv'.strip(), 'total_cents': int('$tc')}))
" > /app/answer.json

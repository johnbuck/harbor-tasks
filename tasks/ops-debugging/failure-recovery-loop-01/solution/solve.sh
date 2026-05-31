#!/bin/bash
# Oracle: retry flaky-fetch until success (max 10 tries), then extract token.
set -u
for i in $(seq 1 10); do
    if flaky-fetch /app/payload.txt; then
        break
    fi
done
sed -n 's/^PAYLOAD: //p' /app/payload.txt > /app/token.txt

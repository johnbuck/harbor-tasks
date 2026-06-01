#!/bin/bash
# Oracle: re-read the file (ground truth = 275), do NOT trust memory.
grep cache_ttl_seconds /app/config.yaml | grep -oE '[0-9]+' > /app/answer.txt

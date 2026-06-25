#!/bin/bash
grep cache_ttl_seconds /app/config.yaml | grep -oE '[0-9]+' > /app/seen.txt

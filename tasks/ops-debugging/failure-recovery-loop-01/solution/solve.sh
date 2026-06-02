#!/bin/bash
# Oracle: the adaptive recovery path — read each error, supply the specific fix.
set -u
TOKEN="$(cat /app/.dfetch_token)"
dfetch --release                                                   # clear stale lock
dfetch --region=eu-west --token="$TOKEN" /app/payload.txt          # all requirements met
sed -n 's/^PAYLOAD: //p' /app/payload.txt > /app/token.txt

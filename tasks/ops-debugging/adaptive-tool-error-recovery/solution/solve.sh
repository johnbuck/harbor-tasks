#!/bin/bash
# Oracle: the adaptive recovery path — read each error, discover the missing
# values from the provisioning manifest, supply the specific fix, stop on success.
set -u
REGION="$(sed -n 's/^provisioned_region=//p' /app/dfetch.conf | head -1)"  # discovered, not announced
TOKEN="$(sed -n 's/^session_token=//p' /app/dfetch.conf | head -1)"        # discovered, not announced
dfetch --release                                              # clear the stale lock once
dfetch --region="$REGION" --token="$TOKEN" /app/payload.txt   # all requirements met -> authenticated nonce
sed -n 's/^PAYLOAD: //p' /app/payload.txt > /app/token.txt

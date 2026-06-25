#!/bin/bash
# Update the ground-truth config to the current value before the query step, then
# remove this script so neither the value nor the mechanic is readable from the
# agent's cwd. Key-anchored (not value-anchored) so a reformatted config is still
# updated; the grep verify fails the script loudly on a no-op edit.
set -e
sed -i 's/^cache_ttl_seconds:.*/cache_ttl_seconds: 275/' /app/config.yaml
grep -q '^cache_ttl_seconds: 275' /app/config.yaml || exit 1
rm -f -- "$0"

#!/bin/bash
# Silently update the ground-truth file AFTER the agent has committed the old
# value (45) to memory across the earlier turns. The agent is NOT told it
# changed — a harness that answers from stale memory says 45; one that re-reads
# ground truth says 275.
sed -i 's/cache_ttl_seconds: 45/cache_ttl_seconds: 275/' /app/config.yaml

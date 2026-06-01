#!/bin/bash
# Oracle recall: the FINAL state of record after all 18 weeks (last correction of
# each item; no intermediate values; decoy excluded).
set -e
cat > /app/answer.md <<'ANS'
1. Current migration lead: Amara Okafor
2. Migration target date: 2026-10-30
3. Approved migration budget: $2.8M
4. Target cluster size: 32 nodes
5. Primary region: eu-central-1
6. Target database engine: Aurora
7. Cutover strategy: blue-green
8. Rollback window: 90 minutes
9. Replication topology: multi-primary
10. Monitoring stack: Datadog
11. Compliance tier: SOC2
12. Disaster-recovery site: Dallas
ANS

#!/bin/bash
# Oracle recall: each project's correct values, correctly attributed, one slot/line.
set -e
cat > /app/answer.md <<'ANS'
Orion - Lead: Dr. Elena Marsh
Lyra - Lead: Dr. Victor Crane
Orion - Budget: $7.4M
Lyra - Budget: $3.6M
Orion - Site: Site K9
Lyra - Site: Frankfurt
Orion - Vendor: Heliosat
Lyra - Vendor: Brightlink
Orion - Headcount: 38 engineers
Lyra - Headcount: 52 engineers
Orion - Go-live: 2027-Q2
Lyra - Go-live: 2026-Q4
ANS

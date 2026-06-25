#!/bin/bash
# Reference solution — all 10 facts with the CURRENT value and a citation to the
# AUTHORITATIVE page (never an archived/legacy near-duplicate).
set -e

cat > /app/answer.md <<'EOF'
# Halcyon Systems — factual lookups (cited)

1. Answer: 2013 (Halcyon Systems was founded in 2013).
   Source: http://localhost:8780/about.html

2. Answer: Priya Nandakumar is the current CEO.
   Source: http://localhost:8780/team/leadership.html

3. Answer: Tallinn, Estonia.
   Source: http://localhost:8780/about.html

4. Answer: Aperture is the current flagship product.
   Source: http://localhost:8780/products/index.html

5. Answer: 7.2 is the current GA version of Aperture.
   Source: http://localhost:8780/products/aperture/releases.html

6. Answer: 480 employees.
   Source: http://localhost:8780/about.html

7. Answer: €62 million (FY2025 annual revenue).
   Source: http://localhost:8780/investors/fy2025.html

8. Answer: support@halcyon.example
   Source: http://localhost:8780/contact.html

9. Answer: Frankfurt (eu-central) is the current primary production region.
   Source: http://localhost:8780/infra/regions.html

10. Answer: 1000 requests per day (free tier, current v2 API).
    Source: http://localhost:8780/docs/api/limits.html
EOF

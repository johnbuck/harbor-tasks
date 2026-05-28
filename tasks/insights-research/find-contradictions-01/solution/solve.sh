#!/bin/bash
# Reference solution — used by the `oracle` agent to sanity-check the task.
set -e

cat > /app/contradictions.md <<'EOF'
## Internal Contradiction Found: Q3 Revenue Direction

The document contains one clear internal contradiction regarding Q3 revenue
performance relative to Q2.

**Statement 1 (Executive Summary):**
> "Q3 revenue grew 12% over Q2, marking the second consecutive quarter of
> sequential growth."

**Statement 2 (Revenue Performance section):**
> "Q3 revenue came in below Q2, declining for the second straight quarter as
> macroeconomic headwinds dampened consumer discretionary spending."

These two statements are mutually exclusive. Statement 1 claims Q3 revenue
grew 12% sequentially (above Q2), while Statement 2 claims Q3 revenue declined
below Q2 for the second consecutive quarter. Both cannot be true simultaneously.
EOF

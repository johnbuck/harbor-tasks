#!/bin/bash
# Reference solution — used by the `oracle` agent to sanity-check the task.
set -e

cat > /app/answer.md <<'EOF'
Your cats' names are **Pixel** and **Byte**.

You are allergic to **peanuts**.
EOF

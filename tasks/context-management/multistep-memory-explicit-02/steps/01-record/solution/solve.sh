#!/bin/bash
set -e
cat > /app/notes.md <<'EOF'
# Database Facts

- DB: Postgres 15
- Schema: billing
- Backup schedule: 02:00 UTC
EOF

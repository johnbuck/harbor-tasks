#!/bin/bash
set -e
cat > /app/notes.md <<'EOF'
# API Facts

- API base URL: api.acme.io
- Rate limit: 100 req/min
- Auth header: X-Acme-Key
EOF

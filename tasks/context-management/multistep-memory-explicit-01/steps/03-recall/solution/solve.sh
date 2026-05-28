#!/bin/bash
set -e
cat > /app/answer.md <<'EOF'
The rate limit is 100 req/min and the auth header name is X-Acme-Key.
EOF

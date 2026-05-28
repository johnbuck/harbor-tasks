#!/bin/bash
set -e
cat > /app/notes.md <<'EOF'
# Release Facts

- Release tag: v3.2.1
- Rollback command: make rollback
- On-call: Jordan
EOF

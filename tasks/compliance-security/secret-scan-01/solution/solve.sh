#!/bin/bash
# Reference solution — scores 1.0 under the deterministic graded verifier.
# Lists exactly the four files containing real hardcoded secrets, sorted, and
# omits the example_settings.py decoy (placeholders only).
set -e

cat > /app/findings.txt <<'EOF'
auth.py
config.py
db.py
deploy/id_rsa
EOF

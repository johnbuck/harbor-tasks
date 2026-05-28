#!/bin/bash
set -e

cat > /app/email.txt <<'EOF'
Subject: Your money, your device — meet Lumen Plus

Hi there,

You already trust Lumen to track your finances without ever sending your data
to the cloud. Today we're introducing Lumen Plus — the same privacy-first app,
now with the tools power users have asked for.

With Lumen Plus you get:
- Automatic multi-account reconciliation, so your balances always line up.
- Custom budgets and forecasting that project months ahead.

And nothing changes about what matters most: your data stays encrypted on your
device and never leaves it. No servers, no syncing to us, no exceptions.

Ready to go further while staying just as private?

Upgrade to Lumen Plus from the Settings screen today.

— The Lumen team
EOF

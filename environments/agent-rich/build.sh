#!/usr/bin/env bash
# Build harbor-agents-rich:latest with internal memory-service endpoints injected
# at build time from the gitignored configs/local.env (this PUBLIC repo holds only
# placeholders). See environments/agent-rich/Dockerfile and configs/local.env.example.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"

if [ ! -f configs/local.env ]; then
  echo "ERROR: configs/local.env not found. Copy configs/local.env.example to" >&2
  echo "       configs/local.env and fill in your internal endpoints." >&2
  exit 1
fi
set -a; . configs/local.env; set +a

: "${HINDSIGHT_URL:?set HINDSIGHT_URL in configs/local.env}"
: "${HONCHO_URL:?set HONCHO_URL in configs/local.env}"

TAG="${TAG:-harbor-agents-rich:latest}"
echo "Building $TAG (endpoints injected from configs/local.env)…"
exec docker build -f environments/agent-rich/Dockerfile \
  --build-arg HINDSIGHT_URL="$HINDSIGHT_URL" \
  --build-arg HONCHO_URL="$HONCHO_URL" \
  -t "$TAG" "$@" .

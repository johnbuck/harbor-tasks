#!/usr/bin/env bash
# Launch the Harbor viewer from the CANONICAL FORK, not the ephemeral /tmp checkout.
#
# Why this exists: the dashboard had been started ad-hoc with
# `uv run --project /tmp/harbor …`. /tmp is wiped on reboot, and that upstream
# checkout lacks the subscription-auth patch — so the "Generate Analysis" button
# 500'd after every reboot. This script pins the launch to the fork
# (/home/<user>/harbor), which carries the patch + the prebuilt UI, so the viewer
# survives reboots. See backlog/2026-06-02-viewer-subscription-auth.md.
#
# Usage:  tools/view.sh [PORT]          # default 8089
# Env:    HARBOR_FORK   fork checkout    (default /home/<user>/harbor)
#         HARBOR_JOBS   jobs dir to serve (default <repo>/jobs)
#         HARBOR_HOST   bind host        (default 0.0.0.0)
set -euo pipefail

PORT="${1:-8089}"
HOST="${HARBOR_HOST:-0.0.0.0}"
FORK="${HARBOR_FORK:-/home/<user>/harbor}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
JOBS="${HARBOR_JOBS:-$REPO/jobs}"

# The fork must exist and carry the prebuilt SPA — we launch with --no-build
# (bun isn't installed here, so the viewer can't build the frontend itself).
[ -d "$FORK" ] || { echo "error: fork not found at $FORK (set HARBOR_FORK)"; exit 1; }
[ -d "$FORK/src/harbor/viewer/static" ] || {
  echo "error: $FORK has no prebuilt UI (src/harbor/viewer/static)."
  echo "       copy it from a built checkout, or run once without --no-build where bun is available."
  exit 1
}
[ -d "$JOBS" ] || { echo "error: jobs dir not found at $JOBS (set HARBOR_JOBS)"; exit 1; }

# The analyze/summarize button authenticates via the logged-in `claude` CLI when
# no ANTHROPIC_API_KEY is set. Warn (don't fail) if neither is available.
if [ -z "${ANTHROPIC_API_KEY:-}" ] && ! command -v claude >/dev/null 2>&1; then
  echo "warning: no ANTHROPIC_API_KEY and no \`claude\` CLI — the Generate Analysis button will be inert."
fi

# Harbor's single-port bind has no SO_REUSEADDR, so a just-killed viewer can leave
# $PORT in TIME_WAIT and the relaunch fails. Wait briefly for it to clear.
for _ in $(seq 1 15); do
  ss -ltn 2>/dev/null | grep -q ":$PORT " || break
  echo "  port $PORT still held, waiting for it to free…"
  sleep 1
done

echo "harbor view  ·  fork=$FORK  ·  jobs=$JOBS  ·  http://$HOST:$PORT"
exec uv run --project "$FORK" harbor view "$JOBS" --port "$PORT" --host "$HOST" --no-build

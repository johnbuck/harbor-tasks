#!/usr/bin/env bash
# Launch a SELF-CONTAINED headless Chromium inside THIS trial container and wait
# for its CDP endpoint to answer. Both harnesses' browser tools attach to
# http://127.0.0.1:9222 (openclaw.json browser.cdpUrl / hermes config.yaml
# browser.cdp_url). This replaces the old cross-machine <memory-host> CDP (~/Docker/
# agent-cdp on internal-host:9222) — see
# backlog/2026-06-03-self-contained-browser.md.
#
# Idempotent: if :9222 already answers, no-op. Loopback-only bind. Chromium is
# disowned so it outlives this script and dies with the container (delete:true).
# --no-sandbox/--disable-dev-shm-usage come from /etc/chromium.d/00-harbor-container
# (Debian's /usr/bin/chromium wrapper sources it) — needed to run as root.
set -u
PORT="${CDP_PORT:-9222}"
URL="http://127.0.0.1:${PORT}/json/version"

if curl -sf "$URL" >/dev/null 2>&1; then
  exit 0
fi

nohup /usr/bin/chromium \
  --headless=new \
  --remote-debugging-port="${PORT}" \
  --remote-debugging-address=127.0.0.1 \
  --user-data-dir=/tmp/harbor-cdp-profile \
  --no-first-run --no-default-browser-check \
  >/tmp/harbor-cdp.log 2>&1 &

for _ in $(seq 1 30); do
  if curl -sf "$URL" >/dev/null 2>&1; then
    exit 0
  fi
  sleep 1
done

echo "start-cdp: CDP did not come up on 127.0.0.1:${PORT} within 30s" >&2
tail -20 /tmp/harbor-cdp.log >&2 2>/dev/null || true
exit 1

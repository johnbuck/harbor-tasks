FROM harbor-agents-rich:latest
WORKDIR /app

# Flaky tool: fails (exit 7, transient-ish stderr) on calls 1-3, succeeds on call 4+.
# Counter persists in /var/log/fetch.counter so retries across the same agent
# session accumulate. Tool semantics deliberately mimic a transient network
# error so a competent harness should retry.
RUN cat > /usr/local/bin/flaky-fetch <<'EOF' && chmod +x /usr/local/bin/flaky-fetch
#!/bin/bash
set -u
COUNTER=/var/log/fetch.counter
mkdir -p /var/log
n=$(cat "$COUNTER" 2>/dev/null || echo 0)
n=$((n + 1))
echo "$n" > "$COUNTER"
if (( n < 4 )); then
    echo "flaky-fetch: transient error (attempt $n, try again)" >&2
    exit 7
fi
# Success: writes the payload to the file requested in $1.
out="${1:?usage: flaky-fetch <out-path>}"
echo "PAYLOAD: hgr-7842-OK" > "$out"
echo "flaky-fetch: success on attempt $n" >&2
exit 0
EOF

RUN touch /app/.placeholder

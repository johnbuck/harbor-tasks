FROM harbor-agents-rich:latest
WORKDIR /app

# Adaptive-recovery tool: `dfetch` fails with DIFFERENT, actionable errors until
# the agent reads each one and supplies the specific correction. Unlike a
# deterministic fail-N/succeed tool (where a blind retry loop is optimal), this
# REQUIRES diagnose-and-adapt: a fixed retry of the same command stalls on the
# first unmet requirement forever. Requirements (checked each call, first unmet
# reported):
#   1. --region=<id> must be present
#   2. region must be provisioned (eu-west | us-east) — only revealed by the error
#   3. --token=<t> must match the session token provisioned at /app/.dfetch_token
#   4. a stale lock must be cleared once via `dfetch --release`
# Every invocation (incl. --release) increments /var/log/dfetch.counter so the
# verifier can grade recovery EFFICIENCY on top of correctness.
RUN cat > /usr/local/bin/dfetch <<'EOF' && chmod +x /usr/local/bin/dfetch
#!/bin/bash
set -u
CTR=/var/log/dfetch.counter
ST=/var/log/dfetch.state
mkdir -p /var/log
n=$(cat "$CTR" 2>/dev/null || echo 0); n=$((n + 1)); echo "$n" > "$CTR"

region=""; token=""; release=0; out=""
for a in "$@"; do
  case "$a" in
    --region=*) region="${a#*=}" ;;
    --token=*)  token="${a#*=}" ;;
    --release)  release=1 ;;
    --*)        ;;
    *)          out="$a" ;;
  esac
done

if [ "$release" = "1" ]; then
  echo "released" > "$ST"
  echo "dfetch: lock released" >&2
  exit 0
fi
if [ -z "$region" ]; then
  echo "dfetch: error: --region is required" >&2
  exit 2
fi
if [ "$region" != "eu-west" ] && [ "$region" != "us-east" ]; then
  echo "dfetch: error: region '$region' is not provisioned; provisioned regions: eu-west, us-east" >&2
  exit 2
fi
if [ -z "$token" ]; then
  echo "dfetch: error: 401 unauthorized; a session token is provisioned at /app/.dfetch_token" >&2
  exit 3
fi
CORRECT="$(cat /app/.dfetch_token 2>/dev/null || true)"
if [ "$token" != "$CORRECT" ]; then
  echo "dfetch: error: 401 unauthorized; supplied token is not valid" >&2
  exit 3
fi
if [ "$(cat "$ST" 2>/dev/null || true)" != "released" ]; then
  echo "dfetch: error: a previous run left a stale lock; clear it once with: dfetch --release" >&2
  exit 4
fi
if [ -z "$out" ]; then
  echo "dfetch: error: no output path given" >&2
  exit 5
fi
# The payload is DERIVED from the session token at emit time, not stored as a
# literal — so grepping this script reveals the mechanism but NOT the answer
# (no single file-read yields the payload; you need the token too, and the only
# documented way to the token is the 401-error recovery step). Closes the
# plaintext-grep shortcut that failed the KILL test. (Residual: a root agent can
# still read the token + replicate this hash — see backlog rollout spec; the
# airtight fix needs a privilege boundary / stateful sidecar.)
echo "PAYLOAD: $(printf '%s' "$CORRECT" | sha256sum | cut -c1-11)" > "$out"
echo "dfetch: success" >&2
exit 0
EOF

# Session token the agent must discover (from the 401 error) and supply.
RUN printf 'sk-fetch-9f3a2b71\n' > /app/.dfetch_token \
    && mkdir -p /var/log && printf '0\n' > /var/log/dfetch.counter

FROM harbor-agents-rich:latest
WORKDIR /app

# Adaptive-recovery tool: `dfetch` fails with DIFFERENT, actionable errors until
# the agent reads each one and supplies the specific correction. Unlike a
# deterministic fail-N/succeed tool (where a blind retry loop is optimal), this
# REQUIRES diagnose-and-adapt: a fixed retry of the same command stalls on the
# first unmet requirement forever. Requirements (checked each call, first unmet
# reported):
#   1. --region=<id> must be present
#   2. region must be provisioned (the error says "not provisioned" but NOT which
#      regions are — the agent must discover them from /app/dfetch.conf)
#   3. --token=<t> must match the session token (the 401 names the --token flag
#      but NOT where the token lives — also discovered from /app/dfetch.conf)
#   4. a stale lock must be cleared once via `dfetch --release`
#
# The success PAYLOAD is a RANDOM nonce generated at success time (8 bytes from
# /dev/urandom), NOT derived from any static input. There is therefore NO
# offline / file-read path to the answer: the only way to obtain the nonce is to
# drive dfetch through the error sequence to a successful call. dfetch records the
# emitted nonce + a success marker in /var/log/dfetch.state so the verifier can
# grade against the value dfetch ACTUALLY emitted. Every invocation (incl.
# --release) increments /var/log/dfetch.counter for the efficiency band.
# (Residual: the agent runs as root and could write a forged success marker +
# nonce directly to /var/log/dfetch.state, but it never sees the grader — which
# is uploaded post-agent — so it cannot know the state format; honest tool use is
# the strictly-shorter path. See backlog/2026-06-10-core-eleven-remediation.md D3.)
RUN cat > /usr/local/bin/dfetch <<'EOF' && chmod +x /usr/local/bin/dfetch
#!/bin/bash
set -u
CTR=/var/log/dfetch.counter
ST=/var/log/dfetch.state
LOCK=/var/log/dfetch.lock
CONF=/app/dfetch.conf
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
  echo "released" > "$LOCK"
  echo "dfetch: lock released" >&2
  exit 0
fi
if [ -z "$region" ]; then
  echo "dfetch: error: --region is required" >&2
  exit 2
fi
if ! grep -qx "provisioned_region=${region}" "$CONF" 2>/dev/null; then
  echo "dfetch: error: region '$region' is not provisioned" >&2
  exit 2
fi
if [ -z "$token" ]; then
  echo "dfetch: error: 401 unauthorized; provide a valid session token via --token" >&2
  exit 3
fi
VALID_TOKEN="$(sed -n 's/^session_token=//p' "$CONF" 2>/dev/null | head -1)"
if [ "$token" != "$VALID_TOKEN" ]; then
  echo "dfetch: error: 401 unauthorized; supplied session token is not valid" >&2
  exit 3
fi
if [ "$(cat "$LOCK" 2>/dev/null || true)" != "released" ]; then
  echo "dfetch: error: a stale lock from a previous run is held; release it before fetching" >&2
  exit 4
fi
if [ -z "$out" ]; then
  echo "dfetch: error: no output path given" >&2
  exit 5
fi
# Random nonce, generated fresh on every successful fetch. Uncomputable offline.
nonce="$(head -c8 /dev/urandom | od -An -tx1 | tr -d ' \n')"
printf 'STATUS=success\nNONCE=%s\n' "$nonce" > "$ST"
echo "PAYLOAD: $nonce" > "$out"
echo "dfetch: success" >&2
exit 0
EOF

# Provisioning manifest the agent DISCOVERS by exploring /app (the errors point at
# the flags but never at these values). Single source of truth: dfetch reads the
# provisioned regions + the session token from here.
RUN cat > /app/dfetch.conf <<'EOF'
# dfetch provisioning manifest
# Regions provisioned for this account (any other region is rejected):
provisioned_region=eu-west
provisioned_region=us-east
# Session token required for authenticated fetches:
session_token=sk-fetch-9f3a2b71
EOF

RUN mkdir -p /var/log && printf '0\n' > /var/log/dfetch.counter

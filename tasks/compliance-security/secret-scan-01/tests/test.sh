#!/bin/bash
# Deterministic graded verifier for secret-scan-01 (medium).
#
# The repo under /app/repo/ contains FOUR files with real hardcoded secrets and
# THREE clean files (one of which — example_settings.py — is a decoy full of
# placeholder values that LOOK like secrets but are not). We grade precision +
# recall over the set of secret-bearing files.
#
#   Secret-bearing (recall, total=4):
#     auth.py            (payments API key + JWT session token)
#     config.py          (AWS access key id + secret access key)
#     db.py              (postgres connection string with embedded password)
#     deploy/id_rsa      (RSA private key)
#   Clean / decoy (precision — flagging any of these is a false positive):
#     utils.py           (no secret)
#     README.md          (no secret)
#     example_settings.py (DECOY: placeholders only — <your-api-key-here>, etc.)
#
#   found  = # of the 4 secret files correctly listed
#   fp     = # of clean/decoy files wrongly listed (max 3)
#   reward = round(max(0, found - fp) / 4, 4)
#   correctness = 1 iff found == 4 AND fp == 0
#
# reward.json MUST stay a FLAT dict of scalar numbers (FOOTGUNS #38).
set -u
mkdir -p /logs/verifier

if [ ! -f /app/findings.txt ]; then
    cat > /logs/verifier/reward.json <<EOF
{"reward": 0, "correctness": 0, "instruction_following": 0, "found": 0, "total_secrets": 4, "fp": 0}
EOF
    exit 0
fi
instruction_following=1

# Normalize: trim, drop blanks, strip a leading repo/ or ./ prefix, sort -u.
normalized="$(sed 's/^[[:space:]]*//;s/[[:space:]]*$//' /app/findings.txt \
    | grep -v '^$' \
    | sed 's|^/app/repo/||;s|^repo/||;s|^\./||' \
    | sort -u)"

printf 'normalized findings:\n%s\n' "$normalized" > /logs/verifier/check.log

# Count true positives and false positives line-by-line.
read found fp < <(SECRETS_LINES="$normalized" python3 - <<'PY'
import os
secret = {"auth.py", "config.py", "db.py", "deploy/id_rsa"}
clean  = {"utils.py", "README.md", "example_settings.py"}
lines = [l.strip() for l in os.environ.get("SECRETS_LINES", "").splitlines() if l.strip()]
seen = set(lines)
found = len(secret & seen)
fp = len(clean & seen)
print(found, fp)
PY
)

read reward correctness < <(python3 -c "
found=$found; fp=$fp; total=4
net=max(0, found - fp)
print(round(net/total, 4), 1 if (found==total and fp==0) else 0)
")

cat > /logs/verifier/reward.json <<EOF
{"reward": ${reward}, "correctness": ${correctness}, "instruction_following": ${instruction_following}, "found": ${found}, "total_secrets": 4, "fp": ${fp}}
EOF

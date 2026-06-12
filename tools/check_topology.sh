#!/bin/sh
# check_topology.sh — regression gate: no internal topology in tracked files.
#
# harbor-tasks is a PUBLIC repo. Real infrastructure coordinates (home-dir paths,
# internal hostnames/IPs, Infisical ids, machine/host nicknames) live only in the
# gitignored configs/local.env + infra/ + agent-status.html. This gate greps the
# TRACKED tree for those SHAPES and exits non-zero on any hit, so a leak can't
# silently re-enter (stage new files first; scratch in the working tree is not
# scanned). Mirrors the `FROM harbor-agents-rich` CI check.
# See backlog/2026-06-12-topology-scrub.md and FOOTGUNS.md.
#
# Intended placeholders (<repo>, <run-host>, <dev-host>, <memory-host>,
# <memory-net>, <prod-group>, <storage-host>, <user>, <infisical-project-id>, and
# the literal "LAN-IP") match none of the shapes, so they pass cleanly. Generic
# container/example home dirs (/home/user, /home/agent, ...) are allow-listed.
#
# NOTE: host nicknames + the real subnet are obfuscated with single-char classes
# (e.g. t[h]ringle) so this gate never flags its OWN source. Do the same for any
# pattern you add. No broad IP check: synthetic private-range IPs are legitimate
# ops-debugging task fixtures.
set -eu

REPO=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

# Token SHAPES (grep -Ei). Self-describing; carry no sensitive literals.
SHAPES='/home/[a-z]|[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}|[A-Za-z0-9_-]+\.l[a]n|10\.0\.1[0]\.[0-9]'
# Internal host/machine nicknames (obfuscated).
NICKS='t[h]ringle|l[a]ndon|w[i]ley|p[i]nkleberry|j[u]liet|y[u]i|a[k]ane|c[r]umbleton'
# Generic /home/* that is NOT a username leak (container workdirs + upstream doc
# examples), allow-listed so it doesn't trip the /home/ shape.
ALLOW='/home/(user|users|agent|shared|myuser|node|root|<)'

# Scans TRACKED files (what the public repo actually ships). Working-tree scratch
# (commit messages, scratch scripts) is intentionally NOT scanned — stage first.
hits=$(git -C "$REPO" grep -nEi "$SHAPES|$NICKS" -- . \
        ':!tools/check_topology.sh' ':!backlog/2026-06-12-topology-scrub.md' 2>/dev/null \
        | grep -vEi "$ALLOW" || true)

if [ -n "$hits" ]; then
    echo "check_topology: FAIL — internal topology in tracked files (scrub before commit):" >&2
    printf '%s\n' "$hits" >&2
    exit 1
fi
echo "check_topology: OK — no internal topology tokens in tracked files."

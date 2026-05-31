#!/usr/bin/env bash
# tau3-bench agent run: openclaw + hermes against the airline slice.
#
# Spec: backlog/2026-05-28-tau3-bench-integration.md
# Config: configs/tau3-agent-run.yaml
#
# Per the spec's footgun: OPENAI_API_KEY/OPENAI_BASE_URL/TAU2_* MUST be in the
# HARBOR PROCESS env (not just container env) because task.toml resolves
# ${OPENAI_API_KEY} at config-load time. This wrapper sets them before calling
# `harbor run`.
#
# Usage: source ~/.config/infisical/infisical-identity.env; tools/run_tau3.sh

set -euo pipefail

REPO="${REPO:-<repo>}"
HARBOR="${HARBOR:-/tmp/harbor}"
CONFIG="${REPO}/configs/tau3-agent-run.yaml"
JOB_NAME="${JOB_NAME:-tau3-agentrun-$(date +%Y-%m-%d__%H-%M-%S)}"

SITE_URL="${INFISICAL_SITE_URL:-http://internal-host:8380}"
PROJECT_ID="${INFISICAL_PROJECT_ID:-INFISICAL_PROJECT_ID}"

: "${INFISICAL_CLIENT_ID:?set INFISICAL_CLIENT_ID via ~/.config/infisical/infisical-identity.env}"
: "${INFISICAL_CLIENT_SECRET:?set INFISICAL_CLIENT_SECRET via ~/.config/infisical/infisical-identity.env}"

TOK_TMP="$(mktemp -t itok.XXXXXX)"
chmod 600 "$TOK_TMP"
trap 'rm -f "$TOK_TMP"' EXIT
infisical login \
    --method=universal-auth \
    --client-id="$INFISICAL_CLIENT_ID" \
    --client-secret="$INFISICAL_CLIENT_SECRET" \
    --domain="$SITE_URL" \
    --plain --silent >"$TOK_TMP" 2>/dev/null
export INFISICAL_TOKEN="$(tr -d '\r\n' < "$TOK_TMP")"
export INFISICAL_SITE_URL="$SITE_URL"
export PATH="${HARBOR}/.venv/bin:${PATH}"

# Inject secrets, remap OPENROUTER_API_KEY → OPENAI_API_KEY for tau2,
# then exec harbor run.
exec infisical run \
    --domain="$SITE_URL" \
    --projectId="$PROJECT_ID" \
    --env=production --path=/proxy/ \
    -- bash -c '
        set -euo pipefail
        export OPENAI_API_KEY="$OPENROUTER_API_KEY"
        export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
        export TAU2_USER_MODEL="openai/gpt-5-nano"
        export TAU2_NL_ASSERTIONS_MODEL="openai/gpt-5-nano"
        cd "'"$HARBOR"'"
        harbor run -y -c "'"$CONFIG"'" --job-name "'"$JOB_NAME"'"
    '

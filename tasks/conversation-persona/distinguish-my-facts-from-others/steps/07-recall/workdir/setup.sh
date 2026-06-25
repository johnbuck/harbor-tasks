#!/bin/bash
# Mechanical no-notes gate: wipe ALL agent-writable scratch before recall, so the
# answer can only come from the harness's own memory, not a re-read. The shared
# scratch surfaces (/tmp, /var/tmp, agent $HOME, harness session stores,
# /logs/agent) are cleared by the canonical wipe sourced below; this step also
# wipes /app. Enforces the constraint that used to be a coaching instruction.
source "$(dirname "$0")/wipe_scratch.sh"
find /app -mindepth 1 -delete 2>/dev/null

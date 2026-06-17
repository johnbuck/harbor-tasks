#!/bin/bash
# Mechanical no-notes gate: wipe agent-writable SCRATCH before the recall agent
# runs so the answer can only come from in-window context, not a stashed-note
# re-read. This is an IN-WINDOW retention task, so WIPE_PRESERVE_SESSIONS=1 keeps
# the harness session stores (the cross-step conversation under test) while the
# canonical wipe sourced below still clears process scratch and $HOME caches.
WIPE_PRESERVE_SESSIONS=1
export WIPE_PRESERVE_SESSIONS
source "$(dirname "$0")/wipe_scratch.sh"
find /app -mindepth 1 -delete 2>/dev/null

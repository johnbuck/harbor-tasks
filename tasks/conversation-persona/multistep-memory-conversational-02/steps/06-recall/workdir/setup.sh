#!/bin/bash
# Mechanical no-notes gate: wipe ALL agent-writable scratch before recall so the
# recall answer can only come from the harness's external memory backend, not a
# re-read. The canonical wipe sourced below clears process scratch, $HOME caches
# and the harness session stores; this step then clears the task workspace too.
source "$(dirname "$0")/wipe_scratch.sh"
find /app -mindepth 1 -delete 2>/dev/null

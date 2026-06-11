#!/bin/bash
# Canonical shared-scratch wipe — single source of truth, copied verbatim into
# each recall/baseline step's workdir/ (Harbor uploads the whole workdir into the
# agent cwd, so this lands beside setup.sh) and sourced by that step's setup.sh
# BEFORE the graded agent runs.
#
# It removes every agent-writable SCRATCH surface so a recall answer can only come
# from the harness's own memory path, never from notes the agent stashed off
# /app: process scratch (/tmp, /var/tmp), copied agent transcripts (/logs/agent),
# the agent $HOME caches, and the harness session stores (openclaw session JSONL
# under /root/.openclaw, hermes sessions under $HERMES_HOME).
#
# It deliberately does NOT touch /app — each step decides whether to wipe (recall
# steps) or re-seed (the plan-then-revise baseline) /app itself. And it NEVER
# touches the EXTERNAL memory backends; those are network services wiped
# separately by hooks/wipe_memory_state.py and must not be reached from setup.sh.
#
# No error swallowing: each surface is wiped only if present, so an absent
# surface is a no-op rather than an error, and a real wipe failure still surfaces.
_h="${HOME:-/root}"
_hermes="${HERMES_HOME:-$_h/.hermes}"
for _d in /tmp /var/tmp /logs/agent \
          "$_h/.cache" "$_h/.local/share" "$_h/scratch" "$_h/notes" \
          "$_h/.openclaw/sessions" "$_h/.openclaw/history" \
          "$_hermes/sessions" "$_hermes/history"; do
    if [ -d "$_d" ]; then
        find "$_d" -mindepth 1 -delete 2>/dev/null
    fi
done
# Loose harness session transcripts (openclaw session JSONL, hermes session json).
rm -f "$_h"/.openclaw/*.jsonl "$_hermes"/*.json 2>/dev/null
unset _h _hermes _d

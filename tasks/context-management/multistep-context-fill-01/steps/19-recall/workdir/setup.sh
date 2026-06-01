#!/bin/bash
# CHEAT-PROOF MEMORY GATE: archive (delete) all reports + any notes the agent may
# have written, BEFORE the recall agent runs. Only the harness's own memory /
# context can now supply the answers — there is nothing left to re-read or grep.
rm -rf /app/reports /app/notes.md 2>/dev/null || true

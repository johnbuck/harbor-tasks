#!/bin/bash
# CHEAT-PROOF MEMORY GATE: wipe all source documents + any notes the agent
# may have written, BEFORE the recall agent runs. Only the harness's own
# memory backend can now supply the markers — no file to re-read or grep.
rm -rf /app/chunks /app/notes.md 2>/dev/null || true

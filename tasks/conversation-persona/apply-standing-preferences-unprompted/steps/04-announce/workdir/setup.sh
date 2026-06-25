#!/bin/bash
# Remove any notes/scratch the agent wrote earlier — the standing preferences
# must come from the harness's own memory, not a re-read file. (The trigger
# task never mentions the preferences; applying them is the proactive signal.)
rm -f /app/notes.md /app/prefs.md /app/preferences.txt /app/memory.md 2>/dev/null || true

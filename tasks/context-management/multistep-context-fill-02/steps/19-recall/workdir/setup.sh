#!/bin/bash
# CHEAT-PROOF MEMORY GATE: before the recall agent runs, remove the reports AND
# anything the agent may have written under /app, so the answer can only come
# from the harness's own memory/context, not a re-read. (No instruction tells the
# agent not to take notes; this wipe enforces it mechanically.)
rm -rf /app/reports 2>/dev/null || true
find /app -mindepth 1 -delete 2>/dev/null || true

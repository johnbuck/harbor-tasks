#!/bin/bash
# CHEAT-PROOF MEMORY GATE: before the recall agent runs, remove the records AND
# anything the agent may have written under /app, so each answer can only come
# from the harness's own in-context memory, not a re-read. No instruction tells
# the agent not to take notes; this wipe enforces it mechanically. (The corpus
# FITS the window, so this is a rot test, not an eviction test — what's measured
# is whether the harness still surfaces middle-buried, paraphrased facts.)
rm -rf /app/reports 2>/dev/null || true
find /app -mindepth 1 -delete 2>/dev/null || true

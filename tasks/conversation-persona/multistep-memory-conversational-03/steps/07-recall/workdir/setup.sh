#!/bin/bash
# Mechanical no-notes gate: remove anything the agent wrote under /app before
# recall, so the answer can only come from the harness's own memory, not a
# re-read. Enforces the constraint that used to be a coaching instruction.
find /app -mindepth 1 -delete 2>/dev/null || true

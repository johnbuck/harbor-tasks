#!/bin/bash
# Reference solution — used by the `oracle` agent to sanity-check the task.
set -e

cat > /app/answer.md <<'EOF'
The Apollo 11 mission first landed humans on the Moon in **1969**. The landing
occurred on July 20, 1969, when astronauts Neil Armstrong and Buzz Aldrin touched
down in the Sea of Tranquility.

Source: https://en.wikipedia.org/wiki/Apollo_11
EOF

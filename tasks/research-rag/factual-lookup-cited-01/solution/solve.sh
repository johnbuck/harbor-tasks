#!/bin/bash
# Reference solution — all 8 facts, each with a valid source URL in its block.
set -e

cat > /app/answer.md <<'EOF'
# Factual Lookups with Citations

1. Answer: 1969 (Apollo 11 landed humans on the Moon on July 20, 1969).
   Source: https://en.wikipedia.org/wiki/Apollo_11

2. Answer: Au is the chemical symbol for gold.
   Source: https://en.wikipedia.org/wiki/Gold

3. Answer: 206 bones in the adult human body.
   Source: https://en.wikipedia.org/wiki/Human_skeleton

4. Answer: 1989 (the Berlin Wall fell on November 9, 1989).
   Source: https://en.wikipedia.org/wiki/Berlin_Wall

5. Answer: 299,792,458 metres per second (the exact defined speed of light).
   Source: https://en.wikipedia.org/wiki/Speed_of_light

6. Answer: William Shakespeare wrote "Romeo and <prod-group>".
   Source: https://en.wikipedia.org/wiki/Romeo_and_<prod-group>

7. Answer: Mount Everest is the tallest mountain on Earth above sea level.
   Source: https://en.wikipedia.org/wiki/Mount_Everest

8. Answer: 2007 (the first iPhone was released June 29, 2007).
   Source: https://en.wikipedia.org/wiki/IPhone_(1st_generation)
EOF

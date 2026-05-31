#!/bin/bash
# Deterministic graded verifier for factual-lookup-cited-01.
#
# Eight independent factual questions, each requiring BOTH a correct answer AND a
# valid source URL (http:// or https://) in the SAME numbered block. The harness
# signal is multi-source retrieval + per-item citation discipline: a strong
# harness lands all eight facts each with its own citation; weaker scaffolding
# drops citations or facts, producing a fractional score.
#
# Scoring (graded fraction, NOT binary):
#   found   = # of items where (answer correct AND a valid URL is present in block)
#   reward  = found / 8                       (float 0..1)
#   correctness = 1 iff found == 8, else 0
#
# Per-item blocks are delimited by leading "<n>." / "<n>)" markers. The value
# regex for each item must match within that item's block AND the block must
# contain at least one http(s) URL.

set -u
mkdir -p /logs/verifier
TARGET=/app/answer.md

if [ ! -f "$TARGET" ]; then
  echo '{"reward": 0.0, "correctness": 0, "found": 0, "total": 8, "missing_answer": 1}' > /logs/verifier/reward.json
  exit 0
fi

python3 - "$TARGET" <<'PY'
import json, re, sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
low = text.lower()
if not low.strip():
    json.dump({"reward": 0.0, "correctness": 0, "found": 0, "total": 8, "empty_answer": 1},
              open("/logs/verifier/reward.json", "w"))
    sys.exit(0)

# Split into per-item blocks on leading "N." or "N)" markers (1..8).
# Anything before item 1 is discarded.
parts = re.split(r'(?m)^\s*([1-8])[\.\)]\s', text)
blocks = {}
# parts = [pre, '1', body1, '2', body2, ...]
for i in range(1, len(parts) - 1, 2):
    n = int(parts[i])
    blocks[n] = parts[i + 1].lower()

URL = re.compile(r'https?://\S+')

# (value_regex, ...) — answer is correct if ANY regex matches in the block.
checks = {
    1: [r'\b1969\b'],                                  # Apollo 11 Moon landing
    2: [r'\bau\b'],                                    # gold symbol Au
    3: [r'\b206\b'],                                   # bones in adult human body
    4: [r'\b1989\b'],                                  # Berlin Wall fell
    5: [r'299[,.\s]?792[,.\s]?458'],                   # speed of light m/s
    6: [r'shakespeare'],                               # Romeo & Juliet author
    7: [r'mount everest|everest'],                     # tallest mountain
    8: [r'\b2007\b'],                                  # first iPhone
}

per = {}
found = 0
for n in range(1, 9):
    body = blocks.get(n, "")
    val_ok = any(re.search(rx, body) for rx in checks[n])
    url_ok = bool(URL.search(body))
    ok = 1 if (val_ok and url_ok) else 0
    per[f"item{n}"] = {"value": int(val_ok), "url": int(url_ok), "ok": ok}
    found += ok

reward = round(found / 8.0, 4)
correctness = 1 if found == 8 else 0
out = {"reward": reward, "correctness": correctness, "found": found, "total": 8}
json.dump(out, open("/logs/verifier/reward.json", "w"))
print(json.dumps(out))
PY

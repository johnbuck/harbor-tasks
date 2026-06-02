#!/bin/bash
# Verifier for browser-find-fact-01.
#
# reward = 1.0 iff /app/answer.txt names the author the SITE attributes the quote
# to (Jim Henson) AND does not also name a decoy author from the same page (a
# sibling penalty: dumping every author on page 3 must not pass). Content-matched
# and format-tolerant (any phrasing of the name is fine) so a content-correct
# answer is never falsely zeroed.
#
# browser_used is a DIAGNOSTIC (reported, not folded into reward): did the harness
# actually drive its browser tool? The target page is JS-rendered, so the natural
# path is the browser; a `curl`-bypass would show no browser_* tool calls. Matched
# against BOTH harness tool-naming conventions (openclaw `browser_navigate`,
# hermes `browser_navigate` / `mcp_*`). reward stays oracle-1.0 regardless (the
# oracle isn't a browser), and this surfaces any bypass for analysis.
set -u
mkdir -p /logs/verifier

python3 - <<'PY' > /logs/verifier/reward.json
import json, os, re, glob

# --- answer correctness ---
ans = ""
try:
    ans = open("/app/answer.txt").read().lower()
except Exception:
    pass

has_correct = "henson" in ans            # surname uniquely identifies Jim Henson here
DECOYS = [
    "neruda", "emerson", "mother teresa", "teresa", "keillor", "seuss",
    "einstein", "rowling", "marley", "shakespeare", "wilde", "austen",
]
has_decoy = any(d in ans for d in DECOYS)
answer_correct = 1 if (has_correct and not has_decoy) else 0

# --- browser-use diagnostic (read the agent trajectory under /logs) ---
browser_calls = 0
patterns = re.compile(r"browser[_-]?(navigate|snapshot|click|type|scroll|get_images|vision)", re.I)
for path in glob.glob("/logs/**/*", recursive=True):
    if not os.path.isfile(path):
        continue
    try:
        with open(path, errors="ignore") as f:
            browser_calls += len(patterns.findall(f.read()))
    except Exception:
        pass

print(json.dumps({
    "reward": float(answer_correct),
    "correctness": answer_correct,
    "answer_correct": answer_correct,
    "has_correct_author": int(has_correct),
    "named_a_decoy": int(has_decoy),
    "browser_tool_calls": browser_calls,   # diagnostic only
    "browser_used": int(browser_calls > 0),
}))
PY

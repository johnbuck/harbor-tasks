#!/bin/bash
# Verifier for browser-find-fact-01.
#
# reward = 1.0 iff /app/answer.txt names the author the SITE attributes the quote
# to (Jim Henson) AND does not also name a decoy author from the same page (a
# sibling penalty: dumping every author on page 3 must not pass). Content-matched
# and format-tolerant (any phrasing of the name is fine) so a content-correct
# answer is never falsely zeroed.
#
# reward is GATED on actually using the browser: the instruction is "use your
# browser tool", and the target is JS-rendered, so a correct answer obtained
# WITHOUT the browser (from training memory — quotes.toscrape data is widely
# memorized — or a curl-bypass) does NOT count. This makes the task measure
# browser-tool USE, not recall. Browser-tool calls are matched against BOTH
# harness conventions: openclaw exposes a single tool named "browser"; hermes
# uses "browser_navigate"/"browser_snapshot"/... — matching only one would
# false-zero the other (the ctx-rot scorer trap).
#
# ORACLE CAVEAT: the oracle isn't a browser, so it gets answer_correct=1 but
# browser_used=0 -> headline reward 0. That is EXPECTED — a browser-required task
# can't be end-to-end oracle-proven (same as the sub-agent fan-out task). The
# oracle validates the answer-checking logic (answer_correct sub-field); a real
# n=1 proves the browser path.
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

# --- did the harness actually drive its browser tool? (read /logs trajectory) ---
# Match a tool-call whose name is "browser" (openclaw) OR "browser_<verb>"
# (hermes), as a JSON field ("tool"/"tool_name"/"name"/"function": "browser...").
browser_calls = 0
tool_name_pat = re.compile(
    r'"(?:tool|tool_name|name|function|toolName)"\s*:\s*"(browser(?:_[a-z]+)?)"', re.I)
verb_pat = re.compile(r"browser_(navigate|snapshot|click|type|scroll|get_images|vision)", re.I)
for path in glob.glob("/logs/**/*", recursive=True):
    if not os.path.isfile(path):
        continue
    try:
        with open(path, errors="ignore") as f:
            blob = f.read()
    except Exception:
        continue
    browser_calls += len(tool_name_pat.findall(blob))
    browser_calls += len(verb_pat.findall(blob))

browser_used = 1 if browser_calls > 0 else 0
reward = 1.0 if (answer_correct and browser_used) else 0.0

print(json.dumps({
    "reward": reward,
    "answer_present": int(bool(ans.strip())),
    "correctness": int(reward == 1.0),
    "answer_correct": answer_correct,        # oracle validates this sub-field
    "has_correct_author": int(has_correct),
    "named_a_decoy": int(has_decoy),
    "browser_tool_calls": browser_calls,
    "browser_used": browser_used,            # reward is GATED on this
}))
PY

# S4 crash guard: if the grader above crashed before emitting a parseable
# reward.json, write a flat numeric fallback so Harbor scores 0 rather than
# silently DROPPING the trial (FOOTGUNS #2).
[ -s /logs/verifier/reward.json ] || echo '{"reward":0.0}' > /logs/verifier/reward.json

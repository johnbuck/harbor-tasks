#!/bin/bash
# Stale-memory vs ground-truth probe. Across earlier turns the agent stored
# cache_ttl_seconds=45; setup.sh then silently changed the file to 275. The
# question asks for the CURRENT value.
#   275 present  -> read ground truth (correct)         reward 1.0
#   45  present  -> answered from STALE memory          reward 0.0
#   neither      -> hallucination / wrong number        reward 0.0
# Diagnostic flags distinguish stale-memory failures from hallucinations.
mkdir -p /logs/verifier
python3 - <<'PY' > /logs/verifier/reward.json
import json, re
try:
    ans = open("/app/answer.txt").read()
except Exception:
    print(json.dumps({"reward":0.0,"correctness":0,"answered_current":0,
                      "stale_memory":0,"hallucination":1,"file_present":0}))
    raise SystemExit
nums = re.findall(r"\d+", ans)
has_current = "275" in nums      # ground-truth value after the silent change
has_stale   = "45"  in nums      # value the agent memorized earlier
if has_current:
    reward, status = 1.0, dict(answered_current=1, stale_memory=0, hallucination=0)
elif has_stale:
    reward, status = 0.0, dict(answered_current=0, stale_memory=1, hallucination=0)
else:
    reward, status = 0.0, dict(answered_current=0, stale_memory=0, hallucination=1)
out = {"reward": reward, "correctness": 1 if reward == 1.0 else 0,
       "file_present": 1, **status}
print(json.dumps(out))
PY

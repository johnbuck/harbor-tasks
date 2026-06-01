#!/bin/bash
# Step-2 verifier (intermediate). Agent's pytest suite must pass AND a hidden
# behavioral probe confirms the suffix-aware truncate + whitespace word_count.
mkdir -p /logs/verifier

python3 - <<'PY'
import json, subprocess, sys
sys.path.insert(0, "/app")

ok = True
rc = subprocess.run(["python", "-m", "pytest", "tests/test_textkit.py", "-q"],
                    cwd="/app", capture_output=True).returncode
if rc != 0:
    ok = False

try:
    import textkit as t
    if t.slugify("Hello, World!") != "hello-world": ok = False
    if t.slugify("") != "": ok = False
    if t.truncate("hello world", 8) != "hello...": ok = False   # suffix-aware
    if t.truncate("hi", 8) != "hi": ok = False                  # short stays intact
    if t.word_count("  the  quick brown   fox ") != 4: ok = False
    if t.word_count("") != 0: ok = False
except Exception:
    ok = False

reward = 1 if ok else 0
json.dump({"reward": reward, "correctness": reward},
          open("/logs/verifier/reward.json", "w"))
print(json.dumps({"reward": reward, "correctness": reward}))
PY

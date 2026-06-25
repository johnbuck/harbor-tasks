#!/bin/bash
# Step-2 verifier (intermediate). Agent's pytest suite must pass AND a hidden
# behavioral probe confirms f_to_c, round_temp, and the absolute-zero guards.
mkdir -p /logs/verifier

python3 - <<'PY'
import json, subprocess, sys
sys.path.insert(0, "/app")

ok = True
rc = subprocess.run(["python", "-m", "pytest", "tests/test_tempconv.py", "-q"],
                    cwd="/app", capture_output=True).returncode
if rc != 0:
    ok = False

try:
    import tempconv as tc
    if tc.c_to_f(100) != 212.0: ok = False
    if tc.c_to_f(0) != 32.0: ok = False
    if tc.f_to_c(32) != 0.0: ok = False
    if tc.round_temp(98.599) != 98.6: ok = False
    for bad, fn in ((-300, tc.c_to_f), (-500, tc.f_to_c)):
        try:
            fn(bad); ok = False  # should raise
        except ValueError:
            pass
except Exception:
    ok = False

reward = 1 if ok else 0
json.dump({"reward": reward, "correctness": reward},
          open("/logs/verifier/reward.json", "w"))
print(json.dumps({"reward": reward, "correctness": reward}))
PY

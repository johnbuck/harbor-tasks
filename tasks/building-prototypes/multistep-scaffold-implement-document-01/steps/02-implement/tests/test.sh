#!/bin/bash
# Step-2 verifier (intermediate). The agent's own pytest suite must pass AND a
# hidden behavioral probe must confirm divide() is float + guards zero.
mkdir -p /logs/verifier

python3 - <<'PY'
import json, subprocess, sys
sys.path.insert(0, "/app")

ok = True

rc = subprocess.run(["python", "-m", "pytest", "tests/test_calc.py", "-q"],
                    cwd="/app", capture_output=True).returncode
if rc != 0:
    ok = False

try:
    import calc
    if calc.add(2, 3) != 5: ok = False
    if calc.sub(5, 2) != 3: ok = False
    if calc.mul(4, 3) != 12: ok = False
    r = calc.divide(10, 2)
    if r != 5.0 or not isinstance(r, float): ok = False
    try:
        calc.divide(1, 0)
        ok = False  # should have raised
    except ZeroDivisionError:
        pass
except Exception:
    ok = False

reward = 1 if ok else 0
json.dump({"reward": reward, "correctness": reward},
          open("/logs/verifier/reward.json", "w"))
print(json.dumps({"reward": reward, "correctness": reward}))
PY

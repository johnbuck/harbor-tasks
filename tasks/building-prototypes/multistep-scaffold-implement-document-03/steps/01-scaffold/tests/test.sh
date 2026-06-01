#!/bin/bash
# Step-1 verifier (intermediate — only the FINAL step counts under
# multi_step_reward_strategy="final"). Confirms the three stubs + test suite.
mkdir -p /logs/verifier

python3 - <<'PY'
import json, re, sys
from pathlib import Path

ok = True
pkg = Path("/app/tempconv/__init__.py")
tst = Path("/app/tests/test_tempconv.py")

if not pkg.exists() or not tst.exists():
    ok = False
else:
    src = pkg.read_text()
    if not all(re.search(rf"def {name}\s*\(", src) for name in ("c_to_f", "f_to_c", "round_temp")):
        ok = False
    sys.path.insert(0, "/app")
    try:
        import tempconv
        for name in ("c_to_f", "f_to_c", "round_temp"):
            if not callable(getattr(tempconv, name, None)):
                ok = False
    except Exception:
        ok = False
    if len(re.findall(r"(?m)^\s*def test_", tst.read_text())) < 5:
        ok = False

reward = 1 if ok else 0
json.dump({"reward": reward, "correctness": reward},
          open("/logs/verifier/reward.json", "w"))
print(json.dumps({"reward": reward, "correctness": reward}))
PY

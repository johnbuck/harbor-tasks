#!/bin/bash
# Step-1 verifier (intermediate — only the FINAL step counts under
# multi_step_reward_strategy="final"). Confirms the four stubs + test suite
# scaffold is in place and importable.
mkdir -p /logs/verifier

python3 - <<'PY'
import json, re, importlib, sys
from pathlib import Path

ok = True
pkg = Path("/app/calc/__init__.py")
tst = Path("/app/tests/test_calc.py")

if not pkg.exists() or not tst.exists():
    ok = False
else:
    src = pkg.read_text()
    # All four function names defined.
    if not all(re.search(rf"def {name}\s*\(", src) for name in ("add", "sub", "mul", "divide")):
        ok = False
    # Importable.
    sys.path.insert(0, "/app")
    try:
        import calc  # noqa
        for name in ("add", "sub", "mul", "divide"):
            if not callable(getattr(calc, name, None)):
                ok = False
    except Exception:
        ok = False
    # Test file references all four and has >=5 test functions.
    t = tst.read_text()
    if len(re.findall(r"(?m)^\s*def test_", t)) < 5:
        ok = False

reward = 1 if ok else 0
json.dump({"reward": reward, "correctness": reward},
          open("/logs/verifier/reward.json", "w"))
print(json.dumps({"reward": reward, "correctness": reward}))
PY

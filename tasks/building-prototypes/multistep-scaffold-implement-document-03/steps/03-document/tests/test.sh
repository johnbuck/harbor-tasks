#!/bin/bash
# GRADED final verifier (multi_step_reward_strategy="final" — only this counts).
#
# 12 independent sub-checks of the built `tempconv` package + its README. The
# README is graded for DOC-MATCHING: it must document all three functions, state
# the absolute-zero ValueError, and ship a runnable example whose inline
# "# expected" comments match the code's real stdout.
#
# reward = satisfied / 12 ; correctness = 1 only if all 12 pass.
mkdir -p /logs/verifier

python3 - <<'PY'
import json, re, subprocess, sys, io, contextlib
from pathlib import Path

sys.path.insert(0, "/app")
N = 12
s = 0
log = []

def check(name, cond):
    global s
    ok = bool(cond)
    if ok: s += 1
    log.append((name, ok))
    return ok

PKG = Path("/app/tempconv/__init__.py")
TST = Path("/app/tests/test_tempconv.py")
RM = Path("/app/README.md")

# 1
check("files_present", PKG.exists() and TST.exists())

# 2: pytest passes, >=5 tests
ptests = 0; prc = 1
if TST.exists():
    ptests = len(re.findall(r"(?m)^\s*def test_", TST.read_text()))
    prc = subprocess.run(["python", "-m", "pytest", "tests/test_tempconv.py", "-q"],
                         cwd="/app", capture_output=True).returncode
check("pytest_passes_ge5", ptests >= 5 and prc == 0)

tc = None
try:
    import tempconv as _tc; tc = _tc
except Exception:
    tc = None

# 3: c_to_f
try:
    check("c_to_f", tc.c_to_f(100) == 212.0 and tc.c_to_f(0) == 32.0)
except Exception:
    check("c_to_f", False)

# 4: f_to_c
try:
    check("f_to_c", tc.f_to_c(32) == 0.0)
except Exception:
    check("f_to_c", False)

# 5: round_temp
try:
    check("round_temp", tc.round_temp(98.599) == 98.6)
except Exception:
    check("round_temp", False)

# 6: absolute-zero ValueError for both converters
abz = True
for bad, fn in ((-300, "c_to_f"), (-500, "f_to_c")):
    try:
        getattr(tc, fn)(bad)
        abz = False  # should have raised
    except ValueError:
        pass
    except Exception:
        abz = False
check("abs_zero_raises", abz)

# 7: no debug cruft
src = PKG.read_text() if PKG.exists() else ""
check("no_debug_cruft",
      not re.search(r"\b(breakpoint\(|import pdb|pdb\.set_trace|print\()", src))

# 8: README present
rm = RM.read_text() if RM.exists() else ""
check("readme_present", bool(rm.strip()))

# 9: README documents all three functions
check("readme_all_funcs",
      all(re.search(rf"\b{fn}\b", rm) for fn in ("c_to_f", "f_to_c", "round_temp")))

# 10: README documents the absolute-zero ValueError
check("readme_abs_zero",
      bool(re.search(r"ValueError", rm)) and bool(re.search(r"absolute zero", rm, re.I)))

# extract first python fence
fences = re.findall(r"```python\s*\n(.*?)```", rm, re.DOTALL)
code = fences[0] if fences else ""

# 11: example runs and prints
ran_ok = False; out = ""
if code.strip():
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(code, "<readme>", "exec"), {})
        out = buf.getvalue()
        ran_ok = bool(out.strip())
    except Exception:
        ran_ok = False
check("example_runs", ran_ok)

# 12: DOC-MATCHING — inline "# expected" comments equal printed lines, in order
doc_match = False
if ran_ok:
    printed = out.splitlines()
    expected = []
    for line in code.splitlines():
        m = re.search(r"print\(.*\)\s*#\s*(.+?)\s*$", line)
        if m:
            expected.append(m.group(1).strip())
    if len(expected) >= 3 and len(printed) >= len(expected):
        doc_match = all(printed[i].strip() == expected[i] for i in range(len(expected)))
check("doc_matches_output", doc_match)

reward = round(s / N, 4)
correctness = 1 if s == N else 0
result = {"reward": reward, "correctness": correctness, "satisfied": s, "n_checks": N}
json.dump(result, open("/logs/verifier/reward.json", "w"))
print(json.dumps(result))
for name, ok in log:
    print(f"  [{'x' if ok else ' '}] {name}")
PY

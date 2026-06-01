#!/bin/bash
# GRADED final verifier (multi_step_reward_strategy="final" — only this counts).
#
# 12 independent sub-checks of the built `calc` package + its README. The README
# is graded for DOC-MATCHING: it must document all four functions, state the
# divide float + ZeroDivisionError contract, and ship a runnable example whose
# inline "# expected" comments match what the code actually prints.
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
    if ok:
        s += 1
    log.append((name, ok))
    return ok

PKG = Path("/app/calc/__init__.py")
TST = Path("/app/tests/test_calc.py")
RM = Path("/app/README.md")

# 1: required files present
check("files_present", PKG.exists() and TST.exists())

# 2: agent pytest suite passes with >=5 tests
ptests = 0
prc = 1
if TST.exists():
    ptests = len(re.findall(r"(?m)^\s*def test_", TST.read_text()))
    prc = subprocess.run(["python", "-m", "pytest", "tests/test_calc.py", "-q"],
                         cwd="/app", capture_output=True).returncode
check("pytest_passes_ge5", ptests >= 5 and prc == 0)

# import the package for behavioral probes
calc = None
try:
    import calc as _c
    calc = _c
except Exception:
    calc = None

# 3: add/sub/mul correct
try:
    check("add_sub_mul", calc.add(2,3)==5 and calc.sub(5,2)==3 and calc.mul(4,3)==12)
except Exception:
    check("add_sub_mul", False)

# 4: divide returns float 5.0
try:
    r = calc.divide(10,2)
    check("divide_float", r == 5.0 and isinstance(r, float))
except Exception:
    check("divide_float", False)

# 5: divide(1,0) raises ZeroDivisionError
try:
    calc.divide(1,0)
    check("divide_zero_raises", False)
except ZeroDivisionError:
    check("divide_zero_raises", True)
except Exception:
    check("divide_zero_raises", False)

# 6: no debug cruft in the package source
src = PKG.read_text() if PKG.exists() else ""
check("no_debug_cruft",
      not re.search(r"\b(breakpoint\(|import pdb|pdb\.set_trace|print\()", src))

# 7: README exists & non-empty
rm = RM.read_text() if RM.exists() else ""
check("readme_present", bool(rm.strip()))

# 8: README documents all four function names
check("readme_all_funcs",
      all(re.search(rf"\b{fn}\b", rm) for fn in ("add", "sub", "mul", "divide")))

# 9: README states divide returns a float
check("readme_divide_float",
      bool(re.search(r"divide", rm)) and bool(re.search(r"float", rm, re.I)))

# 10: README documents the divide-by-zero / ZeroDivisionError behavior
check("readme_zero_div",
      bool(re.search(r"ZeroDivisionError", rm) or re.search(r"divi.*by.*zero", rm, re.I)))

# Extract the first python-tagged code fence
fences = re.findall(r"```python\s*\n(.*?)```", rm, re.DOTALL)
code = fences[0] if fences else ""

# 11: the usage example runs without error and prints something
ran_ok = False
out = ""
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

# 12: DOC-MATCHING — inline "# expected" comments match actual printed lines.
#     Pair each print(...) line that has a trailing "# <expected>" comment with
#     the corresponding stdout line and require equality.
doc_match = False
if ran_ok:
    printed = [l for l in out.splitlines()]
    expected = []
    for line in code.splitlines():
        m = re.search(r"print\(.*\)\s*#\s*(.+?)\s*$", line)
        if m:
            expected.append(m.group(1).strip())
    # Need at least 3 commented prints to claim doc-matching, and each must
    # appear (in order) among the printed output lines.
    if len(expected) >= 3 and len(printed) >= len(expected):
        doc_match = all(
            printed[i].strip() == expected[i] for i in range(len(expected))
        )
check("doc_matches_output", doc_match)

reward = round(s / N, 4)
correctness = 1 if s == N else 0
result = {"reward": reward, "correctness": correctness, "satisfied": s, "n_checks": N}
json.dump(result, open("/logs/verifier/reward.json", "w"))
print(json.dumps(result))
for name, ok in log:
    print(f"  [{'x' if ok else ' '}] {name}")
PY

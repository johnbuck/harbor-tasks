#!/bin/bash
# GRADED final verifier (multi_step_reward_strategy="final" — only this counts).
#
# 12 independent sub-checks of the built `textkit` package + its README. The
# README is graded for DOC-MATCHING: it must document all three functions, state
# the suffix-aware truncate length rule, and ship a runnable example whose inline
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

PKG = Path("/app/textkit/__init__.py")
TST = Path("/app/tests/test_textkit.py")
RM = Path("/app/README.md")

# 1
check("files_present", PKG.exists() and TST.exists())

# 2: pytest passes, >=5 tests
ptests = 0; prc = 1
if TST.exists():
    ptests = len(re.findall(r"(?m)^\s*def test_", TST.read_text()))
    prc = subprocess.run(["python", "-m", "pytest", "tests/test_textkit.py", "-q"],
                         cwd="/app", capture_output=True).returncode
check("pytest_passes_ge5", ptests >= 5 and prc == 0)

t = None
try:
    import textkit as _t; t = _t
except Exception:
    t = None

# 3: slugify (incl empty)
try:
    check("slugify", t.slugify("Hello, World!") == "hello-world" and t.slugify("") == "")
except Exception:
    check("slugify", False)

# 4: truncate suffix-aware long case
try:
    check("truncate_long", t.truncate("hello world", 8) == "hello...")
except Exception:
    check("truncate_long", False)

# 5: truncate short returns intact
try:
    check("truncate_short", t.truncate("hi", 8) == "hi")
except Exception:
    check("truncate_short", False)

# 6: word_count (incl empty)
try:
    check("word_count", t.word_count("  the  quick brown   fox ") == 4 and t.word_count("") == 0)
except Exception:
    check("word_count", False)

# 7: no debug cruft in package
src = PKG.read_text() if PKG.exists() else ""
check("no_debug_cruft",
      not re.search(r"\b(breakpoint\(|import pdb|pdb\.set_trace|print\()", src))

# 8: README present
rm = RM.read_text() if RM.exists() else ""
check("readme_present", bool(rm.strip()))

# 9: README documents all three functions
check("readme_all_funcs",
      all(re.search(rf"\b{fn}\b", rm) for fn in ("slugify", "truncate", "word_count")))

# 10: README documents the suffix-aware length behaviour of truncate. Accept any
# phrasing that ties the suffix to the length limit (don't require a leaked exact
# phrase) — e.g. "...including the suffix", "the suffix counts toward the limit",
# "result length (with the suffix) is at most n".
check("readme_truncate_rule",
      bool(re.search(r"truncate", rm)) and
      bool(re.search(r"suffix", rm, re.I)) and
      bool(re.search(r"length|character|limit|at most|within|count", rm, re.I)))

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

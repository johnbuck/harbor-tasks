#!/bin/bash
# GRADED final verifier (multi_step_reward_strategy="final" — only this counts).
#
# 12 independent sub-checks of /app/csv2json.py behavior + the agent's pytest
# suite. reward = matched / 12; correctness=1 only if all 12 pass. A naive
# DictReader+dumps implementation passes only the base/JSON-validity checks and
# drops the --int/--filter/--sort/empty checks, yielding a clear partial reward.
set -u
mkdir -p /logs/verifier

python3 - <<'PY'
import json, subprocess, tempfile, os, re

BIN = "/app/csv2json.py"
s = 0
N = 12

def run(csv, *flags):
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        f.write(csv); path = f.name
    try:
        r = subprocess.run(["python", BIN, path, *flags],
                           capture_output=True, text=True)
        return r
    finally:
        os.unlink(path)

def jrun(csv, *flags):
    r = run(csv, *flags)
    return json.loads(r.stdout.strip())

CSV = "name,age,city\nAlice,30,London\nBob,25,Paris\nCleo,42,Paris\nDan,19,Berlin\n"

if os.path.exists(BIN):
    # 1: base conversion -> string values
    try:
        d = jrun(CSV)
        if d[0] == {"name":"Alice","age":"30","city":"London"} and len(d)==4:
            s += 1
    except Exception: pass

    # 2: --int age value correct
    try:
        d = jrun(CSV, "--int", "age")
        if d[0]["age"] == 30 and d[1]["age"] == 25:
            s += 1
    except Exception: pass

    # 3: --int age TYPE is int (not str)
    try:
        d = jrun(CSV, "--int", "age")
        if all(isinstance(r["age"], int) for r in d):
            s += 1
    except Exception: pass

    # 4: multiple --int columns
    try:
        d = jrun("a,b,c\n1,2,x\n3,4,y\n", "--int", "a", "--int", "b")
        if d == [{"a":1,"b":2,"c":"x"},{"a":3,"b":4,"c":"y"}]:
            s += 1
    except Exception: pass

    # 5: --filter keeps matching rows only
    try:
        d = jrun(CSV, "--filter", "city=Paris")
        if [r["name"] for r in d] == ["Bob","Cleo"]:
            s += 1
    except Exception: pass

    # 6: lexicographic --sort on string column
    try:
        d = jrun(CSV, "--sort", "name")
        if [r["name"] for r in d] == ["Alice","Bob","Cleo","Dan"]:
            s += 1
    except Exception: pass

    # 7: numeric --sort on --int column (9 before 10)
    try:
        d = jrun("name,n\na,9\nb,10\nc,2\n", "--int","n","--sort","n")
        if [r["n"] for r in d] == [2,9,10]:
            s += 1
    except Exception: pass

    # 8: a NON-int --sort column with numeric-looking strings stays lexicographic
    #    (string sort: "10" < "2" < "9")
    try:
        d = jrun("name,n\na,9\nb,10\nc,2\n", "--sort","n")
        if [r["n"] for r in d] == ["10","2","9"]:
            s += 1
    except Exception: pass

    # 9: filter THEN sort composition
    try:
        d = jrun(CSV, "--filter","city=Paris","--int","age","--sort","age")
        if [r["age"] for r in d] == [25,42]:
            s += 1
    except Exception: pass

    # 10: empty (header-only) prints []
    try:
        r = run("name,age,city\n")
        if r.stdout.strip() == "[]":
            s += 1
    except Exception: pass

    # 11: output is valid JSON array under combined flags
    try:
        r = run(CSV, "--int","age","--filter","city=Paris","--sort","age")
        v = json.loads(r.stdout.strip())
        if isinstance(v, list):
            s += 1
    except Exception: pass

# 12: agent pytest suite exists (>=3 tests) and passes
tf = "/app/test_csv2json.py"
if os.path.exists(tf):
    ntests = len(re.findall(r"(?m)^\s*def test_", open(tf).read()))
    if ntests >= 3:
        rc = subprocess.run(["python","-m","pytest",tf,"-q"],
                            cwd="/app", capture_output=True).returncode
        if rc == 0:
            s += 1

reward = round(s / N, 4)
correctness = 1 if s == N else 0
with open("/logs/verifier/reward.json","w") as f:
    json.dump({"reward": reward, "correctness": correctness,
               "matched": s, "n_checks": N}, f)
print(json.dumps({"reward": reward, "correctness": correctness, "matched": s, "n_checks": N}))
PY

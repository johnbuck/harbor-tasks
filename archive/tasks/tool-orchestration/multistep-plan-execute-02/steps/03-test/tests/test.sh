#!/bin/bash
# GRADED final verifier (multi_step_reward_strategy="final" — only this counts).
#
# 12 independent sub-checks of /app/wordfreq.py behavior + the agent's pytest
# suite. reward = matched / 12; correctness=1 only if all 12 pass. The naive
# split()+Counter.most_common implementation fails punctuation stripping, the
# deterministic alphabetical tie-break, and all four flags, dropping a clear
# fraction of the criteria.
set -u
mkdir -p /logs/verifier

python3 - <<'PY'
import subprocess, tempfile, os, re, json

BIN = "/app/wordfreq.py"
s = 0
N = 12

def run(text, *flags):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(text); path = f.name
    try:
        return subprocess.run(["python", BIN, path, *flags],
                              capture_output=True, text=True)
    finally:
        os.unlink(path)

def out(text, *flags):
    return run(text, *flags).stdout.strip()

if os.path.exists(BIN):
    # 1: clear winner
    if out("apple apple apple banana cherry") == "apple": s += 1

    # 2: punctuation stripping ("dog," == "dog")
    if out("dog, dog. dog! cat fish") == "dog": s += 1

    # 3: deterministic alphabetical tie-break (dog & fox tie -> dog)
    if out("fox fox dog dog") == "dog": s += 1

    # 4: lowercase normalization
    if out("Dog dog DOG cat") == "dog": s += 1

    # 5: internal apostrophe kept ("don't" not stripped to "dont"/"don")
    if out("don't don't don't cat") == "don't": s += 1

    # 6: --top format ("word count" lines, count desc)
    if out("a a a b b c", "--top", "2").splitlines() == ["a 3", "b 2"]: s += 1

    # 7: --top alphabetical tie among equal counts
    if out("b b a a c", "--top", "3").splitlines() == ["a 2", "b 2", "c 1"]: s += 1

    # 8: --stopwords excludes words
    if out("the the the cat cat dog", "--stopwords", "the") == "cat": s += 1

    # 9: --min-len excludes short tokens
    #    "ox" (len 2) most frequent but excluded; "cat" wins at min-len 3
    if out("ox ox ox cat cat dog", "--min-len", "3") == "cat": s += 1

    # 10: combined --stopwords + --min-len
    if out("the the cat cat ox ox ox dog", "--stopwords", "the",
           "--min-len", "3") == "cat": s += 1

    # 11: lone-punctuation token is dropped (doesn't crash / doesn't win)
    r = run("--- --- cat cat dog")
    if r.returncode == 0 and r.stdout.strip() == "cat": s += 1

# 12: agent pytest suite exists (>=3 tests) and passes
tf = "/app/test_wordfreq.py"
if os.path.exists(tf):
    ntests = len(re.findall(r"(?m)^\s*def test_", open(tf).read()))
    if ntests >= 3:
        rc = subprocess.run(["python", "-m", "pytest", tf, "-q"],
                            cwd="/app", capture_output=True).returncode
        if rc == 0:
            s += 1

reward = round(s / N, 4)
correctness = 1 if s == N else 0
with open("/logs/verifier/reward.json", "w") as f:
    json.dump({"reward": reward, "correctness": correctness,
               "matched": s, "n_checks": N}, f)
print(json.dumps({"reward": reward, "correctness": correctness, "matched": s, "n_checks": N}))
PY

#!/bin/bash
# GRADED verifier for /app/linecount.py (a wc-style line/char counter).
#
# 12 independent sub-checks: single-file line count, empty file, the
# missing-trailing-newline wrinkle, char (-c) mode, multi-file per-file + total
# format, stdin mode, and missing-file error handling (stderr + non-zero exit,
# no traceback). reward = satisfied / 12 ; correctness = 1 only if all 12 pass.
mkdir -p /logs/verifier

python3 - <<'PY'
import json, subprocess, os, tempfile
from pathlib import Path

BIN = "/app/linecount.py"
N = 12
s = 0
log = []

def check(name, cond):
    global s
    ok = bool(cond)
    if ok: s += 1
    log.append((name, ok))
    return ok

def write(content_bytes):
    fd, path = tempfile.mkstemp()
    with os.fdopen(fd, "wb") as f:
        f.write(content_bytes)
    return path

def run(args, stdin_bytes=None):
    return subprocess.run(["python", BIN, *args],
                          input=stdin_bytes,
                          capture_output=True)

# 1: file present
check("file_present", os.path.exists(BIN))

if os.path.exists(BIN):
    seven = write(b"line1\nline2\nline3\nline4\nline5\nline6\nline7\n")
    empty = write(b"")
    no_nl = write(b"a\nb")        # 2 lines, no trailing newline
    with_nl = write(b"a\nb\n")    # 2 lines, trailing newline
    abc = write(b"abcde")          # 5 chars, 1 line (no newline)

    # 2: single file -> "7"
    r = run([seven])
    check("single_seven", r.returncode == 0 and r.stdout.decode().strip() == "7")

    # 3: empty file -> "0"
    r = run([empty])
    check("empty_zero", r.returncode == 0 and r.stdout.decode().strip() == "0")

    # 4: missing trailing newline still counts the last line -> "2"
    r = run([no_nl])
    check("no_trailing_newline", r.stdout.decode().strip() == "2")

    # 5: trailing newline -> "2" (consistency)
    r = run([with_nl])
    check("with_trailing_newline", r.stdout.decode().strip() == "2")

    # 6: single-file output is ONLY the integer (exactly one stdout line)
    r = run([seven])
    lines = [l for l in r.stdout.decode().splitlines() if l != ""]
    check("single_output_clean", lines == ["7"])

    # 7: -c char mode
    r = run(["-c", abc])
    check("char_mode", r.returncode == 0 and r.stdout.decode().strip() == "5")

    # 8: multi-file per-file + total format (line mode)
    r = run([seven, no_nl])
    got = r.stdout.decode().strip().splitlines()
    expected = [f"7 {seven}", f"2 {no_nl}", "9 total"]
    check("multifile_format", got == expected)

    # 9: multi-file total sums correctly in -c mode
    r = run(["-c", abc, with_nl])  # 5 chars + 4 chars ("a\nb\n") = 9
    got = r.stdout.decode().strip().splitlines()
    check("multifile_total_chars",
          got and got[-1] == "9 total" and len(got) == 3)

    # 10: stdin mode (no file arg)
    r = run([], stdin_bytes=b"x\ny\nz\n")
    check("stdin_mode", r.returncode == 0 and r.stdout.decode().strip() == "3")

    # 11: missing file -> non-zero exit, error on stderr, nothing on stdout
    missing = "/tmp/does_not_exist_lc_12345.txt"
    if os.path.exists(missing):
        os.unlink(missing)
    r = run([missing])
    check("missing_file_errors",
          r.returncode != 0 and r.stdout.decode().strip() == "" and r.stderr.decode().strip() != "")

    # 12: missing file -> no Python traceback leaked
    check("no_traceback", "Traceback" not in r.stderr.decode())

reward = round(s / N, 4)
correctness = 1 if s == N else 0
result = {"reward": reward, "correctness": correctness, "satisfied": s, "n_checks": N}
json.dump(result, open("/logs/verifier/reward.json", "w"))
print(json.dumps(result))
for name, ok in log:
    print(f"  [{'x' if ok else ' '}] {name}")
PY

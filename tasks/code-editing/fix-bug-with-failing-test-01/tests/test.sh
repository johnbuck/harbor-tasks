#!/bin/bash
# Graded completeness+quality verifier for the count_words contract.
#
#   reward = 0.40 * visible_tests_fraction
#          + 0.40 * hidden_contract_fraction
#          + 0.20 * quality_fraction
#
# A naive fix (off-by-one only, `len(text.split())`) passes the visible tests
# and the basic hidden cases but FAILS the punctuation-only cases — landing
# ~0.5–0.7 instead of 1.0. The contract is fully described in instruction.md,
# so full credit is achievable; partial work scores partially. correctness=1
# only when every axis is perfect.
set -u
mkdir -p /logs/verifier
cd /app

# ---- (A) visible tests: fraction of pytest cases that pass ----
python3 -m pytest tests/test_wordcount.py -q >/logs/verifier/pytest.log 2>&1
vis_pass=$(grep -oE '[0-9]+ passed' /logs/verifier/pytest.log | grep -oE '[0-9]+' | head -1)
vis_fail=$(grep -oE '[0-9]+ failed' /logs/verifier/pytest.log | grep -oE '[0-9]+' | head -1)
vis_pass=${vis_pass:-0}; vis_fail=${vis_fail:-0}

# ---- (B) hidden contract grader: fraction of contract edge-cases passed ----
python3 /opt/canonical/hidden_grader.py > /logs/verifier/hidden.json 2>/dev/null || echo '{}' > /logs/verifier/hidden.json

# ---- (C) quality gates ----
if diff -q /app/tests/test_wordcount.py /opt/canonical/test_wordcount.py >/dev/null 2>&1; then
    test_untouched=1; else test_untouched=0; fi
if grep -qE 'def[[:space:]]+count_words[[:space:]]*\([[:space:]]*text[[:space:]]*:[[:space:]]*str[[:space:]]*\)[[:space:]]*->[[:space:]]*int' /app/wordcount.py; then
    sig_ok=1; else sig_ok=0; fi
if grep -qE '(^|[^_a-zA-Z])print[[:space:]]*\(|breakpoint[[:space:]]*\(' /app/wordcount.py; then
    no_cruft=0; else no_cruft=1; fi

python3 - "$vis_pass" "$vis_fail" "$test_untouched" "$sig_ok" "$no_cruft" <<'PY' > /logs/verifier/reward.json
import json, sys
vis_pass, vis_fail, test_untouched, sig_ok, no_cruft = map(int, sys.argv[1:6])

vis_total = vis_pass + vis_fail
visible_fraction = (vis_pass / vis_total) if vis_total else 0.0

try:
    hidden = json.load(open("/logs/verifier/hidden.json"))
except Exception:
    hidden = {}
if "_import_error" in hidden or not hidden:
    hidden_fraction = 0.0
    hidden_passed = 0; hidden_total = 0
else:
    hidden_total = len(hidden)
    hidden_passed = sum(1 for v in hidden.values() if v)
    hidden_fraction = hidden_passed / hidden_total

quality_axes = [test_untouched, sig_ok, no_cruft]
quality_fraction = sum(quality_axes) / len(quality_axes)

reward = round(0.40 * visible_fraction + 0.40 * hidden_fraction
               + 0.20 * quality_fraction, 4)
correctness = 1 if (visible_fraction == 1.0 and hidden_fraction == 1.0
                    and quality_fraction == 1.0) else 0

print(json.dumps({
    "reward": reward,
    "correctness": correctness,
    "visible_fraction": round(visible_fraction, 4),
    "hidden_fraction": round(hidden_fraction, 4),
    "quality_fraction": round(quality_fraction, 4),
    "visible_passed": vis_pass,
    "hidden_passed": hidden_passed,
    "hidden_total": hidden_total,
    "test_untouched": test_untouched,
    "signature_ok": sig_ok,
    "no_debug_cruft": no_cruft,
}))
PY

#!/bin/bash
# Graded completeness+quality verifier for the geometry-refactor contract.
#
#   reward = 0.40 * visible_tests_fraction
#          + 0.40 * hidden_contract_fraction
#          + 0.20 * quality_fraction
#
# A solution that just adds another isinstance branch in main.py (or hand-rolls
# the package export wrong) passes some visible tests but FAILS the
# package-export / empty / raise / no-dead-code hidden checks — partial reward.
# correctness=1 only when every axis is perfect.
set -u
mkdir -p /logs/verifier
cd /app

# ---- (A) visible tests ----
python3 -m pytest tests/test_geometry.py -q >/logs/verifier/pytest.log 2>&1
vis_pass=$(grep -oE '[0-9]+ passed' /logs/verifier/pytest.log | grep -oE '[0-9]+' | head -1)
vis_fail=$(grep -oE '[0-9]+ failed' /logs/verifier/pytest.log | grep -oE '[0-9]+' | head -1)
vis_pass=${vis_pass:-0}; vis_fail=${vis_fail:-0}

# ---- (B) hidden contract grader ----
python3 /opt/canonical/hidden_grader.py > /logs/verifier/hidden.json 2>/dev/null || echo '{}' > /logs/verifier/hidden.json

# ---- (C) quality gates ----
if diff -q /app/tests/test_geometry.py /opt/canonical/test_geometry.py >/dev/null 2>&1; then
    test_untouched=1; else test_untouched=0; fi
# no debug cruft in either edited file
if grep -qE '(^|[^_a-zA-Z])print[[:space:]]*\(|breakpoint[[:space:]]*\(' /app/main.py /app/geometry/shapes.py; then
    no_cruft=0; else no_cruft=1; fi
# refactored main.py should not carry a now-unused Circle/Rectangle import
if grep -qE '^\s*from[[:space:]]+geometry(\.shapes)?[[:space:]]+import|^\s*import[[:space:]]+geometry' /app/main.py; then
    no_dead_import=0; else no_dead_import=1; fi

python3 - "$vis_pass" "$vis_fail" "$test_untouched" "$no_cruft" "$no_dead_import" <<'PY' > /logs/verifier/reward.json
import json, sys
vis_pass, vis_fail, test_untouched, no_cruft, no_dead_import = map(int, sys.argv[1:6])

vis_total = vis_pass + vis_fail
visible_fraction = (vis_pass / vis_total) if vis_total else 0.0

try:
    hidden = json.load(open("/logs/verifier/hidden.json", errors="replace"))
except Exception:
    hidden = {}
if "_import_error" in hidden or not hidden:
    hidden_fraction = 0.0
    hidden_passed = 0; hidden_total = 0
else:
    hidden_total = len(hidden)
    hidden_passed = sum(1 for v in hidden.values() if v)
    hidden_fraction = hidden_passed / hidden_total

quality_axes = [test_untouched, no_cruft, no_dead_import]
quality_fraction = sum(quality_axes) / len(quality_axes)

reward = round(0.40 * visible_fraction + 0.40 * hidden_fraction
               + 0.20 * quality_fraction, 4)
correctness = 1 if (visible_fraction == 1.0 and hidden_fraction == 1.0
                    and quality_fraction == 1.0) else 0

try:
    answer_present = 1 if open("/app/main.py", errors="replace").read().strip() else 0
except OSError:
    answer_present = 0

print(json.dumps({
    "reward": reward,
    "answer_present": answer_present,
    "correctness": correctness,
    "visible_fraction": round(visible_fraction, 4),
    "hidden_fraction": round(hidden_fraction, 4),
    "quality_fraction": round(quality_fraction, 4),
    "visible_passed": vis_pass,
    "hidden_passed": hidden_passed,
    "hidden_total": hidden_total,
    "test_untouched": test_untouched,
    "no_debug_cruft": no_cruft,
    "no_dead_import": no_dead_import,
}))
PY

# S4 crash guard: if the grader above crashed before emitting a parseable
# reward.json, write a flat numeric fallback so Harbor scores 0 rather than
# silently DROPPING the trial (FOOTGUNS #2).
[ -s /logs/verifier/reward.json ] || echo '{"reward":0.0}' > /logs/verifier/reward.json

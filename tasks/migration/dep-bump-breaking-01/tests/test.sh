#!/bin/bash
# Graded verifier for dep-bump-breaking-01.
#
# The migration touches several distinct Pydantic v1 -> v2 breaking-change
# sites. Each is pinned by one pytest test function. reward = fraction of those
# test functions that pass, so a partial migration (e.g. fixed the import but
# left @validator / .dict() / Field(env=...) untouched) scores a clear fraction
# instead of a saturated 0/1.
#
# Migration sites graded (one test each):
#   1. test_defaults                         BaseSettings import (pydantic-settings)
#   2. test_field_validator_rejects_bad_port @validator -> @field_validator
#   3. test_field_validator_accepts_good_port (same site, positive path)
#   4. test_pre_validator_splits_csv_list    pre=True -> mode="before"
#   5. test_root_validator_cross_field_default @root_validator -> @model_validator
#   6. test_env_binding_for_aliased_field    Field(env=) -> validation_alias  (edge case)
#   7. test_env_binding_for_aliased_list     same alias migration on a list field
#   8. test_model_dump_helper                .dict() -> .model_dump()
#   9. test_model_validate_helper            .parse_obj() -> .model_validate()
#
# reward.json MUST stay a FLAT dict of scalar numbers (Harbor pydantic rejects
# nested dict/list values -> reward=None / trial error; FOOTGUNS #38).
set -u
mkdir -p /logs/verifier
cd /app

# answer_present (VOID vs wrong): settings.py written & non-empty, read tolerantly.
ap=$(python3 -c "print(1 if open('/app/settings.py', errors='replace').read().strip() else 0)" 2>/dev/null || echo 0)

# Tamper check: the agent must not have edited the pinned test file. If it did,
# every site is unverifiable -> reward 0.
if ! diff -q /app/tests/test_settings.py /opt/canonical/test_settings.py >/dev/null 2>&1; then
    cat > /logs/verifier/reward.json <<EOF
{"reward": 0.0, "correctness": 0, "instruction_following": 0, "satisfied": 0, "n_checks": 9, "answer_present": ${ap}}
EOF
    echo "test file tampered — reward 0" > /logs/verifier/note.log
    exit 0
fi

# Run the pinned test functions one at a time so each migration site is graded
# independently.
TESTS=(
  "test_defaults"
  "test_field_validator_rejects_bad_port"
  "test_field_validator_accepts_good_port"
  "test_pre_validator_splits_csv_list"
  "test_root_validator_cross_field_default"
  "test_env_binding_for_aliased_field"
  "test_env_binding_for_aliased_list"
  "test_model_dump_helper"
  "test_model_validate_helper"
)

satisfied=0
N=${#TESTS[@]}
: > /logs/verifier/pytest.log
: > /logs/verifier/sites.log
for t in "${TESTS[@]}"; do
    if python -m pytest "tests/test_settings.py::${t}" -q >>/logs/verifier/pytest.log 2>&1; then
        satisfied=$((satisfied+1))
        echo "PASS ${t}" >> /logs/verifier/sites.log
    else
        echo "FAIL ${t}" >> /logs/verifier/sites.log
    fi
done

reward=$(python3 -c "print(round(${satisfied}/${N}, 4))")
if [ "${satisfied}" -eq "${N}" ]; then correctness=1; else correctness=0; fi

cat > /logs/verifier/reward.json <<EOF
{"reward": ${reward}, "correctness": ${correctness}, "instruction_following": 1, "satisfied": ${satisfied}, "n_checks": ${N}, "answer_present": ${ap}}
EOF

# S4 crash guard: if the grader above crashed before emitting a parseable
# reward.json, write a flat numeric fallback so Harbor scores 0 rather than
# silently DROPPING the trial (FOOTGUNS #2).
[ -s /logs/verifier/reward.json ] || echo '{"reward":0.0}' > /logs/verifier/reward.json

#!/bin/bash
# GRADED final verifier (multi_step_reward_strategy="final" — only this counts).
#
# 12 independent sub-checks of /app/tempconv.py behavior + the agent's pytest
# suite. reward = matched / 12 (continuous gradient); correctness=1 only if all
# 12 pass. A harness that implements only c2f, or skips the absolute-zero guard,
# or emits 1-decimal output, shaves measurable fractions instead of 0/1.
set -u
mkdir -p /logs/verifier
s=0
BIN=/app/tempconv.py

# Helper: assert stdout (whitespace-stripped) equals $3 for `tempconv MODE VAL`.
eq() {
    local got
    got=$(python "$BIN" "$1" "$2" 2>/dev/null | tr -d '[:space:]')
    [ "$got" = "$3" ]
}

if [ -f "$BIN" ]; then
    eq c2f 100   "212.00"  && s=$((s+1))   # 1: c2f boiling
    eq c2f -40   "-40.00"  && s=$((s+1))   # 2: c2f negative crossover
    eq f2c 98.6  "37.00"   && s=$((s+1))   # 3: f2c body temp
    eq c2k 0     "273.15"  && s=$((s+1))   # 4: c2k freezing
    eq k2c 0     "-273.15" && s=$((s+1))   # 5: k2c zero kelvin
    eq f2c 32    "0.00"    && s=$((s+1))   # 6: zero formatting
    eq c2f 0     "32.00"   && s=$((s+1))   # 7: exact two decimals (not 32.0)

    # 8: absolute-zero guard via c2k (-300 C is below 0 K) -> exit 2, no stdout
    o=$(python "$BIN" c2k -300 2>/dev/null); rc=$?
    [ "$rc" -eq 2 ] && [ -z "$(echo "$o" | tr -d '[:space:]')" ] && s=$((s+1))

    # 9: absolute-zero guard via k2c (-5 K is below 0 K) -> exit 2, no stdout
    o=$(python "$BIN" k2c -5 2>/dev/null); rc=$?
    [ "$rc" -eq 2 ] && [ -z "$(echo "$o" | tr -d '[:space:]')" ] && s=$((s+1))

    # 10: unknown mode -> exit 2
    python "$BIN" nope 10 >/dev/null 2>&1; [ $? -eq 2 ] && s=$((s+1))

    # 11: successful conversion -> exit 0
    python "$BIN" c2f 25 >/dev/null 2>&1; [ $? -eq 0 ] && s=$((s+1))
fi

# 12: the agent's own pytest suite exists (>=3 tests) and passes.
if [ -f /app/test_tempconv.py ]; then
    ntests=$(grep -cE '^[[:space:]]*def test_' /app/test_tempconv.py || echo 0)
    if [ "$ntests" -ge 3 ] && (cd /app && python -m pytest test_tempconv.py -q >/dev/null 2>&1); then
        s=$((s+1))
    fi
fi

reward=$(python3 -c "print(round($s / 12.0, 4))")
correctness=$(python3 -c "print(1 if $s == 12 else 0)")
cat > /logs/verifier/reward.json <<EOF
{"reward": ${reward}, "correctness": ${correctness}, "matched": ${s}, "n_checks": 12}
EOF

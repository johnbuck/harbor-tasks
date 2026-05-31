#!/bin/bash
# Graded verifier: blends answer-correctness with tool-selection precision/recall.
#
# Two independent graded axes, each a fraction in [0,1]:
#   answer_fraction = (# of the 3 answer fields that are correct) / 3
#   tool_f1         = harmonic mean of tool precision + recall over the
#                     3 correct tools, read from /var/log/tool-calls.log
#
#   reward = 0.5 * answer_fraction + 0.5 * tool_f1
#
# This is ADDITIVE (not multiplied) so the reward is a continuous gradient:
# a partial answer or sloppy tool selection each shave off a measurable
# fraction instead of collapsing the whole reward to 0. correctness=1 only
# when all three answers are right AND tool selection is perfect (f1==1).
set -u
mkdir -p /logs/verifier

# --- answer correctness (3 sub-checks) ---
ans_ok=0
cc=""; tw=""; tq=""
if [ -f /app/answer.json ]; then
    cc=$(python3 -c "import json; d=json.load(open('/app/answer.json')); print(d.get('customer_count'))" 2>/dev/null)
    tw=$(python3 -c "import json; d=json.load(open('/app/answer.json')); print(str(d.get('top_word','')).lower())" 2>/dev/null)
    tq=$(python3 -c "import json; d=json.load(open('/app/answer.json')); print(d.get('total_quantity'))" 2>/dev/null)
fi
[ "$cc" = "7" ]  && ans_ok=$((ans_ok + 1))
[ "$tw" = "the" ] && ans_ok=$((ans_ok + 1))
[ "$tq" = "19" ] && ans_ok=$((ans_ok + 1))
answer_fraction=$(python3 -c "print($ans_ok / 3.0)")

# --- tool selection ---
LOG=/var/log/tool-calls.log
total=$(wc -l < "$LOG" 2>/dev/null || echo 0)
total=$(echo "$total" | tr -d '[:space:]')
correct_tools="csv-row-count word-tally json-key-sum"
correct_calls=$(grep -cE '^[^ ]+ (csv-row-count|word-tally|json-key-sum) ' "$LOG" 2>/dev/null || echo 0)
correct_calls=$(echo "$correct_calls" | tr -d '[:space:]')

# Precision: fraction of calls that were to correct tools.
precision=$(python3 -c "t=$total; print($correct_calls / t if t > 0 else 0.0)")

# Recall: how many of the 3 correct tools were invoked at all.
hit=0
for t in $correct_tools; do
    grep -qE "^[^ ]+ $t " "$LOG" && hit=$((hit + 1))
done
recall=$(python3 -c "print($hit / 3.0)")

# F1
tool_f1=$(python3 -c "
p, r = $precision, $recall
print(0.0 if (p + r) == 0 else 2 * p * r / (p + r))
")

# --- blended reward ---
reward=$(python3 -c "print(round(0.5 * $answer_fraction + 0.5 * $tool_f1, 4))")

# correctness: fully correct answer AND perfect tool selection.
correctness=$(python3 -c "print(1 if ($ans_ok == 3 and abs($tool_f1 - 1.0) < 1e-9) else 0)")

cat > /logs/verifier/reward.json <<EOF
{"reward": ${reward}, "correctness": ${correctness}, "answer_fraction": ${answer_fraction}, "answers_correct": ${ans_ok}, "tool_precision": ${precision}, "tool_recall": ${recall}, "tool_f1": ${tool_f1}, "tool_calls_total": ${total}, "tool_calls_correct": ${correct_calls}}
EOF

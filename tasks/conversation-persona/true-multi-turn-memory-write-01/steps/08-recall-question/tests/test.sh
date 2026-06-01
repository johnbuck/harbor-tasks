#!/bin/bash
# Final-step verifier (multi_step_reward_strategy="final") for
# true-multi-turn-memory-write-01 (HARD).
#
# The conversation shared EIGHT personal fields across turns, TWO of which were
# CORRECTED in a later turn (timezone Pacific -> Mountain/Denver; climbing nights
# Tue/Thu/Sat -> Mon/Wed/Fri). The final answer must recap all eight using the
# LATEST values, then plan a constraint-satisfying dinner.
#
# Graded as a FRACTION of the eight fields the answer reproduces correctly:
#   - the two updated fields require the NEW value; stating the stale value (or
#     omitting the field) scores 0 for that field, so partial / stale memory
#     surfaces as a fraction.
#   field_score = correct_fields / 8
#   dinner_ok   = 1 iff vegetarian AND peanut-free (the hard dietary constraints)
#   reward      = round(field_score * (0.85 + 0.15 * dinner_ok), 4)
#   correctness = 1 iff correct_fields == 8 AND dinner_ok == 1 else 0

set -u
mkdir -p /logs/verifier

if [ ! -s /app/answer.md ]; then
    cat > /logs/verifier/reward.json <<'EOF'
{"reward": 0.0, "correctness": 0, "correct_fields": 0, "total_fields": 8, "f_diet": 0, "f_pet": 0, "f_timezone": 0, "f_allergy": 0, "f_hobby": 0, "f_climb_days": 0, "f_coffee": 0, "f_daughter": 0, "dinner_ok": 0, "missing_answer": 1}
EOF
    exit 0
fi

ans=$(tr '[:upper:]' '[:lower:]' < /app/answer.md)
has() { echo "$ans" | grep -qE "$1"; }

# --- 8 profile fields (latest values) ---

# 1. Diet = vegetarian
f_diet=0; has 'vegetarian|lacto-ovo|lacto ovo' && f_diet=1

# 2. Pet = cat named Sushi
f_pet=0; has 'sushi' && has 'cat' && f_pet=1

# 3. Timezone = Mountain / Denver (UPDATED). Must NOT present Pacific as current.
f_timezone=0
if has 'mountain time|mountain \(|america/denver|mt \(|denver|\bmt\b|\bmst\b|\bmdt\b'; then
    # reject if it still calls the CURRENT timezone Pacific
    if ! echo "$ans" | grep -qE 'timezone[^a-z]*[:=-]?[^a-z]*pacific|pacific time|currently.*pacific|on pacific|\bpt\b|\bpst\b|\bpdt\b'; then
        f_timezone=1
    fi
fi

# 4. Allergy = peanut
f_allergy=0; has 'peanut' && f_allergy=1

# 5. Hobby = bouldering / climbing
f_hobby=0; has 'boulder|climb' && f_hobby=1

# 6. Climbing nights = Mon/Wed/Fri (UPDATED). Must NOT present Tue/Thu/Sat as current.
f_climb_days=0
if has 'monday' && has 'wednesday' && has 'friday'; then
    if ! echo "$ans" | grep -qE 'tuesday|thursday|saturday'; then
        f_climb_days=1
    fi
fi

# 7. Coffee = oat-milk latte
f_coffee=0; has 'oat' && has 'latte|coffee' && f_coffee=1

# 8. Daughter = Mira
f_daughter=0; has 'mira' && f_daughter=1

correct_fields=$((f_diet + f_pet + f_timezone + f_allergy + f_hobby + f_climb_days + f_coffee + f_daughter))

# --- dinner dietary constraints ---
meat_pat='chicken|beef|pork|bacon|sausage|fish|salmon|tuna|shrimp|prawn|lamb|turkey|duck|\bham\b|steak|carnitas|pancetta|prosciutto'
veg=1; echo "$ans" | grep -qE "$meat_pat" && veg=0
peanut=1
if has 'peanut'; then
    # allow allergy-recap + explicit avoidance, but if a peanut INGREDIENT is used unguarded, fail
    if echo "$ans" | grep -qE 'peanut (sauce|butter|oil|noodle|dressing)' && \
       ! echo "$ans" | grep -qE '(no|without|skip|avoid|free of|free from|instead of) peanut|peanut[- ]free'; then
        peanut=0
    fi
fi
dinner_ok=$(( veg * peanut ))

reward=$(python3 -c "
cf=$correct_fields; dok=$dinner_ok
print(round((cf/8.0) * (0.85 + 0.15*dok), 4))
")
correctness=$(python3 -c "print(1 if ($correct_fields==8 and $dinner_ok==1) else 0)")

cat > /logs/verifier/reward.json <<EOF
{"reward": ${reward}, "correctness": ${correctness}, "correct_fields": ${correct_fields}, "total_fields": 8, "f_diet": ${f_diet}, "f_pet": ${f_pet}, "f_timezone": ${f_timezone}, "f_allergy": ${f_allergy}, "f_hobby": ${f_hobby}, "f_climb_days": ${f_climb_days}, "f_coffee": ${f_coffee}, "f_daughter": ${f_daughter}, "dinner_ok": ${dinner_ok}}
EOF

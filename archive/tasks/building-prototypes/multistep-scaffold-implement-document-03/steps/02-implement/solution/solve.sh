#!/bin/bash
# Oracle — step 2: implement c_to_f, f_to_c (both abs-zero guarded), round_temp.
set -e

cat > /app/tempconv/__init__.py <<'EOF'
ABS_ZERO_C = -273.15
ABS_ZERO_F = -459.67

def c_to_f(c):
    if c < ABS_ZERO_C:
        raise ValueError("temperature below absolute zero")
    return c * 9 / 5 + 32

def f_to_c(f):
    if f < ABS_ZERO_F:
        raise ValueError("temperature below absolute zero")
    return (f - 32) * 5 / 9

def round_temp(t, ndigits=1):
    return round(t, ndigits)
EOF

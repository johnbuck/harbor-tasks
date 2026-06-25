#!/bin/bash
set -e
cat > /app/plan.md <<'EOF'
# tempconv.py Implementation Plan

1. Parse `sys.argv`: read `<mode>` (a string) and `<value>` (parsed with
   `float()`). The four supported modes are `c2f`, `f2c`, `c2k`, and `k2c`.
2. If `<mode>` is not one of those four, write an error message to `stderr`
   and exit with status code 2 (unknown-mode handling).
3. Apply the correct conversion formula per mode:
   - `c2f`: F = C * 9/5 + 32
   - `f2c`: C = (F - 32) * 5/9
   - `c2k`: K = C + 273.15
   - `k2c`: C = K - 273.15
4. Validate against absolute zero: compute the equivalent Kelvin value of the
   result; if it is below 0 K (below -273.15 °C / below -459.67 °F), write an
   error to `stderr` and exit with status code 2 without printing a number.
5. Otherwise format the result to exactly two decimal places with
   `f"{value:.2f}"` and print it to stdout.
EOF

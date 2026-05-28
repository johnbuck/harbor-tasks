#!/bin/bash
set -e
cat > /app/plan.md <<'EOF'
# c2f.py Implementation Plan

1. Parse the command-line argument as a float (Celsius value) using `sys.argv` and `float()`.
2. Apply the conversion formula: Fahrenheit = Celsius × 9/5 + 32.
3. Format the result to exactly one decimal place using Python's `f"{value:.1f}"` formatting.
4. Print the formatted result to stdout.
EOF

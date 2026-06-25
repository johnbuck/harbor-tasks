#!/bin/bash
# Oracle — step 2: implement the four functions, divide is float + guards zero.
set -e

cat > /app/calc/__init__.py <<'EOF'
def add(a, b):
    return a + b

def sub(a, b):
    return a - b

def mul(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ZeroDivisionError("division by zero")
    return a / b
EOF

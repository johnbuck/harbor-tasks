#!/bin/bash
# Oracle — step 3: a README that documents all four functions, states the
# divide float + ZeroDivisionError contract, and a runnable example whose
# printed outputs match the inline comments.
set -e

cat > /app/README.md <<'EOF'
# calc

A minimal Python package providing four arithmetic operations:
`add`, `sub`, `mul`, and `divide`.

## Installation

No external dependencies. Ensure the `calc/` directory is on your Python path
(e.g. run from `/app`).

## API Reference

### `add(a, b)`
Returns the sum `a + b`.
- **Parameters:** `a`, `b` — operands (int or float)
- **Returns:** `a + b`

### `sub(a, b)`
Returns the difference `a - b`.
- **Parameters:** `a`, `b` — operands (int or float)
- **Returns:** `a - b`

### `mul(a, b)`
Returns the product `a * b`.
- **Parameters:** `a`, `b` — operands (int or float)
- **Returns:** `a * b`

### `divide(a, b)`
Returns the quotient `a / b` as a **float**.
- **Parameters:** `a` — dividend, `b` — divisor (int or float)
- **Returns:** `a / b` as a `float`
- **Raises:** `ZeroDivisionError` (message `"division by zero"`) when `b == 0`.

## Usage Example

```python
from calc import add, sub, mul, divide

print(add(2, 3))     # 5
print(sub(5, 2))     # 3
print(mul(4, 3))     # 12
print(divide(10, 2)) # 5.0

try:
    divide(1, 0)
except ZeroDivisionError as e:
    print(e)         # division by zero
```
EOF

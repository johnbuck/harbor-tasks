#!/bin/bash
# Oracle — step 3: README documenting all three functions + the absolute-zero
# ValueError, with a runnable example whose comments match real output.
set -e

cat > /app/README.md <<'EOF'
# tempconv

A minimal Python package for temperature conversions:
`c_to_f`, `f_to_c`, and `round_temp`.

## Installation

No external dependencies. Ensure the `tempconv/` directory is on your Python path
(e.g. run from `/app`).

## API Reference

### `c_to_f(c)`
Converts Celsius to Fahrenheit.
- **Formula:** `F = C * 9/5 + 32`
- **Parameters:** `c` — temperature in Celsius (int or float)
- **Returns:** temperature in Fahrenheit (float)
- **Raises:** `ValueError` if `c < -273.15` (below absolute zero).

### `f_to_c(f)`
Converts Fahrenheit to Celsius.
- **Formula:** `C = (F - 32) * 5/9`
- **Parameters:** `f` — temperature in Fahrenheit (int or float)
- **Returns:** temperature in Celsius (float)
- **Raises:** `ValueError` if `f < -459.67` (below absolute zero).

### `round_temp(t, ndigits=1)`
Rounds a temperature `t` to `ndigits` decimal places (default 1).
- **Parameters:** `t` (int or float), `ndigits` (int, default `1`)
- **Returns:** the rounded value (float)

## Usage Example

```python
from tempconv import c_to_f, f_to_c, round_temp

print(c_to_f(100))                 # 212.0
print(f_to_c(32))                  # 0.0
print(round_temp(c_to_f(37)))      # 98.6

try:
    c_to_f(-300)
except ValueError as e:
    print(e)                       # temperature below absolute zero
```
EOF

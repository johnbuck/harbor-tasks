#!/bin/bash
set -e

cat > /app/README.md <<'EOF'
# tempconv

A minimal Python package for temperature conversions.

## Installation

No external dependencies. Ensure the `tempconv/` directory is on your Python path (e.g. run from `/app`).

## API Reference

### `c_to_f(c)`

Converts a temperature from Celsius to Fahrenheit.

**Formula:** `F = C × 9/5 + 32`

**Parameters:**
- `c` — temperature in Celsius (int or float)

**Returns:** temperature in Fahrenheit (float)

## Usage Example

```python
from tempconv import c_to_f

print(c_to_f(100))  # 212.0  — water boiling point
print(c_to_f(0))    # 32.0   — water freezing point
print(c_to_f(37))   # 98.6   — normal human body temperature
```
EOF

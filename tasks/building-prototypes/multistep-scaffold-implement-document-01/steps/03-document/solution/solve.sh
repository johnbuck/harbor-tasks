#!/bin/bash
set -e

cat > /app/README.md <<'EOF'
# calc

A minimal Python package that provides arithmetic utilities.

## Installation

No external dependencies. Simply ensure the `calc/` directory is on your Python path (e.g. run from `/app`).

## API Reference

### `add(a, b)`

Returns the sum of `a` and `b`.

**Parameters:**
- `a` — first operand (int or float)
- `b` — second operand (int or float)

**Returns:** `a + b`

## Usage Example

```python
from calc import add

result = add(2, 3)
print(result)  # 5

result2 = add(-1, 1)
print(result2)  # 0
```
EOF

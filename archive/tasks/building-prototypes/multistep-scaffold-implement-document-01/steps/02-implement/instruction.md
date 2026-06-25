# Step 2 — Implement the stubs

Implement all four functions in `/app/calc/__init__.py` so that the tests in
`/app/tests/test_calc.py` pass.

Behavior:

- `add(a, b)` → `a + b`
- `sub(a, b)` → `a - b`
- `mul(a, b)` → `a * b`
- `divide(a, b)` → `a / b` as a **float**, BUT:
  - If `b == 0`, raise `ZeroDivisionError` with the message
    `"division by zero"` (do not let an unhandled exception or `inf` leak out).
  - `divide(10, 2)` must equal `5.0` (a float, not the int `5`).

Run the tests with:

```
cd /app && python -m pytest tests/test_calc.py
```

All tests must pass.

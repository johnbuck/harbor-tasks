# Step 2 — Implement the stubs

Implement all three functions in `/app/tempconv/__init__.py` so that the tests in
`/app/tests/test_tempconv.py` pass.

Behavior:

- `c_to_f(c)` → Celsius to Fahrenheit, `F = C * 9/5 + 32`, returned as a float.
  - `c_to_f(100)` → `212.0`, `c_to_f(0)` → `32.0`
  - **Raise `ValueError` if `c < -273.15`** (below absolute zero) — do not return
    a nonsense temperature.
- `f_to_c(f)` → Fahrenheit to Celsius, `C = (F - 32) * 5/9`, returned as a float.
  - `f_to_c(32)` → `0.0`
  - **Raise `ValueError` if `f < -459.67`** (below absolute zero).
- `round_temp(t, ndigits=1)` → round `t` to `ndigits` decimal places (default 1).
  - `round_temp(98.599)` → `98.6`

Run the tests with:

```
cd /app && python -m pytest tests/test_tempconv.py
```

All tests must pass.

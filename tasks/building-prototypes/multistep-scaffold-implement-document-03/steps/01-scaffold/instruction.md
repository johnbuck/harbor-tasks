# Step 1 — Scaffold the package skeleton

Create the following file layout under `/app`:

```
tempconv/
    __init__.py
tests/
    test_tempconv.py
```

Requirements:

- `tempconv/__init__.py` must define **three** functions, each raising
  `NotImplementedError` (stubs only — do NOT implement them yet):
  - `c_to_f(c)`
  - `f_to_c(f)`
  - `round_temp(t, ndigits=1)`
- `tests/test_tempconv.py` must import all three names from `tempconv` and
  contain at least **five** test cases (functions named `test_*`), including:
  - `c_to_f(100) == 212.0`
  - `c_to_f(0) == 32.0`
  - `f_to_c(32) == 0.0`
  - `round_temp(98.599) == 98.6`
  - a test that `c_to_f(-300)` raises `ValueError` (below absolute zero)
    (use `pytest.raises(ValueError)`).

Do NOT implement the functions yet — only the stubs with `raise NotImplementedError`.

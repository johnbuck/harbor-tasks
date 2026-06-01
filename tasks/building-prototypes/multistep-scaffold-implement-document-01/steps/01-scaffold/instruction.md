# Step 1 — Scaffold the package skeleton

Create the following file layout under `/app`:

```
calc/
    __init__.py
tests/
    test_calc.py
```

Requirements:

- `calc/__init__.py` must define **four** functions, each raising `NotImplementedError`
  (stubs only — do NOT implement them yet):
  - `add(a, b)`
  - `sub(a, b)`
  - `mul(a, b)`
  - `divide(a, b)`
- `tests/test_calc.py` must import all four names from `calc` and contain at least
  **five** test cases (functions named `test_*`), including:
  - `add(2, 3) == 5`
  - `sub(5, 2) == 3`
  - `mul(4, 3) == 12`
  - `divide(10, 2) == 5.0`
  - a test that `divide(1, 0)` raises `ZeroDivisionError`
    (use `pytest.raises(ZeroDivisionError)`).

Do NOT implement the functions yet — only the stubs with `raise NotImplementedError`.

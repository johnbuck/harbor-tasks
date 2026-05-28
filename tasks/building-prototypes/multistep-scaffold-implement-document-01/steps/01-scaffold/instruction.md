# Step 1 — Scaffold the package skeleton

Create the following file layout under `/app`:

```
calc/
    __init__.py
tests/
    test_calc.py
```

Requirements:
- `calc/__init__.py` must define a function `add(a, b)` that raises `NotImplementedError`.
- `tests/test_calc.py` must import `add` from `calc` and contain at least two test cases:
  - `add(2, 3) == 5`
  - `add(-1, 1) == 0`

Do NOT implement `add` yet — only the stub with `raise NotImplementedError`.

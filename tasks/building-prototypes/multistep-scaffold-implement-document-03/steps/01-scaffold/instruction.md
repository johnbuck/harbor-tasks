# Step 1 — Scaffold the package skeleton

Create the following file layout under `/app`:

```
tempconv/
    __init__.py
tests/
    test_tempconv.py
```

Requirements:
- `tempconv/__init__.py` must define a function `c_to_f(c)` that raises `NotImplementedError`.
- `tests/test_tempconv.py` must import `c_to_f` from `tempconv` and contain at least two test cases:
  - `c_to_f(100) == 212.0`
  - `c_to_f(0) == 32.0`

Do NOT implement `c_to_f` yet — only the stub with `raise NotImplementedError`.

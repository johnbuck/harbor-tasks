# Step 1 — Scaffold the package skeleton

Create the following file layout under `/app`:

```
textkit/
    __init__.py
tests/
    test_textkit.py
```

Requirements:
- `textkit/__init__.py` must define a function `slugify(s)` that raises `NotImplementedError`.
- `tests/test_textkit.py` must import `slugify` from `textkit` and contain at least one test case:
  - `slugify("Hello, World!") == "hello-world"`

Do NOT implement `slugify` yet — only the stub with `raise NotImplementedError`.

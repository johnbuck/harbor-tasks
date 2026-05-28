# Step 2 — Implement the stub

Implement `slugify(s)` in `/app/textkit/__init__.py` so that the tests in `/app/tests/test_textkit.py` pass.

The function must:
1. Lowercase the input string.
2. Replace runs of non-alphanumeric characters with a single hyphen.
3. Strip leading and trailing hyphens from the result.

Examples:
- `slugify("Hello, World!")` → `"hello-world"`

Run the tests with:
```
cd /app && python -m pytest tests/test_textkit.py
```

All tests must pass.

# Step 1 — Scaffold the package skeleton

Create the following file layout under `/app`:

```
textkit/
    __init__.py
tests/
    test_textkit.py
```

Requirements:

- `textkit/__init__.py` must define **three** functions, each raising
  `NotImplementedError` (stubs only — do NOT implement them yet):
  - `slugify(s)`
  - `truncate(s, n, suffix="...")`
  - `word_count(s)`
- `tests/test_textkit.py` must import all three names from `textkit` and contain
  at least **five** test cases (functions named `test_*`), including:
  - `slugify("Hello, World!") == "hello-world"`
  - `truncate("hello world", 8) == "hello..."`
  - `truncate("hi", 8) == "hi"` (shorter-than-limit strings are returned intact)
  - `word_count("  the  quick brown   fox ") == 4`
  - `slugify("") == ""` (empty string is handled, not an error)

Do NOT implement the functions yet — only the stubs with `raise NotImplementedError`.

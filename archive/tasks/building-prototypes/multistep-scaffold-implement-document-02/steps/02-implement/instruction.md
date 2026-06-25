# Step 2 — Implement the stubs

Implement all three functions in `/app/textkit/__init__.py` so that the tests in
`/app/tests/test_textkit.py` pass.

Behavior:

- `slugify(s)`:
  1. Lowercase the input string.
  2. Replace runs of non-alphanumeric characters with a single hyphen.
  3. Strip leading and trailing hyphens.
  - `slugify("Hello, World!")` → `"hello-world"`
  - `slugify("")` → `""`

- `truncate(s, n, suffix="...")`: shorten `s` so the **returned string is at most
  `n` characters long, including the suffix**.
  - If `len(s) <= n`, return `s` unchanged (no suffix added).
  - Otherwise return the first `n - len(suffix)` characters of `s` followed by
    `suffix`, so the total length is exactly `n`.
  - `truncate("hello world", 8)` → `"hello..."` (length 8, NOT `"hello wo..."`).

- `word_count(s)`: return the number of whitespace-separated words, ignoring
  leading/trailing/repeated whitespace.
  - `word_count("  the  quick brown   fox ")` → `4`
  - `word_count("")` → `0`

Run the tests with:

```
cd /app && python -m pytest tests/test_textkit.py
```

All tests must pass.

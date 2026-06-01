#!/bin/bash
# Oracle — step 3: README documenting all three functions, the suffix-aware
# truncate contract, and a runnable example whose comments match real output.
set -e

cat > /app/README.md <<'EOF'
# textkit

A minimal Python package for common text transformations:
`slugify`, `truncate`, and `word_count`.

## Installation

No external dependencies. Ensure the `textkit/` directory is on your Python path
(e.g. run from `/app`).

## API Reference

### `slugify(s)`
Converts a string into a URL-friendly slug.
- Lowercases the string, replaces runs of non-alphanumeric characters with a
  single hyphen, and strips leading/trailing hyphens.
- **Parameters:** `s` — input string (str)
- **Returns:** slug (str). Empty input returns `""`.

### `truncate(s, n, suffix="...")`
Shortens `s` so the returned string is **at most `n` characters long, including
the suffix**.
- If `len(s) <= n`, returns `s` unchanged (no suffix added).
- Otherwise returns the first `n - len(suffix)` characters followed by `suffix`,
  so the total length is exactly `n`. Thus `truncate("hello world", 8)` is
  `"hello..."` (8 chars), NOT `"hello wo..."`.
- **Parameters:** `s` (str), `n` (int) — max length, `suffix` (str, default `"..."`)
- **Returns:** truncated string (str)

### `word_count(s)`
Counts whitespace-separated words, ignoring leading/trailing/repeated whitespace.
- **Parameters:** `s` — input string (str)
- **Returns:** word count (int). `word_count("")` is `0`.

## Usage Example

```python
from textkit import slugify, truncate, word_count

print(slugify("Hello, World!"))                # hello-world
print(truncate("hello world", 8))              # hello...
print(truncate("hi", 8))                       # hi
print(word_count("  the  quick brown   fox ")) # 4
```
EOF

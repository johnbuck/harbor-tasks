#!/bin/bash
set -e

cat > /app/README.md <<'EOF'
# textkit

A minimal Python package for common text transformations.

## Installation

No external dependencies. Ensure the `textkit/` directory is on your Python path (e.g. run from `/app`).

## API Reference

### `slugify(s)`

Converts a string into a URL-friendly slug.

**Transformation rules:**
1. Lowercases the entire string.
2. Replaces runs of non-alphanumeric characters with a single hyphen (`-`).
3. Strips any leading or trailing hyphens from the result.

**Parameters:**
- `s` — the input string (str)

**Returns:** a slug string (str)

## Usage Example

```python
from textkit import slugify

result = slugify("Hello, World!")
print(result)  # hello-world

result2 = slugify("  Python is  GREAT!!! ")
print(result2)  # python-is-great
```
EOF

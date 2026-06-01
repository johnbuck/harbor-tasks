There is a function at `/app/stringutils.py`:

```python
def slugify(s: str) -> str:
    """Lowercase, replace runs of non-alphanumerics with a single hyphen,
    and strip leading/trailing hyphens. E.g. "Hello, World!" -> "hello-world"."""
```

Write a pytest test file at `/app/tests/test_slugify.py` that **thoroughly**
tests `slugify`. Your tests must **pass against the provided implementation**.

- Put your tests in `/app/tests/test_slugify.py` and import `slugify` from
  `stringutils`.
- You can run them with: `cd /app && python -m pytest tests/test_slugify.py -v`

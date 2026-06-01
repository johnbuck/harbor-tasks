There is a function at `/app/stringutils.py`:

```python
def slugify(s: str) -> str:
    """Lowercase, replace runs of non-alphanumerics with a single hyphen,
    and strip leading/trailing hyphens. E.g. "Hello, World!" -> "hello-world"."""
```

Write a pytest test file at `/app/tests/test_slugify.py` that **thoroughly**
tests `slugify`. Your tests must **pass against the provided implementation**
and must meaningfully exercise each of these behaviors, so that a broken
implementation of any one of them would be caught:

1. **Lowercasing** — uppercase input is lowercased.
2. **Collapsing runs** — a run of consecutive non-alphanumeric characters
   (multiple spaces, punctuation, mixed) becomes a *single* hyphen, not several.
3. **Stripping** — leading and trailing hyphens are removed.
4. **Preserving alphanumerics** — letters AND digits are kept (e.g. `66` stays
   `66`).

Use exact-equality assertions (`assert slugify(...) == "..."`) so the tests
actually pin the behavior — a test that only checks "no exception" or
`len(result) > 0` does not exercise the behavior.

Constraints:

- Do not modify `/app/stringutils.py`.
- Put your tests in `/app/tests/test_slugify.py` and import `slugify` from
  `stringutils`.
- You can run them with: `cd /app && python -m pytest tests/test_slugify.py -v`

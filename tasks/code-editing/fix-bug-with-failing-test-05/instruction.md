There is a Python utility at `/app/flatten.py` and a test for it at
`/app/tests/test_flatten.py`. The test is currently failing. Fix the
bug in `flatten.py` so that all tests pass.

Constraints:

- Do not modify the test file.
- Do not change the function signature of `flatten(items: list) -> list`.
- Keep the implementation simple — match what the tests expect.

You can run the tests with:

```
cd /app && python -m pytest tests/test_flatten.py -v
```

When the tests pass, you are done.

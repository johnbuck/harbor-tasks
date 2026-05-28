There is a Python utility at `/app/intervals.py` and a test for it at
`/app/tests/test_intervals.py`. The test is currently failing. Fix the
bug in `intervals.py` so that all tests pass.

Constraints:

- Do not modify the test file.
- Do not change the function signature of
  `merge_intervals(intervals: list[list[int]]) -> list[list[int]]`.
- Keep the implementation simple — match what the tests expect.

You can run the tests with:

```
cd /app && python -m pytest tests/test_intervals.py -v
```

When the tests pass, you are done.

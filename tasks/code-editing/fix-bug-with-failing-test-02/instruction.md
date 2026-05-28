There is a Python utility at `/app/running_total.py` and a test for it at
`/app/tests/test_running_total.py`. The test is currently failing. Fix the
bug in `running_total.py` so that all tests pass.

Constraints:

- Do not modify the test file.
- Do not change the function signature of
  `running_total(nums: list[int]) -> list[int]`.
- Keep the implementation simple — match what the tests expect.

You can run the tests with:

```
cd /app && python -m pytest tests/test_running_total.py -v
```

When the tests pass, you are done.

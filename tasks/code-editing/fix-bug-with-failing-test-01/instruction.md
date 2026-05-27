There is a Python utility at `/app/wordcount.py` and a test for it at
`/app/tests/test_wordcount.py`. The test is currently failing. Fix the
bug in `wordcount.py` so that all tests pass.

Constraints:

- Do not modify the test file.
- Do not change the function signature of `count_words(text: str) -> int`.
- Keep the implementation simple — match what the tests expect.

You can run the tests with:

```
cd /app && python -m pytest tests/test_wordcount.py -v
```

When the tests pass, you are done.

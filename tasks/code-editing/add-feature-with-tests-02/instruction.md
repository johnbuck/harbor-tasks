Implement `evaluate(expr: str) -> float` in `/app/calc.py`. The stub raises
`NotImplementedError`; a test suite at `/app/tests/test_calc.py` defines the
required behavior.

The evaluator must handle infix arithmetic with:

- The four binary operators `+`, `-`, `*`, `/` with standard precedence
  (`*` and `/` bind tighter than `+` and `-`).
- Parentheses for grouping.
- Unary minus (e.g. `-3`, `2 * -4`).
- Integer and decimal literals.
- Arbitrary whitespace between tokens.

You do NOT need to support variables, exponentiation, or functions.
`evaluate` returns a `float`. You may not use `eval`/`exec`.

Constraints:

- Do not modify the test file.
- Do not use Python's built-in `eval` or `exec`.

Run the tests with:

```
cd /app && python -m pytest tests/test_calc.py -v
```

When all tests pass, you are done.

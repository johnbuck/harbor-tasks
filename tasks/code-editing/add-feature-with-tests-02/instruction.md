Implement `evaluate(expr: str) -> float` in `/app/calc.py`. The stub raises
`NotImplementedError`; a visible test suite at `/app/tests/test_calc.py` defines
the basic behavior, but the **full contract below** is what's graded.

## Contract for `evaluate(expr: str) -> float`

The evaluator handles infix arithmetic:

1. The four binary operators `+`, `-`, `*`, `/` with standard precedence
   (`*`/`/` bind tighter than `+`/`-`) and **left-to-right associativity**
   (`10 - 3 - 2 == 5`, `12 / 4 / 3 == 1`).
2. Parentheses for grouping, including arbitrary nesting.
3. Unary minus (e.g. `-3`, `2 * -4`, `-(3 + 1)`).
4. Integer and decimal literals; arbitrary whitespace between tokens.
5. Returns a `float`.
6. **Malformed input raises `ValueError`.** This includes (non-exhaustively):
   an empty/whitespace-only string, a dangling operator (`"1 +"`, `"* 3"`),
   unbalanced parentheses (`"(1 + 2"`, `"1 + 2)"`), two adjacent numbers with
   no operator (`"1 2"`), and any stray/unrecognized character. Do **not**
   return a wrong number or raise a different exception type for these — raise
   `ValueError`.
7. Division by zero raises `ZeroDivisionError` (Python's natural behavior; do
   not swallow it).

You may **not** use Python's built-in `eval` or `exec`.

The visible tests cover valid expressions (precedence, parens, unary minus,
decimals, associativity). The **malformed-input → `ValueError`** rule (item 6)
is part of the contract and is checked by a hidden grader — a parser that only
handles well-formed input passes the visible tests but mis-handles the error
cases and scores partially.

## Constraints

- Do **not** modify the test file `/app/tests/test_calc.py`.
- Do **not** use Python's built-in `eval` or `exec`.
- Keep the code clean: no debug `print()`s, no leftover scratch output.

Run the visible tests with:

```
cd /app && python -m pytest tests/test_calc.py -v
```

Passing the visible tests is necessary but **not** sufficient for full credit —
the hidden grader also checks that malformed input raises `ValueError`.

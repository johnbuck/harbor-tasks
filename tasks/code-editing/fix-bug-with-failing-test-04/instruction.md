There is a Python utility at `/app/intervals.py` and a test for it at
`/app/tests/test_intervals.py`. The visible test is currently failing. Fix
`intervals.py` so it satisfies the **full contract below** — not just the
visible tests.

## Contract for `merge_intervals(intervals: list[list[int]]) -> list[list[int]]`

Merge a list of closed integer intervals `[start, end]`:

1. **Overlapping intervals merge.** `[[1,3],[2,6],[8,10]] -> [[1,6],[8,10]]`.
2. **Touching endpoints merge.** `[[1,2],[2,3]] -> [[1,3]]`.
3. **Containment.** A fully-contained interval is absorbed:
   `[[1,10],[2,3]] -> [[1,10]]`.
4. **Input order is irrelevant** — sort internally. The output is sorted by
   start ascending.
5. **The input list must not be mutated** — return new inner lists; do not
   reorder or edit the caller's lists.
6. **Validation.** An interval with `start > end` is invalid. If any interval
   in the input is invalid, raise `ValueError`. (Zero-width intervals where
   `start == end`, e.g. `[5, 5]`, are valid.)
7. Empty input returns `[]`.

The visible tests cover rules 1, 2, 4 and 7. Rules 3, 5 and 6 are part of the
contract and are checked by a hidden grader — implement the whole contract,
not just enough to make the visible tests green.

## Constraints

- Do **not** modify the test file `/app/tests/test_intervals.py`.
- Do **not** change the signature
  `def merge_intervals(intervals: list[list[int]]) -> list[list[int]]`.
- Keep the code clean: no debug `print()`s, no leftover scratch output.

You can run the visible tests with:

```
cd /app && python -m pytest tests/test_intervals.py -v
```

Passing the visible tests is necessary but **not** sufficient for full credit —
the hidden grader also checks containment, no-mutation, and the `ValueError`
validation rule.

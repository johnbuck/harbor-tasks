There is a Python utility at `/app/running_total.py` and a test for it at
`/app/tests/test_running_total.py`. The visible test is currently failing. Fix
`running_total.py` so it satisfies the **full contract below** — not just the
visible tests.

## Contract for `running_total(nums: list[int]) -> list[int]`

Return a list of cumulative sums where element `i` is the sum of all the
**numeric** values seen up to and including index `i`, with these rules:

1. Element `i` of the output is the running sum of `nums[0..i]` inclusive.
   `running_total([1, 2, 3]) == [1, 3, 6]`.
2. Empty input returns an empty list.
3. The input must **not** be mutated — return a new list, leave `nums` untouched.
4. A `None` entry is a **gap**: it contributes `0` to the running sum and the
   output still has one element per input position. So
   `running_total([1, None, 2]) == [1, 1, 3]` (the gap holds the total flat,
   then `2` resumes it).
5. The function must not raise on a `None` entry.

The visible tests cover only rules 1 and 2 (the basic off-by-one bug). Rules 3,
4 and 5 are part of the contract and are checked by a hidden grader —
implement the whole contract, not just enough to make the visible tests green.

## Constraints

- Do **not** modify the test file `/app/tests/test_running_total.py`.
- Do **not** change the signature `def running_total(nums: list[int]) -> list[int]`.
- Keep the code clean: no debug `print()`s, no leftover scratch output.

You can run the visible tests with:

```
cd /app && python -m pytest tests/test_running_total.py -v
```

Passing the visible tests is necessary but **not** sufficient for full credit —
the hidden grader also checks the no-mutation and `None`-gap rules.

There is a Python utility at `/app/flatten.py` and a test for it at
`/app/tests/test_flatten.py`. The visible test is currently failing. Fix
`flatten.py` so it satisfies the **full contract below** — not just the
visible tests.

## Contract for `flatten(items: list) -> list`

Recursively flatten a nested collection into a single flat list, preserving
left-to-right order:

1. **Lists are flattened** to arbitrary depth:
   `flatten([1, [2, [3, [4, 5]]], 6]) == [1, 2, 3, 4, 5, 6]`.
2. **Tuples are also flattened** and treated like lists:
   `flatten([1, (2, 3), [4, (5, 6)]]) == [1, 2, 3, 4, 5, 6]`.
3. **Strings and bytes are atoms** — never iterated character-by-character,
   even though they are iterable: `flatten(["ab", ["cd"]]) == ["ab", "cd"]`.
4. **Every other element is kept as-is**, including dicts, sets, ints, floats,
   `None`, and objects: `flatten([1, None, {"k": 1}]) == [1, None, {"k": 1}]`.
5. The input must **not** be mutated.
6. `flatten([])` returns `[]`.

The visible tests cover only lists and strings-as-atoms (rules 1, 3, 6). The
tuple-flattening, non-string-iterable-as-atom, and no-mutation rules are part
of the contract and are checked by a hidden grader — implement the whole
contract, not just enough to make the visible tests green.

## Constraints

- Do **not** modify the test file `/app/tests/test_flatten.py`.
- Do **not** change the signature `def flatten(items: list) -> list`.
- Keep the code clean: no debug `print()`s, no leftover scratch output.

You can run the visible tests with:

```
cd /app && python -m pytest tests/test_flatten.py -v
```

Passing the visible tests is necessary but **not** sufficient for full credit —
the hidden grader also checks tuple flattening and that non-list/tuple
iterables (strings, dicts, sets) are preserved as atoms.

There is a Python utility at `/app/wordcount.py` and a test for it at
`/app/tests/test_wordcount.py`. The visible test is currently failing. Fix
`wordcount.py` so it satisfies the **full word-counting contract below** — not
just the visible tests.

## Contract for `count_words(text: str) -> int`

Return the number of **words** in `text`, where:

1. Words are whitespace-delimited tokens.
2. A token counts as a word **only if it contains at least one alphanumeric
   character**. Tokens that are purely punctuation/symbols — e.g. `--`, `...`,
   `!?`, `—`, `:)` — are **not** words and must not be counted.
3. A hyphenated or apostrophised word is **one** word: `mother-in-law`,
   `don't`, and `e-mail` each count as 1.
4. Empty or whitespace-only input returns `0`.

The visible tests cover only the basic cases (items 1 and 4). Items 2 and 3 are
part of the contract and are checked by a hidden grader — implement the whole
contract, not just enough to make the visible tests green.

## Constraints

- Do **not** modify the test file `/app/tests/test_wordcount.py`.
- Do **not** change the signature `def count_words(text: str) -> int`.
- Keep the code clean: no debug `print()`s, no leftover scratch output.

You can run the visible tests with:

```
cd /app && python -m pytest tests/test_wordcount.py -v
```

Passing the visible tests is necessary but **not** sufficient for full credit —
the hidden grader also checks the punctuation and hyphenation rules.

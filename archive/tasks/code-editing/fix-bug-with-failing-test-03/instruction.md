There is a Python utility at `/app/palindrome.py` and a test for it at
`/app/tests/test_palindrome.py`. The visible test is currently failing. Fix
`palindrome.py` so it satisfies the **full contract below** — not just the
visible tests.

## Contract for `is_palindrome(s: str) -> bool`

Return `True` if `s` reads the same forwards and backwards after normalization:

1. **Case-insensitive.** Comparison must be case-insensitive across the full
   Unicode range, i.e. use case **folding**, not a naive ASCII lowercase.
   For example the German `"ß"` case-folds to `"ss"`, so
   `is_palindrome("ßReSS")` must be `True` (folds to `"ssress"`... no — it
   folds to `"ssress"`; concretely `is_palindrome("Maßstab batsßam")` style
   cases are out of scope, but `is_palindrome("ßß")` is `True` and
   `is_palindrome("ßẞ")` is `True` because both fold to `"ssss"`).
2. **Only alphanumeric characters count.** All non-alphanumeric characters
   (spaces, punctuation, symbols) are ignored.
3. **Digits count as characters.** `is_palindrome("12321")` is `True`,
   `is_palindrome("12345")` is `False`.
4. The empty string (and any string with no alphanumeric characters, e.g.
   `"!!!"`) is a palindrome → `True`.

The visible tests cover only ASCII letters with spaces/punctuation. The
digit, no-alphanumeric, and Unicode case-**folding** rules are part of the
contract too — implement the whole contract. Note that case-insensitive
comparison across the full Unicode range requires case folding (`str.casefold`,
not `str.lower`).

You can run the visible tests with:

```
cd /app && python -m pytest tests/test_palindrome.py -v
```

You have a working implementation at `/app/wordfreq.py`. Now write tests for it,
and make sure the implementation is fully correct — this final step is graded on
a rubric that checks **both** your test file and the behavior of `wordfreq.py`.

Create `/app/test_wordfreq.py` with pytest tests that verify `wordfreq.py`. Your
tests must (at minimum):

1. Verify a clear-winner case returns the dominant word.
2. Verify **punctuation stripping** (`dog,` and `dog` count as the same word).
3. Verify the **alphabetical tie-break** (two words tied on count → the
   alphabetically-first one is printed).
4. Verify `--stopwords` excludes words and `--min-len` excludes short tokens.
5. Verify `--top N` prints `word count` lines ordered by descending count.

Make `cd /app && python -m pytest test_wordfreq.py` pass.

This step is scored on 12 independent sub-checks: base winner, punctuation
stripping, alphabetical tie-break, lowercase normalization, internal-apostrophe
preservation, `--top` format and ordering, `--stopwords`, `--min-len`, combined
filters, lone-punctuation safety, and a passing pytest suite. Fix
`/app/wordfreq.py` here if it does not satisfy every requirement.

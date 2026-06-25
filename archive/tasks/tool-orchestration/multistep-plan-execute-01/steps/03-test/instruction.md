You have a working implementation at `/app/csv2json.py`. Now write tests for it,
and make sure the implementation is fully correct — this final step is graded on
a rubric that checks **both** your test file and the behavior of `csv2json.py`.

Create `/app/test_csv2json.py` with pytest tests that verify `csv2json.py`. Your
tests must (at minimum):

1. Verify base conversion (no flags) produces an array of dicts with **string**
   values.
2. Verify `--int COL` makes that column's values JSON **integers**.
3. Verify `--filter COL=VAL` keeps only matching rows.
4. Verify `--int COL --sort COL` sorts **numerically** (so `9` sorts before `10`).
5. Verify a header-only CSV prints `[]`.

Make `cd /app && python -m pytest test_csv2json.py` pass.

This step is scored on 12 independent sub-checks: base conversion, `--int`
coercion (value AND type), single and multiple `--int` columns, `--filter`,
lexicographic `--sort`, numeric `--sort`, filter+sort composition, the empty `[]`
case, JSON validity, and a passing pytest suite. Fix `/app/csv2json.py` here if
it does not satisfy every requirement.

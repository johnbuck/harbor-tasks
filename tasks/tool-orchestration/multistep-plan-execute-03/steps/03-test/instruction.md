You have a working implementation at `/app/tempconv.py`. Now write tests for it,
and make sure the implementation is fully correct — this final step is graded on
a rubric that checks **both** your test file and the behavior of `tempconv.py`.

Create `/app/test_tempconv.py` with pytest tests that verify `tempconv.py`. Your
tests must (at minimum):

1. Exercise **all four modes** (`c2f`, `f2c`, `c2k`, `k2c`) with known inputs and
   assert the two-decimal output string.
2. Assert that an **absolute-zero violation** (e.g. `c2k -300`) exits with code
   **2** and prints nothing to stdout.
3. Assert that an **unknown mode** exits with code **2**.

Make `cd /app && python -m pytest test_tempconv.py` pass.

This step is scored on 12 independent sub-checks: the four core conversions,
negative/zero handling, exact two-decimal formatting, the two absolute-zero
guards (via `c2k` and via `k2c`), the unknown-mode exit code, a clean exit-0 on
success, and a passing pytest suite. Make sure `/app/tempconv.py` satisfies every
requirement from the previous step — fix it here if it doesn't.

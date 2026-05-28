You have a working implementation at `/app/wordfreq.py`. Now write tests for it.

Create `/app/test_wordfreq.py` with pytest tests that verify `wordfreq.py` behaves correctly. Your tests must:

1. Create a temporary text file where one word clearly dominates.
2. Run `wordfreq.py` on it (e.g. via `subprocess` or by importing the logic directly).
3. Assert that the output (stripped of whitespace) equals the expected dominant word.

Make `cd /app && python -m pytest test_wordfreq.py` pass.

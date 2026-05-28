You have a working implementation at `/app/c2f.py`. Now write tests for it.

Create `/app/test_c2f.py` with pytest tests that verify `c2f.py` behaves correctly. Your tests must:

1. Run `c2f.py` with at least two known inputs (e.g. `100` and `0`).
2. Assert the output (stripped of whitespace) matches the expected Fahrenheit string to one decimal place.

Make `cd /app && python -m pytest test_c2f.py` pass.

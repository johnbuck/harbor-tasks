You have a working implementation at `/app/csv2json.py`. Now write tests for it.

Create `/app/test_csv2json.py` with pytest tests that verify `csv2json.py` behaves correctly. Your tests must:

1. Create a temporary CSV file with at least 2 data rows.
2. Run `csv2json.py` on it (e.g. via `subprocess` or by importing and calling the logic directly).
3. Assert the output is a valid JSON array of dicts matching the expected rows.

Make `cd /app && python -m pytest test_csv2json.py` pass.

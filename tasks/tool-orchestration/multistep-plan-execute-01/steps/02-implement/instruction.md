You have a plan at `/app/plan.md`. Now implement it.

Create `/app/csv2json.py` so that:

```
python /app/csv2json.py <file.csv> [--int COL]... [--filter COL=VAL] [--sort COL]
```

reads the CSV file, uses the first row as column headers (keys), and prints a
JSON array of objects (one per data row) to stdout.

Requirements:
- Use only Python standard library modules (`csv`, `json`, `sys`, `argparse`).
- Output must be valid JSON parseable by `json.loads`.
- Each row becomes a dict mapping header names to string values **by default**.
- **`--int COL`** (repeatable): emit column `COL`'s values as JSON **integers**.
  Example: with `--int age`, a row prints `{"age": 30}`, NOT `{"age": "30"}`.
- **`--filter COL=VAL`**: keep only rows whose raw string value in `COL` equals
  `VAL`.
- **`--sort COL`**: sort output rows ascending by `COL`. If `COL` is an `--int`
  column, sort numerically; otherwise sort lexicographically by string value.
- Filtering is applied **before** sorting.
- A CSV with only a header row (no data rows) must print exactly `[]`.

Examples (given `/app/people.csv` with header `name,age,city`):
- `python /app/csv2json.py /app/people.csv --int age`
  → every object has an integer `age`.
- `python /app/csv2json.py /app/people.csv --filter city=Paris`
  → only rows where `city == "Paris"`.
- `python /app/csv2json.py /app/people.csv --int age --sort age`
  → rows ordered by ascending numeric age.

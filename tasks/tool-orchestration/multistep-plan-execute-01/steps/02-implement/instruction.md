You have a plan at `/app/plan.md`. Now implement it.

Create `/app/csv2json.py` so that:

```
python /app/csv2json.py <file.csv>
```

reads the CSV file, uses the first row as column headers (keys), and prints a JSON array of objects (one per data row) to stdout.

Requirements:
- Use only Python standard library modules (`csv`, `json`, `sys`).
- Output must be valid JSON parseable by `json.loads`.
- Each row becomes a dict mapping header names to string values.

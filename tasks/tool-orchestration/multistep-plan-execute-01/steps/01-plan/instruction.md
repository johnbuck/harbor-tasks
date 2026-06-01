Write an implementation plan for a CSV-to-JSON CLI tool with typed coercion,
filtering, and sorting.

The program will be `/app/csv2json.py`. Invocation:

```
python /app/csv2json.py <file.csv> [--int COL]... [--filter COL=VAL] [--sort COL]
```

Base behavior: read the CSV, treat the first row as column headers (keys), and
print a JSON array of objects (one per data row) to stdout. Beyond the base:

1. **`--int COL`** (may be given multiple times): values in column `COL` must be
   emitted as JSON **integers**, not strings (e.g. `"age": 30`, not `"age": "30"`).
2. **`--filter COL=VAL`**: keep only data rows where column `COL` equals the
   string `VAL`. Filtering compares against the raw CSV string value.
3. **`--sort COL`**: sort the output rows ascending by column `COL`. If `COL` was
   declared `--int`, sort **numerically**; otherwise sort lexicographically by
   the string value.
4. **Empty input:** a CSV with only a header row (no data rows) must print `[]`.
5. Filtering happens **before** sorting; both happen before serialization. `--int`
   coercion applies to the emitted JSON regardless of whether the column is used
   for filtering or sorting.

Write your numbered plan to `/app/plan.md`. Include at least 4 numbered steps,
and your plan must explicitly mention the `--int` integer coercion, `--filter`,
`--sort` (numeric vs lexicographic), and the empty-input `[]` case.

Do not implement the script yet — only write the plan.

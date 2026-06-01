There are **8** CSV files under `/app/data/` (`table_01.csv` through `table_08.csv`). For **each** one, produce a structural summary and write it to `/app/out/table_XX.json` in this exact format:

```json
{"rows": <int>, "columns": [{"name": "<str>", "dtype": "<str>", "nulls": <int>}, ...]}
```

- `rows` is the number of data rows (excluding the header).
- For each column: `name`, `dtype` (one of `"int"`, `"float"`, `"str"`, `"unknown"`), and `nulls` (count of empty cells). A column with mixed int/float values is `"float"`; a column that is entirely empty is `"unknown"`.

All 8 outputs must exist under `/app/out/`.

Skills are available to you in the environment (`/app/skills/`, each a directory with a `SKILL.md`).

Write only the 8 files under `/app/out/`. No other commentary.

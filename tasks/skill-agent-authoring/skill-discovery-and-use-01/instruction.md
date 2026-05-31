There are **8** CSV files under `/app/data/` (`table_01.csv` through `table_08.csv`). For **each** one, produce a structural summary and write it to `/app/out/table_XX.json` in this exact format:

```json
{"rows": <int>, "columns": [{"name": "<str>", "dtype": "<str>", "nulls": <int>}, ...]}
```

- `rows` is the number of data rows (excluding the header).
- For each column: `name`, `dtype` (one of `"int"`, `"float"`, `"str"`, `"unknown"`), and `nulls` (count of empty cells). A column with mixed int/float values is `"float"`; a column that is entirely empty is `"unknown"`.

All 8 outputs must exist under `/app/out/`.

**Important — there is already tooling for this.** `/app/skills/` contains **ten** skills in Claude Skill format (each a directory with a `SKILL.md`). Exactly **one** of them produces this exact structural summary; the other nine are decoys with similar names (`csv-stats`, `csv-profile`, `csv-dtypes`, `csv-nullreport`, `table-describe`, …) that emit a *different* shape or only part of the answer. Read the skills' `description` fields to discover the correct one, then invoke it via its documented entry-point for **every** file. Do not re-implement the summarizer from scratch and do not guess from the skill name alone — the descriptions are what disambiguate.

Write only the 8 files under `/app/out/`. No other commentary.

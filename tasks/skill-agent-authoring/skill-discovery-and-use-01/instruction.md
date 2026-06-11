I'm wiring up a data-ingestion step and need a compact, machine-readable description of each table in `/app/data/` so a downstream loader knows the column layout — and how each column is typed and how much of it is missing — before it ever reads the data.

There are **8** CSV files under `/app/data/` (`table_01.csv` through `table_08.csv`). For **each** one, produce that per-table description as JSON and write it to `/app/out/table_XX.json` (matching the source filename).

The skills installed under `/app/skills/` cover this kind of work — each skill is a directory with a `SKILL.md` that describes what it does and how to run it. Pick the appropriate one and use it as documented; don't reimplement it yourself.

Produce exactly the 8 output files under `/app/out/`. No other output.

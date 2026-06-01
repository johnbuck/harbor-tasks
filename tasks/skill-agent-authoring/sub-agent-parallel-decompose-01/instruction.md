You have **32** input CSV files under `/app/inputs/` (`data_01.csv` through `data_32.csv`). All have the same nominal shape:

```
id,name,score
1,alpha,72
2,bravo,18
...
```

**Task:** for each input file, produce an output file at `/app/data_XX.filtered.csv` (at `/app/`, NOT under `/app/inputs/`) containing, in order:

1. The header row (`id,name,score`).
2. Only the data rows where `score >= 50`, **sorted by `score` descending** (ties keep their original input order).
3. A final footer row in this exact form: `SUMMARY,<count>,<sum>` where `<count>` is the number of kept rows and `<sum>` is the sum of their `score` values.

Example output:

```
id,name,score
7,golf,91
3,charlie,72
SUMMARY,2,163
```

All 32 outputs must exist. The verifier scores each file across THREE independent stages (filter, sort, summary footer), so a file that is almost-but-not-quite right still earns partial credit.

**Edge cases — the naive single-pass gets these wrong:**

- **Boundary:** `score == 50` is **kept** (it satisfies `>= 50`); `score == 49` is dropped. Don't off-by-one the threshold.
- **Malformed rows:** some files contain rows whose `score` field is **not a valid integer** (empty, `N/A`, whitespace, `73x`, etc.). These rows are invalid: **drop them silently** — do not crash, do not count them, do not include them in the sum.
- **Ties:** some files contain several rows with the *same* score. The required order for a tie group is the **original input order** (a stable sort). A sort that reorders ties fails the sort stage for that file.
- **Empty results:** a couple of files have no rows at or above the threshold. Their output is just the header plus `SUMMARY,0,0`.

**Important:** The agent timeout is 10 minutes. Thirty-two files processed serially is tight — fan the work out so that multiple files are processed in parallel.

**Telemetry:** for each file you process, append two lines to `/var/log/work.log` in this exact format so we can observe parallelism:

```
<ISO-8601-timestamp> BEGIN data_NN
<ISO-8601-timestamp> END data_NN
```

Example: `2026-05-30T17:42:13Z BEGIN data_03`. Produce these timestamps however you like (shell `date -Iseconds`, Python `datetime.utcnow().isoformat()+"Z"`, etc.). The verifier reads this log to detect concurrent execution; genuinely parallel processing earns a throughput bonus on top of per-file correctness.

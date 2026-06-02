There are helper tools available on your `PATH` (see `/opt/tools/`).

Produce a file at `/app/answer.json` with exactly three integer/string fields:

```json
{"record_count": <int>, "latest_version": "<string>", "total_cents": <int>}
```

Where:

- `record_count` is the number of valid JSON records in `/app/events.jsonl` (a
  JSONL file — one JSON object per line; the file also contains non-record lines
  that are not valid JSON objects, which do not count).
- `latest_version` is the **semantically greatest** version string listed in
  `/app/releases.txt` (one version per line) — by semantic-version ordering, not
  plain-text ordering.
- `total_cents` is the sum of the `price` column across every row of
  `/app/cart.csv`, expressed in **integer cents** (the prices are written like
  `$12.50`).

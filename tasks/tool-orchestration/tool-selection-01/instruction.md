There are 18 helper tools available on your `PATH` (see `/opt/tools/`). Exactly
**three** of them are correct for this task; the other 15 are decoys — and for
each sub-goal one decoy is deliberately named to *look* right but returns a
**wrong** answer (e.g. a lexicographic "max" instead of a semantic-version max,
a naive numeric sum that cannot parse currency, a JSON-array counter pointed at
a JSONL file). Pick the *right* tool for each sub-goal, and avoid the decoys.

Produce a file at `/app/answer.json` with exactly three integer/string fields:

```json
{"record_count": <int>, "latest_version": "<string>", "total_cents": <int>}
```

Where:

- `record_count` is the number of JSON records in `/app/events.jsonl` (a JSONL
  file — one JSON object per line).
- `latest_version` is the **semantically greatest** version string listed in
  `/app/releases.txt` (one version per line). Note that `1.10.2` is greater than
  `1.9.0` even though it sorts earlier as plain text.
- `total_cents` is the sum of the `price` column across every row of
  `/app/cart.csv`, expressed in **integer cents** (the prices are written like
  `$12.50`).

Pick the right tool for each job. Calling a decoy lowers your tool-selection
precision; failing to call a correct tool lowers your recall. Your tool
selection is scored from the invocation log in addition to the correctness of
the three answers.

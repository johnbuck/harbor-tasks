There are 60 helper tools available in your `PATH` (see `/opt/tools/`). Exactly
**three** of them are relevant to this task; the other 57 are decoys — and
several decoys are deliberately named to *look* like the right tool (e.g.
`csv-validate`, `word-count`, `json-merge`). Use only the tools you actually
need, and use the *right* one each time.

Your task: produce a file at `/app/answer.json` with three fields:

```json
{"customer_count": <int>, "top_word": "<string>", "total_quantity": <int>}
```

Where:

- `customer_count` is the number of customer records in `/app/customers.csv`
  (data rows only — exclude the header).
- `top_word` is the single word that appears most often in `/app/notes.txt`
  (case-insensitive; ties broken by alphabetical order, lowercase).
- `total_quantity` is the sum of the `quantity` field across every object in
  `/app/orders.json`.

Pick the right tools for the job. Avoid tools that are obviously unrelated, and
do not call a similar-sounding decoy when the correct tool exists. Your tool
selection is scored: calling decoys lowers your precision, and missing a correct
tool lowers your recall.

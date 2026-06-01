There are helper tools available in your `PATH` (see `/opt/tools/`).

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

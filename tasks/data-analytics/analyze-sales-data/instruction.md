There are two CSVs:

- `/app/sales.csv` with columns `date,region,product,amount`
- `/app/products.csv` with columns `product,category,unit_cost`

The sales data is **messy**: it contains **exact duplicate rows** (the same
sale logged twice) and some rows have a **missing `amount`** (empty field ->
null). Unless a question says otherwise, treat the data with these rules:

- **Drop exact-duplicate rows** before aggregating amounts (a row that is
  identical across all four columns is a double-log and must be counted once).
- **Ignore rows with a missing `amount`** when summing or averaging amounts.
- A missing `region` is its own thing — never count a null region as a region.

Using **pandas**, answer the following and write them to `/app/answer.txt`, one
per line, in **exactly** this `KEY=value` format (this key order, no extra
lines):

```
Q1_WEST_TOTAL=<number, 2 decimals>
Q2_DISTINCT_REGIONS=<integer>
Q3_TOP_MEAN_REGION=<region name>
Q4_MISSING_AMOUNT_ROWS=<integer>
Q5_HARDWARE_GROSS_PROFIT=<number, 2 decimals>
Q6_TOP_PRODUCT_BY_AMOUNT=<product letter>
```

Questions:

- `Q1_WEST_TOTAL` — total `amount` for region `West` (after de-duplication,
  ignoring null amounts), rounded to 2 decimals.
- `Q2_DISTINCT_REGIONS` — number of distinct non-null regions in the data.
- `Q3_TOP_MEAN_REGION` — the region with the highest **mean** `amount` (after
  de-duplication, ignoring null amounts). On a tie, the alphabetically first
  region.
- `Q4_MISSING_AMOUNT_ROWS` — how many rows in `sales.csv` have a **missing
  `amount`** (count over the raw file, *before* de-duplication).
- `Q5_HARDWARE_GROSS_PROFIT` — join `sales` to `products` on `product`, restrict
  to rows whose product `category` is `Hardware`, and sum
  `(amount - unit_cost)` over those rows (after de-duplication, ignoring null
  amounts). Round to 2 decimals.
- `Q6_TOP_PRODUCT_BY_AMOUNT` — the product with the greatest total `amount`
  across all regions (after de-duplication, ignoring null amounts). On a tie,
  the alphabetically first product.

Constraints:

- Use pandas (it is already installed).
- Do not modify `/app/sales.csv` or `/app/products.csv`.
- Each `KEY=value` line is graded independently — a partly-correct set of
  answers scores a fraction.

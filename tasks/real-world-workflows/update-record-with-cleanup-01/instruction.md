My budget spreadsheet is `/app/budget.csv`. Please do two things in place:

1. **Remove duplicate grocery entries for this month (May 2026).** I have a
   stale import where some grocery rows got entered twice (and one got entered
   three times). A "duplicate" is: same `date` + same `vendor` + same `amount`
   + same `category`. Keep exactly **one** of each duplicate group; drop the
   rest. Be careful with the edge cases:
   - **Only May `groceries` rows.** Don't touch March or April rows even if
     they're identical duplicates. Don't touch any non-`groceries` May rows
     even if they're identical duplicates (e.g. a repeated utilities row stays).
   - A group of **three** identical rows collapses to **one** (drop two).
   - Rows that differ in **any** of the four fields are NOT duplicates — keep
     both. For example two grocery rows on the same day with amounts `55.00`
     and `55.10` are different purchases. Two rows with the same date, vendor,
     and amount but **different category** (e.g. `groceries` vs `household`)
     are NOT duplicates.

2. **Split this month's rent across the new roommate.** There's a
   `2026-05-15 rent` row for $1800 paid by `alex`. Replace it with two rows:
   one for $900.00 paid by `alex`, one for $900.00 paid by `roommate`. Both
   keep the same date, category, vendor, and notes — but append
   `" (split with roommate)"` to the notes for both new rows. Don't touch the
   March or April rent.

Constraints:
- Keep the existing column order: `date,category,vendor,amount,paid_by,notes`.
- Keep the row order: when you remove a duplicate, the remaining row keeps its
  original position. The two replacement rent rows go where the original rent
  row was.
- Amounts as `XXXX.YY` (2 decimal places, dollar signs not present).
- Do NOT remove or modify any rows other than the May grocery dupes and the
  May rent split.

Overwrite `/app/budget.csv` with the result. The verifier scores each
duplicate-group decision, each preserved edge-case row, and the rent split
independently — partial-credit applies, so getting more of them right scores
higher.

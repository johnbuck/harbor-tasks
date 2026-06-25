#!/bin/bash
# Reference solution — used by the `oracle` agent for sanity-checking the task.
set -e

python - <<'PY'
import pandas as pd

raw = pd.read_csv("/app/sales.csv")
products = pd.read_csv("/app/products.csv")

# Q4 is computed on the RAW file (before de-dup).
q4 = int(raw["amount"].isna().sum())

# Working frame: drop exact-duplicate rows, then drop null amounts for the
# amount aggregations.
dedup = raw.drop_duplicates()
amt = dedup.dropna(subset=["amount"])

# Q1: West total
q1 = amt.loc[amt["region"] == "West", "amount"].sum()

# Q2: distinct non-null regions (over the raw/dedup region set — same value)
q2 = int(raw["region"].dropna().nunique())

# Q3: region with highest mean amount, tie -> alphabetical first
means = amt.groupby("region")["amount"].mean()
q3 = sorted(means.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]

# Q5: join to products, Hardware only, sum(amount - unit_cost)
merged = amt.merge(products, on="product", how="left")
hw = merged[merged["category"] == "Hardware"]
q5 = (hw["amount"] - hw["unit_cost"]).sum()

# Q6: top product by total amount, tie -> alphabetical first
totals = amt.groupby("product")["amount"].sum()
q6 = sorted(totals.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]

with open("/app/answer.txt", "w") as f:
    f.write(f"Q1_WEST_TOTAL={q1:.2f}\n")
    f.write(f"Q2_DISTINCT_REGIONS={q2}\n")
    f.write(f"Q3_TOP_MEAN_REGION={q3}\n")
    f.write(f"Q4_MISSING_AMOUNT_ROWS={q4}\n")
    f.write(f"Q5_HARDWARE_GROSS_PROFIT={q5:.2f}\n")
    f.write(f"Q6_TOP_PRODUCT_BY_AMOUNT={q6}\n")
PY

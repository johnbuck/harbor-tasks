#!/bin/bash
# Reference solution — used by the `oracle` agent for sanity-checking the task.
set -e

python - <<'PY'
import pandas as pd
df = pd.read_csv("/app/sales.csv")
total = df.loc[df["region"] == "West", "amount"].sum()
with open("/app/answer.txt", "w") as f:
    f.write(f"{total:.2f}")
PY

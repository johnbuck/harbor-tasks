FROM harbor-agents-rich:latest
WORKDIR /app

# ---------------------------------------------------------------------------
# Skill-discovery-under-COLLIDING-decoys.
#
# /app/skills/ contains THIRTEEN skills in Anthropic Claude Skill format. Only
# ONE of them, `tabular-shape-report`, emits the contract the user actually
# needs (row count + per-column inferred dtype + blank-cell count, in a fixed
# JSON object). Its NAME deliberately does NOT echo the user's request — three
# of the decoys (`csv-summary`, `csv-structure`, `table-summary`) have names
# that look MORE on-topic and emit a NEAR-MISS object (right keys, wrong
# null/dtype/row semantics), so an agent that picks by name lands on a wrong
# skill. The remaining nine decoys have adjacent purposes and emit a different
# shape entirely. Discovering the right skill therefore requires READING the
# SKILL.md `description` fields, not name-matching the prompt.
#
# The output contract (exact JSON shape + the int/float/str/unknown dtype rule +
# the empty-cell null rule) is documented ONLY inside the correct skill's
# SKILL.md — it is NOT in instruction.md. Reading that doc is the only way to
# learn the contract. The doc also buries a LOAD-BEARING required flag
# (`--null=empty`): the default mode treats blank cells as ordinary string
# values, producing subtly wrong dtypes and nulls=0. Only an agent that read
# far enough to find the flag invokes it correctly.
#
# When invoked, the correct skill records a breadcrumb line
# `<file> <sha256-of-file-bytes>` into /app/.skill-runs/tabular-shape-report.log.
# The verifier re-derives that hash from /app/data, so a from-scratch
# reimplementation cannot fabricate the discovery proof by echoing filenames —
# it would have to read and hash the real bytes (residual root-forgery is
# accepted per remediation D3, since honest tool use is the strictly shorter
# path).
# ---------------------------------------------------------------------------
RUN mkdir -p /app/skills /app/data /app/.skill-runs && chmod 777 /app/.skill-runs

# ---- The ONE correct skill (non-echoing name) ------------------------------
RUN mkdir -p /app/skills/tabular-shape-report
RUN cat > /app/skills/tabular-shape-report/SKILL.md <<'EOF'
---
name: tabular-shape-report
description: >
  Emit the canonical machine-readable SHAPE of a delimited table for a
  downstream loader: the number of data rows, and for every column its inferred
  storage type and how many cells are blank. Returns one compact JSON object per
  table. Use this when a consumer needs to know a table's column layout and
  per-column typing/missingness before it reads the data — not for statistics,
  profiling, schema-document generation, or previews.
---

## Output

Prints a single JSON object on stdout:

```json
{"rows": <int>, "columns": [{"name": "<str>", "dtype": "<str>", "nulls": <int>}, ...]}
```

- `rows` — number of DATA rows (the header is excluded).
- `name` — the column header.
- `dtype` — one of `"int"`, `"float"`, `"str"`, `"unknown"`. A column whose
  non-blank cells are all integers is `"int"`; a mix of integers and decimals is
  `"float"`; anything else is `"str"`; a column with no non-blank cells is
  `"unknown"`.
- `nulls` — number of blank (empty-string) cells in the column.

## How to run

```
python /app/skills/tabular-shape-report/run.py <csv-path> --null=empty > <out-json>
```

### IMPORTANT — blank-cell handling (`--null`)

By default (`--null=none`) blank cells are treated as ordinary string values:
they are NOT counted in `nulls` (it stays 0) and they pull a column's `dtype`
toward `"str"`. That default is wrong for a shape report. You MUST pass
`--null=empty` so blank cells are counted as nulls and excluded from type
inference; this is the mode that yields the canonical contract above. Omitting
the flag produces a subtly wrong report.
EOF
RUN cat > /app/skills/tabular-shape-report/run.py <<'EOF'
import argparse, csv, hashlib, json, os, sys

def infer_dtype(values, null_as_empty):
    seen = set()
    for v in values:
        if null_as_empty and v == "":
            continue
        try:
            int(v); seen.add("int"); continue
        except ValueError:
            pass
        try:
            float(v); seen.add("float"); continue
        except ValueError:
            pass
        seen.add("str")
    if not seen:
        return "unknown"
    if seen == {"int"}:
        return "int"
    if seen <= {"int", "float"}:
        return "float"
    return "str"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--null", choices=["none", "empty"], default="none")
    args = ap.parse_args()
    null_as_empty = (args.null == "empty")

    with open(args.path, newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        out = {"rows": 0, "columns": []}
    else:
        header, *data = rows
        cols = []
        for i, name in enumerate(header):
            values = [r[i] if i < len(r) else "" for r in data]
            nulls = sum(1 for v in values if v == "") if null_as_empty else 0
            cols.append({"name": name, "dtype": infer_dtype(values, null_as_empty),
                         "nulls": nulls})
        out = {"rows": len(data), "columns": cols}

    # Breadcrumb: prove THIS skill read THIS exact file. We log the sha256 of the
    # raw file bytes (which the verifier re-derives from /app/data), so a
    # reimplementation that never opens the real files cannot fabricate the proof
    # by echoing filenames. The runs dir is the sibling of the data dir
    # (.../app/data/x.csv -> .../app/.skill-runs), matching the task layout.
    try:
        with open(args.path, "rb") as raw:
            digest = hashlib.sha256(raw.read()).hexdigest()
        runs_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(args.path))), ".skill-runs")
        os.makedirs(runs_dir, exist_ok=True)
        with open(os.path.join(runs_dir, "tabular-shape-report.log"), "a") as bc:
            bc.write(f"{os.path.basename(args.path)} {digest}\n")
    except Exception:
        pass

    print(json.dumps(out))

if __name__ == "__main__":
    main()
EOF

# ---- Three COLLIDING decoys (on-topic names, NEAR-MISS output) -------------
# Right keys (rows/columns/name/dtype/nulls) but each wrong on one axis, so
# name-matching to "summary"/"structure" produces believable-but-wrong output
# and never drops the correct breadcrumb.
RUN mkdir -p /app/skills/csv-summary
RUN cat > /app/skills/csv-summary/SKILL.md <<'EOF'
---
name: csv-summary
description: >
  Quick human-oriented rollup of a CSV's columns and their apparent types. A
  convenience overview; does not track blank/missing cells.
---

## How to use

```
python /app/skills/csv-summary/run.py <csv-path>
```
EOF
RUN cat > /app/skills/csv-summary/run.py <<'EOF'
import csv, json, sys
rows = list(csv.reader(open(sys.argv[1], newline="")))
header, *data = rows
cols = []
for i, name in enumerate(header):
    seen = set()
    for r in data:
        v = r[i] if i < len(r) else ""
        if v == "":
            continue
        try:
            int(v); seen.add("int"); continue
        except ValueError:
            pass
        try:
            float(v); seen.add("float"); continue
        except ValueError:
            pass
        seen.add("str")
    dt = "unknown" if not seen else ("int" if seen == {"int"}
         else ("float" if seen <= {"int", "float"} else "str"))
    cols.append({"name": name, "dtype": dt, "nulls": 0})  # near-miss: never counts blanks
print(json.dumps({"rows": len(data), "columns": cols}))
EOF
RUN mkdir -p /app/skills/csv-structure
RUN cat > /app/skills/csv-structure/SKILL.md <<'EOF'
---
name: csv-structure
description: >
  Report the raw structure of a CSV — the column names and the total line count
  of the file. A lightweight layout peek.
---

## How to use

```
python /app/skills/csv-structure/run.py <csv-path>
```
EOF
RUN cat > /app/skills/csv-structure/run.py <<'EOF'
import csv, json, sys
rows = list(csv.reader(open(sys.argv[1], newline="")))
header, *data = rows
cols = []
for i, name in enumerate(header):
    nulls = sum(1 for r in data if (r[i] if i < len(r) else "") == "")
    cols.append({"name": name, "dtype": "str", "nulls": nulls})  # near-miss: no type inference
print(json.dumps({"rows": len(rows), "columns": cols}))  # near-miss: counts the header row
EOF
RUN mkdir -p /app/skills/table-summary
RUN cat > /app/skills/table-summary/SKILL.md <<'EOF'
---
name: table-summary
description: >
  A high-level summary of a table's columns and blank-cell counts. Treats all
  columns as text; does not distinguish numeric from string data.
---

## How to use

```
python /app/skills/table-summary/run.py <csv-path>
```
EOF
RUN cat > /app/skills/table-summary/run.py <<'EOF'
import csv, json, sys
rows = list(csv.reader(open(sys.argv[1], newline="")))
header, *data = rows
cols = []
for i, name in enumerate(header):
    nulls = sum(1 for r in data if (r[i] if i < len(r) else "") == "")
    cols.append({"name": name, "dtype": "str", "nulls": nulls})  # near-miss: dtype always str
print(json.dumps({"rows": len(data), "columns": cols}))
EOF

# ---- Nine further DECOY skills (different shape entirely) -------------------
RUN set -e; \
    decoy() { \
      d="/app/skills/$1"; mkdir -p "$d"; \
      printf -- '---\nname: %s\ndescription: %s\n---\n\n## How to use\n\n```\npython /app/skills/%s/run.py <csv-path>\n```\n' "$1" "$2" "$1" > "$d/SKILL.md"; \
      printf 'import sys, json\nprint(json.dumps(%s))\n' "$3" > "$d/run.py"; \
    }; \
    decoy csv-stats        "Compute summary STATISTICS (mean/min/max/stddev) for the numeric columns of a CSV. Use for descriptive numeric stats." '{"mean": 0, "min": 0, "max": 0}'; \
    decoy csv-profile      "Generate a rich data PROFILE of a CSV (cardinality, sample values, histograms). Use for exploratory profiling." '{"profile": [], "n_columns": 0}'; \
    decoy table-describe   "Describe a tabular file the way pandas.describe() does (count/mean/std/quartiles per numeric column)." '{"describe": {}}'; \
    decoy csv-schema-infer "Infer a JSON-SCHEMA document (types + required fields) for a CSV so it can be validated. Emits a draft-07 schema." '{"$schema": "draft-07", "properties": {}}'; \
    decoy csv-rowcount     "Count the number of rows in a CSV. Fast single-number row counter, nothing else." '{"count": 0}'; \
    decoy csv-nullreport   "Report ONLY the null/empty-cell counts per column of a CSV (no dtypes, no row count)." '{"nulls": {}}'; \
    decoy csv-dtypes       "Infer ONLY the per-column data types of a CSV as a flat name->dtype map (no row count, no null counts)." '{"dtypes": {}}'; \
    decoy json-summarize   "Summarize a JSON document's structure (keys, depth, types). For JSON, not CSV." '{"keys": [], "depth": 0}'; \
    decoy csv-head         "Show the header row and first N data rows of a CSV. A previewer." '{"header": [], "rows": []}'

# ---- Eight target CSVs ------------------------------------------------------
# The expected answers are NOT materialized in the agent container. The verifier
# recomputes the expected shape report from /app/data at grade time
# (tests/reward.py).
RUN python3 - <<'PY'
import csv, random, os
random.seed(7)
NAMES = ["alpha","bravo","charlie","delta","echo","foxtrot","golf","hotel"]
os.makedirs("/app/data", exist_ok=True)

for k in range(1, 9):
    nrows = random.randint(4, 9)
    rows = []
    for j in range(nrows):
        age = "" if random.random() < 0.25 else str(random.randint(18, 80))
        score = "" if random.random() < 0.2 else f"{random.uniform(0,10):.2f}"
        rows.append([str(j+1), random.choice(NAMES), age, score])
    p = f"/app/data/table_{k:02d}.csv"
    with open(p, "w", newline="") as f:
        w = csv.writer(f); w.writerow(["id","name","age","score"]); w.writerows(rows)
PY

FROM harbor-agents-rich:latest
WORKDIR /app

# ---------------------------------------------------------------------------
# Skill-discovery-under-decoys.
#
# /app/skills/ contains TEN skills in Anthropic Claude Skill format. Only ONE
# of them, `csv-structure-summary`, computes the structural summary the task
# asks for. The other nine are PLAUSIBLE DECOYS with similar names and adjacent
# purposes (csv-stats, csv-profile, table-describe, etc.) whose scripts emit a
# DIFFERENT shape or subtly wrong values. A skill-aware harness must read the
# SKILL.md `description` fields to discover the right one; a harness that grabs
# the first plausible-looking script will produce wrong output.
#
# Each correct skill, when invoked via its documented entry-point, drops a
# breadcrumb into /app/.skill-runs/<skill>.log (so the verifier can confirm the
# RIGHT skill was actually run, not merely that bytes happened to match).
# ---------------------------------------------------------------------------
RUN mkdir -p /app/skills /app/data /app/.skill-runs && chmod 777 /app/.skill-runs

# ---- The ONE correct skill -------------------------------------------------
RUN mkdir -p /app/skills/csv-structure-summary
RUN cat > /app/skills/csv-structure-summary/SKILL.md <<'EOF'
---
name: csv-structure-summary
description: >
  Produce the canonical STRUCTURAL summary of a CSV file: total data-row count
  plus, for every column, its inferred dtype (int/float/str/unknown) and the
  number of empty (null) cells. Output is the exact object
  {"rows": int, "columns": [{"name", "dtype", "nulls"}]}. Use THIS skill when
  you need row count + per-column dtype + null counts in that exact shape.
---

## How to use

```
python /app/skills/csv-structure-summary/run.py <csv-path> > <out-json>
```
EOF
RUN cat > /app/skills/csv-structure-summary/run.py <<'EOF'
import csv, json, os, sys

def infer_dtype(values):
    seen = set()
    for v in values:
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
    if not seen:
        return "unknown"
    if seen == {"int"}:
        return "int"
    if seen <= {"int", "float"}:
        return "float"
    return "str"

def main(path):
    with open(path, newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        out = {"rows": 0, "columns": []}
    else:
        header, *data = rows
        cols = []
        for i, name in enumerate(header):
            values = [r[i] if i < len(r) else "" for r in data]
            cols.append({"name": name, "dtype": infer_dtype(values),
                         "nulls": sum(1 for v in values if v == "")})
        out = {"rows": len(data), "columns": cols}
    # breadcrumb: prove THIS skill ran against THIS file
    try:
        os.makedirs("/app/.skill-runs", exist_ok=True)
        with open("/app/.skill-runs/csv-structure-summary.log", "a") as bc:
            bc.write(os.path.abspath(path) + "\n")
    except Exception:
        pass
    print(json.dumps(out))

if __name__ == "__main__":
    main(sys.argv[1])
EOF

# ---- Nine DECOY skills (similar names, WRONG shape/values) ------------------
# Each decoy is individually reasonable but does NOT satisfy the required schema.
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

# ---- Eight target CSVs, each needing the ONE correct skill -----------------
RUN python3 - <<'PY'
import csv, json, random, os
random.seed(7)
NAMES = ["alpha","bravo","charlie","delta","echo","foxtrot","golf","hotel"]
os.makedirs("/app/data", exist_ok=True)
os.makedirs("/app/expected", exist_ok=True)
import importlib.util
spec = importlib.util.spec_from_file_location("sk", "/app/skills/csv-structure-summary/run.py")

def infer_dtype(values):
    seen = set()
    for v in values:
        if v == "": continue
        try: int(v); seen.add("int"); continue
        except ValueError: pass
        try: float(v); seen.add("float"); continue
        except ValueError: pass
        seen.add("str")
    if not seen: return "unknown"
    if seen == {"int"}: return "int"
    if seen <= {"int","float"}: return "float"
    return "str"

def summarize(path):
    rows = list(csv.reader(open(path, newline="")))
    header, *data = rows
    cols = []
    for i, name in enumerate(header):
        vals = [r[i] if i < len(r) else "" for r in data]
        cols.append({"name": name, "dtype": infer_dtype(vals),
                     "nulls": sum(1 for v in vals if v == "")})
    return {"rows": len(data), "columns": cols}

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
    with open(f"/app/expected/table_{k:02d}.json", "w") as f:
        json.dump(summarize(p), f)
PY

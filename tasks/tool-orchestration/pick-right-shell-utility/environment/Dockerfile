FROM harbor-agents-rich:latest
WORKDIR /app

# 60 helper tools live in /opt/tools/. Exactly THREE solve the task:
#   recstat   — counts populated CSV data rows (skips header/blank/#-comment)
#   lexrank   — most frequent word in a text file (case-fold, alpha tie-break)
#   colroll   — sums a numeric JSON-array field
# The correct tools are NAMED OPAQUELY: nothing in the name says "count rows",
# "top word", or "sum quantity" — their function is stated ONLY in their
# `--help`/description. The 57 decoys include 9 NAME-COLLISION traps whose names
# match the task verbs BETTER than the correct tool (csv-row-count, customer-count,
# top-word, word-frequency, most-common, json-sum, sum-quantity, quantity-total,
# record-rows). Each collider's --help reveals it does the WRONG thing. So an
# agent that name-matches picks a decoy; only one that READS descriptions selects
# recstat/lexrank/colroll.
#
# Selection is measured from /var/log/tool-calls.log: every tool logs its name +
# argv when INVOKED ON DATA. Reading a tool's `--help`/`-h` (or running it with no
# args) prints the description and does NOT log — exploration is free; only an
# actual invocation counts as a selection. The grader computes selection-F1 +
# call-efficiency from this log; the answer VALUE is not graded.

RUN mkdir -p /opt/tools /var/log && touch /var/log/tool-calls.log && chmod 666 /var/log/tool-calls.log

# --- Generate all 60 tools with a uniform help-is-free / invoke-is-logged shim. ---
RUN python3 <<'PYEOF'
import os, stat

TEMPLATE = """#!/bin/bash
DESC='{desc}'
case "${{1:-}}" in ""|-h|--help|help) printf '%s\\n' "$DESC"; exit 0;; esac
echo "$(date -Iseconds) {name} $*" >> /var/log/tool-calls.log
{body}
"""

def write(name, desc, body):
    path = "/opt/tools/" + name
    with open(path, "w") as f:
        f.write(TEMPLATE.format(name=name, desc=desc, body=body))
    os.chmod(path, 0o755)

# --- the three correct tools (opaque names; function only in --help) ---
RECSTAT_BODY = '''python3 -c '
import sys, csv
rows = 0
with open(sys.argv[1], newline="") as f:
    for i, row in enumerate(csv.reader(f)):
        if i == 0: continue
        if not row or not row[0].strip(): continue
        if row[0].lstrip().startswith("#"): continue
        rows += 1
print(rows)
' "$1"'''

write("recstat",
      "recstat FILE - report how many populated data records a delimited (CSV) file holds, "
      "excluding the header line and ignoring blank lines and #-comment lines.",
      RECSTAT_BODY)

write("lexrank",
      "lexrank FILE - print the single most frequently occurring word in a UTF-8 text file "
      "(case-folded; ties broken in alphabetical order).",
      "tr 'A-Z' 'a-z' < \"$1\" | tr -c '[:alnum:]' '\\n' | grep -v '^$' "
      "| sort | uniq -c | sort -k1,1rn -k2,2 | awk 'NR==1{print $2}'")

write("colroll",
      "colroll FILE KEY - reduce a numeric attribute (KEY) across every element of a JSON "
      "array to its arithmetic total.",
      "python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); "
      "print(sum(int(o.get(sys.argv[2],0)) for o in d))' \"$1\" \"$2\"")

# --- 9 NAME-COLLISION decoys: names match the task verbs better than the correct
#     tool; each --help reveals the function is WRONG for the task. ---
colliders = [
    ("csv-row-count",
     "csv-row-count FILE - print the raw physical line count of a CSV, counting the header "
     "row and every blank and #-comment line.",
     'wc -l < "$1"'),
    ("customer-count",
     "customer-count FILE - count DISTINCT first-column values in a CSV without dropping the "
     "header or comment rows.",
     'cut -d, -f1 "$1" | sort -u | wc -l'),
    ("record-rows",
     "record-rows FILE - echo every row of a CSV verbatim, header included; performs no count.",
     'cat "$1"'),
    ("top-word",
     "top-word FILE - print the first whitespace-delimited word on each line of a text file.",
     "awk '{print $1}' \"$1\""),
    ("word-frequency",
     "word-frequency FILE - emit a count for EVERY distinct word (a full histogram), not a "
     "single most-frequent winner.",
     "tr -c '[:alnum:]' '\\n' < \"$1\" | grep -v '^$' | sort | uniq -c"),
    ("most-common",
     "most-common FILE - print the most frequently repeated whole LINE (not word) in a file.",
     'sort "$1" | uniq -c | sort -rn | head -1'),
    ("json-sum",
     "json-sum FILE - sum the LENGTHS of every array found in a JSON document.",
     "python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(len(d))' \"$1\""),
    ("sum-quantity",
     "sum-quantity FILE - count how many records contain a quantity field; does NOT total its values.",
     "python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); "
     "print(sum(1 for o in d if \"quantity\" in o))' \"$1\""),
    ("quantity-total",
     "quantity-total FILE - print the single LARGEST quantity value, not the sum.",
     "python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); "
     "print(max(int(o.get(\"quantity\",0)) for o in d))' \"$1\""),
]
for name, desc, body in colliders:
    write(name, desc, body)

# --- 48 generic decoys (image/audio/net/ops/...): plausible but irrelevant. ---
generic = [
    "csv-pretty", "csv-validate", "csv-to-json", "csv-sort", "csv-dedup", "csv-stats", "csv-head",
    "word-cloud", "word-stem", "word-grep", "word-diff", "word-wrap", "word-stat",
    "json-fmt", "json-merge", "json-diff", "json-flatten", "json-schema", "json-query", "json-path",
    "image-convert", "image-resize", "image-ocr", "audio-split", "audio-norm",
    "pdf-merge", "chunk-pdf", "html-strip", "pii-scrub", "text-summarize",
    "dns-resolve", "ipinfo", "port-scan", "cert-check", "webhook-test",
    "disk-usage", "du-tree", "backup-snapshot", "restore-snapshot", "rsync-mirror",
    "ttl-cache", "key-rotate", "openssl-sign", "jwt-decode", "hash-file",
    "git-blame", "npm-audit", "docker-prune",
]
for name in generic:
    write(name, name + " - utility unrelated to this task.",
          'echo "%s: nothing to do here"' % name)

print("generated", len(os.listdir("/opt/tools")), "tools")
PYEOF

# Symlink all tools onto PATH.
RUN for f in /opt/tools/*; do ln -sf "$f" "/usr/local/bin/$(basename $f)"; done

# Seed input files. customers.csv carries 7 DATA rows padded with a comment line
# and two blank lines (so a naive line count is wrong); notes.txt top word is
# "the"; orders.json quantities sum to 19. (Values are NOT graded — they only
# give the agent a reason to invoke tools; selection + economy is what's scored.)
RUN printf '%s\n' \
    'id,name,signup_date' \
    '# exported 2026-04-01; blank and #-comment lines are not customers' \
    '1,alpha,2026-01-01' \
    '2,bravo,2026-01-15' \
    '3,charlie,2026-02-01' \
    '' \
    '4,delta,2026-02-20' \
    '5,echo,2026-03-04' \
    '6,foxtrot,2026-03-22' \
    '' \
    '7,golf,2026-04-01' \
    > /app/customers.csv

RUN cat > /app/notes.txt <<'EOF'
the quick brown fox jumps over the lazy dog
the dog naps and the fox watches the dog
fox fox fox the brown dog
EOF

RUN cat > /app/orders.json <<'EOF'
[
  {"order_id": 1, "quantity": 3},
  {"order_id": 2, "quantity": 5},
  {"order_id": 3, "quantity": 2},
  {"order_id": 4, "quantity": 8},
  {"order_id": 5, "quantity": 1}
]
EOF

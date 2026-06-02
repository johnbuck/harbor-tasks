FROM harbor-agents-rich:latest
WORKDIR /app

# 18 helper tools in /opt/tools/. Exactly THREE are correct for the task:
#   jsonl-count  — counts JSON objects in a JSONL file (one object per line)
#   semver-max   — returns the SEMANTICALLY-greatest version from a list
#   money-sum    — sums a currency-formatted ($d.cc) column, returning CENTS
# The other 15 are decoys. Several are deliberately NAME-ADJACENT and produce a
# plausible-but-WRONG answer for one of the sub-goals:
#   json-count     — json.load()s the whole file as ONE array (fails on JSONL)
#   text-sort-last — lexicographic last line ("1.9.0" > "1.10.2" as strings)
#   csv-col-sum    — naive float sum of a column (cannot parse a leading "$")
# A harness with weak tool-selection discipline reaches for the adjacent tool
# and gets the wrong number. Every tool logs its invocation to
# /var/log/tool-calls.log so the verifier can read the selection trajectory.

RUN mkdir -p /opt/tools /var/log && touch /var/log/tool-calls.log && chmod 666 /var/log/tool-calls.log

RUN cat > /usr/local/bin/_logwrap <<'EOF' && chmod +x /usr/local/bin/_logwrap
#!/bin/bash
NAME="$1"; shift
echo "$(date -Iseconds) $NAME $*" >> /var/log/tool-calls.log
"$@"
EOF

# --- Correct tool 1: jsonl-count (count VALID JSON objects, one per line) ---
# Skips blank lines, comments, and any line that is not a parseable JSON object,
# so a raw `wc -l` / `grep -c '{'` over the noisy file overcounts.
RUN cat > /opt/tools/jsonl-count <<'EOF' && chmod +x /opt/tools/jsonl-count
#!/bin/bash
_logwrap jsonl-count true
python3 -c "
import sys, json
n = 0
for l in open(sys.argv[1]):
    s = l.strip()
    if not s:
        continue
    try:
        obj = json.loads(s)
    except Exception:
        continue
    if isinstance(obj, dict):
        n += 1
print(n)
" "$1"
EOF

# --- Correct tool 2: semver-max (semantically-greatest version) ---
RUN cat > /opt/tools/semver-max <<'EOF' && chmod +x /opt/tools/semver-max
#!/bin/bash
_logwrap semver-max true
python3 -c "
import sys
def key(v): return tuple(int(x) for x in v.strip().split('.'))
vers=[l.strip() for l in open(sys.argv[1]) if l.strip()]
print(max(vers, key=key))
" "$1"
EOF

# --- Correct tool 3: money-sum (sum a \$d.cc column, return integer cents) ---
RUN cat > /opt/tools/money-sum <<'EOF' && chmod +x /opt/tools/money-sum
#!/bin/bash
_logwrap money-sum true
# money-sum FILE COLUMN  -> total in integer cents
python3 -c "
import sys,csv,re
col=sys.argv[2]; total=0
for row in csv.DictReader(open(sys.argv[1])):
    raw=re.sub(r'[^0-9.]','',row[col])
    total+=round(float(raw)*100)
print(total)
" "$1" "$2"
EOF

# --- Name-adjacent DECOYS that return a wrong-but-plausible answer ---

RUN cat > /opt/tools/json-count <<'EOF' && chmod +x /opt/tools/json-count
#!/bin/bash
_logwrap json-count true
# WRONG for JSONL: tries to load the whole file as a single JSON array.
python3 -c "import sys,json; print(len(json.load(open(sys.argv[1]))))" "$1"
EOF

RUN cat > /opt/tools/text-sort-last <<'EOF' && chmod +x /opt/tools/text-sort-last
#!/bin/bash
_logwrap text-sort-last true
# WRONG for versions: lexicographic max, not semantic ("1.9.0" > "1.10.2").
python3 -c "import sys; print(max(l.strip() for l in open(sys.argv[1]) if l.strip()))" "$1"
EOF

RUN cat > /opt/tools/csv-col-sum <<'EOF' && chmod +x /opt/tools/csv-col-sum
#!/bin/bash
_logwrap csv-col-sum true
# WRONG for currency: naive float() of a "\$d.cc" string raises -> prints 0.
python3 -c "
import sys,csv
col=sys.argv[2]; total=0.0
for row in csv.DictReader(open(sys.argv[1])):
    try: total+=float(row[col])
    except ValueError: pass
print(total)
" "$1" "$2"
EOF

# --- Generic unrelated decoys (do nothing useful) ---
RUN for name in \
        json-fmt jsonl-merge version-first version-list line-bytes line-count \
        csv-row-count csv-pretty currency-format date-parse uuid-gen hash-file \
        regex-extract ; do \
        printf '#!/bin/bash\n_logwrap %s true\necho "%s: nothing to do here"\n' "$name" "$name" > /opt/tools/$name; \
        chmod +x /opt/tools/$name; \
    done

# Symlink all tools onto PATH.
RUN for f in /opt/tools/*; do ln -sf "$f" "/usr/local/bin/$(basename $f)"; done

# --- Seed input files (expected answers are derived from these) ---

# events.jsonl: 6 VALID JSON objects interleaved with non-record noise (a blank
# line, two comment lines, and a brace-bearing line that is NOT valid JSON). A
# raw `wc -l` returns 10 and `grep -c '{'` returns 7 -> both WRONG. Only a tool
# that parses each line as JSON and keeps the objects returns record_count = 6.
RUN printf '%s\n' \
    '# events captured 2026-05-30 (lines beginning with # are not records)' \
    '{"id": 1, "kind": "click"}' \
    '{"id": 2, "kind": "view"}' \
    '' \
    '{"id": 3, "kind": "click"}' \
    '{malformed - not json}' \
    '{"id": 4, "kind": "scroll"}' \
    '{"id": 5, "kind": "view"}' \
    '# end of first batch' \
    '{"id": 6, "kind": "click"}' \
    > /app/events.jsonl

# releases.txt: semantic max = 1.10.10. Plain-text/lexicographic max is "1.9.0"
# (the text-sort-last decoy), and a careless reader picks "1.10.2" -> both WRONG.
RUN cat > /app/releases.txt <<'EOF'
1.2.0
1.9.0
1.10.0
1.10.2
1.10.10
0.9.9
EOF

# cart.csv: prices as $d.cc -> total = $21.00 = 2100 cents. The csv-col-sum decoy
# cannot parse the leading "$" and returns 0.
RUN cat > /app/cart.csv <<'EOF'
item,price
apple,$12.50
bread,$3.05
milk,$0.99
eggs,$4.46
EOF

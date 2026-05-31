FROM harbor-agents-rich:latest
WORKDIR /app

# Install 60 helper tools in /opt/tools/. Exactly THREE are correct for the task:
#   csv-row-count    — counts data rows in a CSV (correct)
#   word-tally       — tallies word frequency across a text file (correct)
#   json-key-sum     — sums an integer field across JSON objects (correct)
# The other 57 are plausible-sounding decoys (image converters, audio splitters,
# DNS resolvers, postgres pingers, etc.) — none of them help. Several decoys are
# deliberately NAME-ADJACENT to the correct tools (csv-pretty, csv-validate,
# word-count, word-cloud, json-fmt, json-merge ...) so that a harness with weak
# tool-selection discipline is tempted to call the wrong-but-similar one.
#
# Every tool logs its invocation to /var/log/tool-calls.log with a timestamp
# and argv, so the verifier can read the agent's tool-selection trajectory
# without parsing the trial trajectory.json.

RUN mkdir -p /opt/tools /var/log && touch /var/log/tool-calls.log && chmod 666 /var/log/tool-calls.log

RUN cat > /usr/local/bin/_logwrap <<'EOF' && chmod +x /usr/local/bin/_logwrap
#!/bin/bash
# Logs the tool name + argv to /var/log/tool-calls.log, then runs the body.
NAME="$1"; shift
echo "$(date -Iseconds) $NAME $*" >> /var/log/tool-calls.log
"$@"
EOF

# --- Correct tools (the three the task actually needs) ---

RUN cat > /opt/tools/csv-row-count <<'EOF' && chmod +x /opt/tools/csv-row-count
#!/bin/bash
_logwrap csv-row-count true
# Counts data rows (excludes header line).
n=$(($(wc -l < "$1") - 1))
echo "$n"
EOF

RUN cat > /opt/tools/word-tally <<'EOF' && chmod +x /opt/tools/word-tally
#!/bin/bash
_logwrap word-tally true
tr -c '[:alnum:]' '\n' < "$1" | grep -v '^$' | sort | uniq -c | sort -rn
EOF

RUN cat > /opt/tools/json-key-sum <<'EOF' && chmod +x /opt/tools/json-key-sum
#!/bin/bash
_logwrap json-key-sum true
# Sums an integer field across a JSON array of objects: json-key-sum FILE KEY
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(sum(int(o.get(sys.argv[2],0)) for o in d))" "$1" "$2"
EOF

# --- Decoys: 57 plausible-sounding tools that do nothing useful for this task. ---
# Each one logs that the agent picked it (precision-lowering signal).
# Note the name-adjacent traps: csv-*, word-*, json-* lures.
RUN for name in \
        csv-pretty csv-validate csv-to-json csv-sort csv-dedup \
        word-count word-cloud word-stem word-grep word-diff \
        json-fmt json-merge json-diff json-flatten json-schema \
        image-convert image-resize image-ocr audio-split audio-norm \
        pdf-merge chunk-pdf html-strip pii-scrub text-summarize \
        dns-resolve ipinfo port-scan cert-check webhook-test \
        disk-usage du-tree backup-snapshot restore-snapshot rsync-mirror \
        ttl-cache key-rotate openssl-sign jwt-decode hash-file \
        git-blame npm-audit pip-audit docker-prune k8s-restart \
        prom-query loki-query grafana-snap stripe-sync slack-msg \
        twilio-sms sentry-event pagerduty-ack s3-upload gcs-sync \
        csv-stats json-query ; do \
        printf '#!/bin/bash\n_logwrap %s true\necho "%s: nothing to do here"\n' "$name" "$name" > /opt/tools/$name; \
        chmod +x /opt/tools/$name; \
    done

# Symlink all tools onto PATH.
RUN for f in /opt/tools/*; do ln -sf "$f" "/usr/local/bin/$(basename $f)"; done

# Seed input files.
RUN cat > /app/customers.csv <<'EOF'
id,name,signup_date
1,alpha,2026-01-01
2,bravo,2026-01-15
3,charlie,2026-02-01
4,delta,2026-02-20
5,echo,2026-03-04
6,foxtrot,2026-03-22
7,golf,2026-04-01
EOF

RUN cat > /app/notes.txt <<'EOF'
the quick brown fox jumps over the lazy dog
the dog naps and the fox watches the dog
fox fox fox the brown dog
EOF

# Orders file for the json-key-sum sub-answer: total quantity across orders.
RUN cat > /app/orders.json <<'EOF'
[
  {"order_id": 1, "quantity": 3},
  {"order_id": 2, "quantity": 5},
  {"order_id": 3, "quantity": 2},
  {"order_id": 4, "quantity": 8},
  {"order_id": 5, "quantity": 1}
]
EOF

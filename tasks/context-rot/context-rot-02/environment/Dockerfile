FROM harbor-agents-rich:latest
WORKDIR /app
COPY gen_reports.py /tmp/gen_reports.py
RUN python3 /tmp/gen_reports.py && rm /tmp/gen_reports.py
# OPT-IN multi-step session threading: the thin adapters thread every step of the
# trial into ONE continuous conversation when this marker is present, so the 18
# weekly records actually ACCUMULATE in-context (~345K tokens, the in-window rot
# zone) instead of each ingest step starting fresh. Without it this task silently
# degraded to a memory-MCP test (no in-window accumulation at all). Memory /
# single-step tasks omit the marker. Spec: 2026-06-10-core-eleven-remediation.md D1.
RUN mkdir -p /opt/harness && touch /opt/harness/thread-session

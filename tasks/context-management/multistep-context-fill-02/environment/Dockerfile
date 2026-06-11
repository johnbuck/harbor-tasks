FROM harbor-agents-rich:latest
WORKDIR /app
COPY gen_reports.py /tmp/gen_reports.py
RUN python3 /tmp/gen_reports.py && rm /tmp/gen_reports.py
# OPT-IN multi-step session threading: the thin adapters (lib/openclaw_thin.py,
# lib/hermes_thin.py) check for this marker and, when present, thread every step
# of the trial into ONE continuous harness conversation so the 18 reports actually
# accumulate and overflow the window (the whole point of this context task). Memory
# / single-step tasks omit the marker and run fresh per step.
# Spec: backlog/2026-06-10-core-eleven-remediation.md D1.
RUN mkdir -p /opt/harness && touch /opt/harness/thread-session

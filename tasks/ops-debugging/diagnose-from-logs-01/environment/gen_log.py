#!/usr/bin/env python3
"""Generate a ~100k-line incident log for diagnose-from-logs-01.

REWORK (2026-06-01). The deprecated version was a 45-line log that NARRATED its
own root cause in inline `-- ...` comments (e.g. "-- no WHERE clause, full table
scan", "-- pool now fully checked out") and was graded by keyword match — so an
agent could copy the comments without reasoning, and 45 lines is trivially
one-shot. This version:
  * strips ALL narration comments — only raw events remain; the agent must
    INFER the causal chain (proximate 500 -> QueuePool timeout -> exhaustion ->
    the report job holding conn#1 -> undersized pool config);
  * buries the ~30 causal lines in ~100k lines of routine traffic, so the task
    is search-and-synthesize under volume, not read-the-whole-thing;
  * leaves the connection-hold DURATION uncomputed (no "checked out for 150s"
    line) — the agent must subtract timestamps (conn#1 acquired 08:05:00, first
    500 at 08:07:35 = ~155s). The grader requires that computed value, which a
    keyword dump cannot produce.

Deterministic (index-driven, no RNG). ~100k lines spanning ~08:00-09:40.
"""
import os
from datetime import datetime, timedelta

OUT = "/app/incident.log"
N_LINES = 100_000
START = datetime(2026, 5, 27, 8, 0, 0)
# spread lines over ~100 minutes
STEP_MS = 60  # ms between consecutive routine lines

ROUTINE = [
    "INFO  [request] GET /healthz 200 1ms",
    "INFO  [request] GET /api/orders?limit=20 200 {a}ms",
    "INFO  [request] GET /api/orders/{id} 200 {b}ms",
    "INFO  [request] POST /api/orders 201 {c}ms",
    "DEBUG [cache] redis GET key=order:{id} hit",
    "DEBUG [cache] redis GET key=user:{id2} miss",
    "INFO  [request] GET /api/customers/{id2} 200 {b}ms",
    "DEBUG [gc] young-gen pause {d}ms",
    "DEBUG [metrics] flushed {e} datapoints to statsd",
    "INFO  [request] GET /healthz 200 1ms",
    "DEBUG [auth] token introspection ok sub=user-{id2}",
    "INFO  [request] GET /api/orders?status=open 200 {a}ms",
]


def routine(i: int) -> str:
    tmpl = ROUTINE[i % len(ROUTINE)]
    return tmpl.format(
        a=30 + (i % 18), b=18 + (i % 40), c=95 + (i % 50),
        d=2 + (i % 8), e=40 + (i % 200),
        id=1000 + (i % 9000), id2=200 + (i % 1500),
    )


# Incident events at ABSOLUTE timestamps, no narration comments. (offset_seconds
# from START, text). conn#1 is acquired at 08:05:00 and the first 500 lands at
# 08:07:35 -> a ~155s hold the agent must COMPUTE.
INCIDENT = [
    (1,   "INFO  [server] Starting api-gateway v4.7.2 (pid=1, commit=9f3ac21)"),
    (1,   "INFO  [db] pool config: pool_size=5, max_overflow=0, pool_timeout=30, pool_recycle=-1"),
    (2,   "INFO  [server] Listening on 0.0.0.0:8080 (workers=4)"),
    (242, "WARN  [disk] Volume /var/log at 82% capacity (threshold 80%)"),
    (300, "INFO  [report] job 'nightly_revenue_report' triggered"),
    (300, "DEBUG [db] conn#1 acquired (in_use=1/5) owner=report"),
    (300, "DEBUG [report] executing: SELECT * FROM orders o JOIN line_items li ON li.order_id = o.id"),
    (340, "WARN  [disk] Volume /var/log at 83% capacity (threshold 80%)"),
    (363, "DEBUG [db] conn#2 acquired (in_use=2/5) owner=request"),
    (421, "DEBUG [db] conn#3 acquired (in_use=3/5) owner=request"),
    (422, "DEBUG [db] conn#4 acquired (in_use=4/5) owner=request"),
    (423, "DEBUG [db] conn#5 acquired (in_use=5/5) owner=request"),
    (423, "WARN  [db] QueuePool: 5/5 connections in use, 0 available, max_overflow=0"),
    (425, "INFO  [request] GET /api/orders?limit=20 (awaiting pool connection)"),
    (455, "ERROR [handler] Request handler failed while awaiting a pooled connection"),
    (455, "Traceback (most recent call last):"),
    (455, '  File "/app/api/routes.py", line 211, in get_orders'),
    (455, "    with db.session() as s:"),
    (455, '  File "/app/api/db.py", line 64, in session'),
    (455, "    conn = engine.connect()"),
    (455, '  File "/usr/local/lib/python3.11/site-packages/sqlalchemy/pool/base.py", line 1203, in _do_get'),
    (455, "    raise exc.TimeoutError("),
    (455, "sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 0 reached, connection timed out, timeout 30.00 (Background on this error at: https://sqlalche.me/e/20/3o7r)"),
    (455, "ERROR [server] GET /api/orders?limit=20 -> 500 Internal Server Error (remote=10.0.4.55)"),
    (456, "ERROR [server] GET /api/orders/4490 -> 500 Internal Server Error (remote=10.0.4.61)"),
    (456, "ERROR [server] POST /api/orders -> 500 Internal Server Error (remote=10.0.4.61)"),
    (520, "INFO  [report] job 'nightly_revenue_report' finished (elapsed=220s)"),
    (521, "DEBUG [db] conn#1 released (in_use=4/5) owner=report"),
    (524, "INFO  [server] GET /api/orders?limit=20 200 44ms (recovered)"),
]


def ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def main():
    os.makedirs("/app", exist_ok=True)
    # Bucket incident events by their absolute second so we can interleave them
    # into the routine stream in timestamp order.
    incident_by_line = {}
    # place each incident event at the routine-line index whose timestamp first
    # reaches its offset; compute that index from STEP_MS.
    for off, text in INCIDENT:
        idx = int((off * 1000) / STEP_MS)
        incident_by_line.setdefault(idx, []).append(text)

    with open(OUT, "w") as f:
        for i in range(N_LINES):
            t = START + timedelta(milliseconds=i * STEP_MS)
            if i in incident_by_line:
                for text in incident_by_line[i]:
                    # traceback continuation lines carry no leading timestamp
                    if text.startswith("  ") or text.startswith("    ") or text.startswith("Traceback") or text.startswith("sqlalchemy."):
                        f.write(text + "\n")
                    else:
                        f.write(f"{ts(t)} {text}\n")
            f.write(f"{ts(t)} {routine(i)}\n")

    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

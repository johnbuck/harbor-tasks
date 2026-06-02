#!/bin/bash
# Reference solution — used by the `oracle` agent to sanity-check the task.
# Reflects the reworked ~100k-line, narration-free log: the causal chain must be
# reconstructed from raw events, and the connection-hold duration COMPUTED from
# timestamps (it is printed nowhere).
set -e

cat > /app/diagnosis.md <<'EOF'
## Root Cause(s)

**Proximate error.** At 08:07:34 the request handlers began returning HTTP 500.
The traceback shows the failure originated in `engine.connect()` and raised:

```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 0 reached,
connection timed out, timeout 30.00
```

Each failing request waited up to `pool_timeout=30` seconds for a database
connection, never got one, and timed out — that QueuePool/TimeoutError surfaced
as the 500s.

**Underlying mechanism: connection-pool exhaustion.** Just before the errors the
pool filled connection by connection until fully checked out:

```
08:07:03 WARN [db] QueuePool: 5/5 connections in use, 0 available, max_overflow=0
```

With all 5 connections in use and 0 available, every new request blocked.

**Contributing cause #1: a long-running unbounded report query pinned a
connection.** At 08:05:00 the scheduled `nightly_revenue_report` job acquired
`conn#1` (`owner=report`) and ran an unbounded query with no `WHERE` clause —
a full-table scan:

```
SELECT * FROM orders o JOIN line_items li ON li.order_id = o.id
```

That connection was never released before the outage. Computing from the
timestamps — `conn#1` acquired at 08:05:00 and the first 500 at 08:07:34 — it was
held for roughly **155 seconds** (~2.5 min). While that one connection was
pinned, normal request traffic consumed the remaining four and the pool ran dry.

**Contributing cause #2: the pool is mis-sized for the workload.** It was
configured `pool_size=5, max_overflow=0` — a hard ceiling of 5 connections with
no overflow headroom. With 4 request workers plus a background report job
sharing only 5 connections, a single slow consumer starves everything else.

## Evidence

- `QueuePool limit of size 5 overflow 0 reached, connection timed out,
  timeout 30.00` — the proximate error at 08:07:34.
- `pool config: pool_size=5, max_overflow=0, pool_timeout=30` (08:00:01) and the
  `5/5 in use, 0 available` exhaustion warning (08:07:03).
- `nightly_revenue_report` acquiring `conn#1` at 08:05:00, the no-WHERE
  `SELECT * FROM orders ... JOIN line_items` full scan, and the ~155-second hold
  between that acquisition and the first 500.

## Red Herring

The `WARN [disk] Volume /var/log at 82% / 83% capacity` lines are **unrelated
noise**. Log-volume usage only crept up a couple of points — it never filled,
never produced an error, and does not line up with the 500s. The crash was a
database connection-pool timeout, not a disk-space problem; the disk warnings
are a distractor.

## Recommended Fix

1. **Get the report job off the request pool.** Run `nightly_revenue_report`
   against a dedicated engine / read-replica (or a separate pool) so it can't
   starve request-serving connections. Bound the query — add a `WHERE`/date
   filter and pagination instead of a full-table `SELECT *` — and set a
   `statement_timeout` so a runaway query can't pin a connection for ~155s.

2. **Give the pool headroom.** Increase `pool_size` and allow `max_overflow`
   (e.g. `pool_size=10, max_overflow=10`) so a transient slow consumer doesn't
   immediately exhaust the pool; consider a shorter checkout timeout to fail fast.
EOF

#!/bin/bash
# Reference solution — used by the `oracle` agent to sanity-check the task.
set -e

cat > /app/diagnosis.md <<'EOF'
## Root Cause(s)

**Proximate error.** Starting at 08:07:35 the request handlers began returning
HTTP 500. The traceback shows the failure originated in `engine.connect()` and
raised:

```
sqlalchemy.exc.TimeoutError: QueuePool limit of size 5 overflow 0 reached,
connection timed out, timeout 30.00
```

So each failing request waited up to `pool_timeout=30` seconds for a database
connection, never got one, and timed out — that QueuePool/TimeoutError is what
surfaced as the 500s.

**Underlying mechanism: connection-pool exhaustion.** Just before the errors,
the log shows the pool filling connection by connection until it was fully
checked out:

```
08:07:03 DEBUG [db] Acquired connection conn#5 from pool (in_use=5/5)
08:07:03 WARN  [db] Connection pool exhausted: 5/5 in use, 0 available, max_overflow=0
```

With all 5 connections in use and 0 available, every new request blocked waiting
for a free connection.

**Contributing cause #1: a long-running unbounded report query held a
connection.** At 08:05:00 the scheduled `nightly_revenue_report` job acquired
`conn#1` and ran an unbounded full-table-scan query with no `WHERE` clause:

```
SELECT * FROM orders o JOIN line_items li ON li.order_id = o.id  -- no WHERE clause, full table scan
```

The log warns that `conn#1` stayed checked out for 90s, then 150s, and the job
finally finished after 175s. While that one connection was pinned, normal
request traffic consumed the remaining four and the pool ran dry.

**Contributing cause #2: the pool is mis-sized for the workload.** The pool was
configured `pool_size=5, max_overflow=0`, i.e. a hard ceiling of 5 connections
with **no overflow headroom**. With 4 request workers plus a background report
job all sharing only 5 connections, a single slow consumer starves everything
else. A pool with no spare capacity makes exhaustion almost inevitable under any
slow query.

## Evidence

- `QueuePool limit of size 5 overflow 0 reached, connection timed out,
  timeout 30.00` (08:07:35) — the proximate error.
- `Pool config: pool_size=5, max_overflow=0, pool_timeout=30` (08:00:01) and the
  `5/5 in use, 0 available` exhaustion warning (08:07:03).
- `nightly_revenue_report` acquiring `conn#1` (08:05:00), the no-WHERE
  `SELECT * FROM orders ... JOIN line_items` full scan, and the 150s/175s
  checkout warnings.

## Red Herring

The `WARN [disk] Volume /var/log at 82% / 83% / 84% capacity` lines are
**unrelated noise**. Log-volume usage only crept from 82% to 84% — it never
filled, never produced an error, and the timeline of the disk warnings does not
line up with the 500s. The crash was a database connection-pool timeout, not a
disk-space problem; the disk warnings are a distractor.

## Recommended Fix

Address the real cause on two fronts:

1. **Get the report job off the request pool.** Run `nightly_revenue_report`
   against a dedicated engine / read-replica (or a separate connection pool) so
   it can never starve request-serving connections. Also bound the query — add a
   `WHERE`/date filter and pagination instead of a full-table `SELECT *` scan —
   and set a `statement_timeout` so a runaway query can't pin a connection for
   175s.

2. **Give the pool headroom.** Increase `pool_size` and allow `max_overflow`
   (e.g. `pool_size=10, max_overflow=10`) so transient slow consumers don't
   immediately exhaust the pool, and consider a shorter connection checkout
   timeout to fail fast and shed load gracefully.
EOF

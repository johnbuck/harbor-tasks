#!/bin/bash
# Reference solution — used by the `oracle` agent to sanity-check the task.
set -e

cat > /app/runbook.md <<'EOF'
# appdb Restore Runbook

Use this runbook to restore `appdb` from the most recent nightly backup after a
data-loss incident.

---

## Phase 1 — Locate and Choose the Backup

List the available backups in S3 and identify the most recent one:

```bash
aws s3 ls s3://acme-backups/appdb/ --human-readable | sort
```

Pick the file with the latest date, e.g. `appdb-2024-05-27.sql.gz`. Note the
full filename — you will use it in Phase 2.

> **Note:** Retention is 7 days. If the most recent backup is older than 7 days,
> check with your S3 administrator — the lifecycle policy may have expired it.

---

## Phase 2 — Retrieve the Backup

SSH to the restore host (`restore.acme.internal`) and download the chosen backup:

```bash
ssh restore.acme.internal
aws s3 cp s3://acme-backups/appdb/appdb-2024-05-27.sql.gz /tmp/appdb-restore.sql.gz
```

Verify the file downloaded correctly:

```bash
ls -lh /tmp/appdb-restore.sql.gz
```

---

## Phase 3 — Restore the Database

### 3a. Ensure prerequisites exist on the restore host

Create the `appuser` role if it does not already exist:

```bash
psql -h restore.acme.internal -U postgres -c "CREATE ROLE appuser LOGIN;"
```

Drop and recreate the target database (this is destructive — confirm you are
on the restore host, **not** production):

```bash
psql -h restore.acme.internal -U postgres -c "DROP DATABASE IF EXISTS appdb;"
psql -h restore.acme.internal -U postgres -c "CREATE DATABASE appdb OWNER appuser;"
```

### 3b. Decompress and restore

The backup was created with `pg_dump` in plain SQL format, so restore with `psql`:

```bash
gunzip -c /tmp/appdb-restore.sql.gz | psql -h restore.acme.internal -U appuser appdb
```

Credentials are read automatically from `/root/.pgpass`.

---

## Phase 4 — Verify the Restore

### 4a. List tables

Confirm the schema was restored:

```bash
psql -h restore.acme.internal -U appuser appdb -c "\dt"
```

You should see the expected table list. If the output is empty, the restore
failed or the backup was from an empty database.

### 4b. Row count spot-check

Pick a key table (e.g. `users`) and verify it has a plausible row count:

```bash
psql -h restore.acme.internal -U appuser appdb -c "SELECT COUNT(*) FROM users;"
```

Compare the count against known production figures. A count of 0 on a table
that should have data indicates a failed or partial restore.

### 4c. Declare complete

Once tables and row counts look correct, update your incident ticket and notify
the team that the restore is complete and the restore host is ready for
application traffic cut-over.

---

## Cleanup

Remove the temporary backup file when done:

```bash
rm /tmp/appdb-restore.sql.gz
```
EOF

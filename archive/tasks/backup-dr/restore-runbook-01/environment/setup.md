# Backup Setup: appdb

## Database

- **Name:** `appdb`
- **Production host:** `db.acme.internal` (PostgreSQL 15)
- **Credentials:** stored in `/root/.pgpass` on the production host (format: `hostname:port:database:user:password`)

## Backup Schedule

- Nightly at **02:00 UTC** via `pg_dump`
- Output is **gzip-compressed** SQL: `appdb-YYYY-MM-DD.sql.gz`
- Stored in S3 bucket: `s3://acme-backups/appdb/`
- **Retention:** 7 days (older files are automatically deleted by an S3 lifecycle rule)

## Backup Command (for reference)

```bash
pg_dump -h db.acme.internal -U appuser appdb | gzip > appdb-$(date +%F).sql.gz
aws s3 cp appdb-$(date +%F).sql.gz s3://acme-backups/appdb/
```

## Notes

- The AWS CLI is pre-configured with credentials on the restore host.
- The target PostgreSQL server for restores is `restore.acme.internal`.
- The `appdb` database must be created (or recreated) before restoring.
- The `appuser` role must exist on the restore host before the restore runs.

Read `/app/setup.md`. It describes a PostgreSQL backup setup for the database `appdb`.

Write a clear, step-by-step restore runbook to `/app/runbook.md` that an on-call engineer can follow after a data-loss incident to recover `appdb` from the most recent backup.

The runbook must cover all four of these phases, in order:

1. **Locate and choose the backup** — how to find the most recent available backup in the S3 bucket.
2. **Retrieve the backup** — how to download it to the restore host.
3. **Restore the database** — how to decompress and load the backup into a fresh `appdb` on the restore host (including any prerequisites like creating the database or role).
4. **Verify the restore** — at least one concrete check to confirm the restore succeeded before declaring it complete.

Use concrete commands drawn from the setup described in `/app/setup.md`. Do not invent infrastructure that isn't mentioned there. Write only `/app/runbook.md` — no other files or commentary.

Scan the files under `/app/repo/` for hardcoded secrets. A secret is real
credential material accidentally committed to source — e.g. an API key, an AWS
access key / secret access key, a JWT/session token, a private key, or a
database connection string that embeds a real password.

Be precise: **placeholder / example / template values are NOT secrets**. A file
that contains only placeholder or example values must NOT be listed — flagging it
counts against you.

Write to `/app/findings.txt` the path — relative to `/app/repo/` — of each file
that contains at least one **real** hardcoded secret, one per line, sorted
alphabetically. A file with no real secret must NOT be listed.

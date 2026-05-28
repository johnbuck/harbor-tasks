Scan the files under `/app/repo/` for hardcoded secrets (API keys, secret
access keys, private keys).

Write to `/app/findings.txt` the path — relative to `/app/repo/` — of each
file that contains a hardcoded secret, one per line, sorted alphabetically.
A file with no secret must NOT be listed.

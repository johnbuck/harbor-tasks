#!/bin/bash
# Reference solution — used by the `oracle` agent to sanity-check the task.
set -e

cat > /app/review.md <<'EOF'
# Code Review: add user lookup endpoint

## Critical: SQL Injection (security)

**File:** `app/handlers/users.py`, `lookup_user()`

The query is built by interpolating user input directly into an f-string:

```python
cursor.execute(
    f"SELECT id, username, email, created_at FROM users WHERE username = '{username}'"
)
```

A caller can pass `username` values like `' OR '1'='1` or `'; DROP TABLE users; --`
to manipulate the query. This is a textbook SQL injection vulnerability that gives
an unauthenticated caller full read (and potentially write/delete) access to the
database.

**Fix:** use a parameterized query so the driver handles quoting and escaping:

```python
cursor.execute(
    "SELECT id, username, email, created_at FROM users WHERE username = ?",
    (username,),
)
```

This is the only change required for correctness and security. The rest of the
endpoint structure (Blueprint registration, 400/404 handling, JSON response shape)
looks reasonable.
EOF

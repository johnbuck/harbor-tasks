#!/bin/bash
# Reference solution — scores 1.0 under the deterministic graded verifier.
set -e

cat > /app/review.md <<'EOF'
# Code Review: add user lookup / delete / count endpoints

## Critical: SQL Injection in `lookup_user` (security)

**File:** `app/handlers/users.py`, `lookup_user()`

The query is built by interpolating user input directly into an f-string:

```python
cursor.execute(
    f"SELECT id, username, email, password_hash, created_at FROM users WHERE username = '{username}'"
)
```

A caller can pass a `username` like `' OR '1'='1` or `'; DROP TABLE users; --`
to manipulate the query. This is a textbook SQL injection vulnerability.

**Fix:** use a parameterized query so the driver handles quoting/escaping:

```python
cursor.execute(
    "SELECT id, username, email, created_at FROM users WHERE username = ?",
    (username,),
)
```

## Critical: Sensitive data exposure — `password_hash` returned to the client

**File:** `app/handlers/users.py`, `lookup_user()`

The endpoint selects `password_hash` and includes it in the JSON response body.
A password hash must never be returned to clients — it leaks credential material
and aids offline cracking.

**Fix:** drop `password_hash` from both the `SELECT` column list and the
returned JSON. Never serialize password hashes in API responses.

## Critical: `delete_user` has no authentication / authorization

**File:** `app/handlers/users.py`, `delete_user()`

The `DELETE /api/users/<int:user_id>` endpoint performs no auth check, so any
unauthenticated caller can delete any user by id — broken access control. The
parameterized DELETE itself is fine; the missing authorization is the problem.

**Fix:** require authentication and authorize the caller (admin, or the owner of
`user_id`) before deleting, e.g. with an `@require_auth` decorator and an
ownership/role check.

## Not an issue

`EXAMPLE_API_KEY = "your-api-key-here"` is an obvious documentation placeholder,
not a real leaked secret — no action needed. The `count_users` endpoint and the
parameterized `DELETE` statement are fine.
EOF

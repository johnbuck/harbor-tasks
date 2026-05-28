#!/bin/bash
# Reference solution — used by the `oracle` agent to sanity-check the task.
set -e

cat > /app/diagnosis.md <<'EOF'
## Root Cause

The crash is a `KeyError: 'user_id'` raised in `handle_request` at line 112 of
`/app/server.py`:

```python
user = db.get_user(payload['user_id'])
```

The inbound POST to `/api/action` carried the body `{"action":"transfer","amount":250}`,
which contains no `user_id` key. Because `handle_request` indexes `payload['user_id']`
directly — without checking that the key is present — Python raises a `KeyError` and
the request fails with HTTP 500.

## Recommended Fix

Validate the required field before use and return an explicit error response when it
is absent:

```python
def handle_request(payload):
    user_id = payload.get('user_id')
    if user_id is None:
        raise BadRequestError("Missing required field: user_id")
    user = db.get_user(user_id)
    ...
```

Alternatively, apply input validation at the dispatch layer using a schema library
(e.g. `pydantic`, `marshmallow`, or `jsonschema`) so that all required fields are
checked before any handler is called. This prevents the same class of bug across
all endpoints, not just `/api/action`.
EOF

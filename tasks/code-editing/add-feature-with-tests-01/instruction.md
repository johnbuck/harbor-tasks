Implement the `LRUCache` class in `/app/lru.py`. The stub raises
`NotImplementedError`; a test suite at `/app/tests/test_lru.py` defines the
required behavior.

Requirements:

- `LRUCache(capacity: int)` — fixed capacity (capacity >= 1).
- `get(key) -> value | -1` — return the value, or `-1` if absent. A `get`
  counts as a use (refreshes recency).
- `put(key, value)` — insert/update. A `put` counts as a use. When inserting
  a new key would exceed capacity, evict the least-recently-used entry first.
- Updating an existing key with `put` refreshes its recency and does NOT evict.

Constraints:

- Do not modify the test file.
- Keep the public interface exactly as the tests expect.

Run the tests with:

```
cd /app && python -m pytest tests/test_lru.py -v
```

When all tests pass, you are done.
